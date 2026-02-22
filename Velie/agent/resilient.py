"""Velie QA Agent — Resilient HTTP Client.

Provides exponential backoff + retry + circuit breaker for API calls.
"""

from __future__ import annotations

import asyncio
import logging
import time
from functools import wraps

import httpx

logger = logging.getLogger(__name__)

# Circuit breaker state
_circuit_state: dict[str, dict] = {}
_CIRCUIT_THRESHOLD = 5  # failures before opening
_CIRCUIT_TIMEOUT = 60  # seconds to wait before half-open


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""


def _get_circuit(name: str) -> dict:
    """Get circuit breaker state for a named service."""
    if name not in _circuit_state:
        _circuit_state[name] = {
            "failures": 0,
            "state": "closed",  # closed, open, half-open
            "last_failure": 0.0,
        }
    return _circuit_state[name]


def _check_circuit(name: str) -> None:
    """Check if circuit is open. Raises CircuitOpenError if so."""
    circuit = _get_circuit(name)
    if circuit["state"] == "open":
        if time.time() - circuit["last_failure"] > _CIRCUIT_TIMEOUT:
            circuit["state"] = "half-open"
            logger.info("Circuit %s: half-open (attempting retry)", name)
        else:
            raise CircuitOpenError(f"Circuit {name} is open. Wait {_CIRCUIT_TIMEOUT}s.")


def _record_success(name: str) -> None:
    """Record a successful call, closing the circuit."""
    circuit = _get_circuit(name)
    circuit["failures"] = 0
    circuit["state"] = "closed"


def _record_failure(name: str) -> None:
    """Record a failure, potentially opening the circuit."""
    circuit = _get_circuit(name)
    circuit["failures"] += 1
    circuit["last_failure"] = time.time()
    if circuit["failures"] >= _CIRCUIT_THRESHOLD:
        circuit["state"] = "open"
        logger.warning("Circuit %s: OPEN after %d failures", name, circuit["failures"])


async def resilient_request(
    method: str,
    url: str,
    *,
    circuit_name: str = "default",
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 30.0,
    headers: dict | None = None,
    json_data: dict | None = None,
    content: str | bytes | None = None,
) -> httpx.Response:
    """Make an HTTP request with exponential backoff + circuit breaker.

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE).
        url: Request URL.
        circuit_name: Name for circuit breaker tracking.
        max_retries: Maximum number of retries.
        base_delay: Base delay in seconds (doubles each retry).
        timeout: Request timeout in seconds.
        headers: Optional headers dict.
        json_data: Optional JSON body.
        content: Optional raw body content.

    Returns:
        httpx.Response on success.

    Raises:
        CircuitOpenError: If the circuit breaker is open.
        httpx.HTTPStatusError: If all retries exhausted.
    """
    _check_circuit(circuit_name)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                kwargs: dict = {"headers": headers or {}}
                if json_data is not None:
                    kwargs["json"] = json_data
                if content is not None:
                    kwargs["content"] = content

                response = await client.request(method, url, **kwargs)

                # Rate limit handling
                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", base_delay * (2 ** attempt)))
                    logger.warning(
                        "Rate limited on %s (attempt %d/%d). Retrying in %ds",
                        circuit_name, attempt + 1, max_retries + 1, retry_after,
                    )
                    await asyncio.sleep(retry_after)
                    continue

                # Server errors — retry
                if response.status_code >= 500:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        "Server error %d on %s (attempt %d/%d). Retrying in %.1fs",
                        response.status_code, circuit_name, attempt + 1, max_retries + 1, delay,
                    )
                    _record_failure(circuit_name)
                    await asyncio.sleep(delay)
                    continue

                # Success or client error (4xx) — don't retry
                _record_success(circuit_name)
                return response

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            last_error = e
            delay = base_delay * (2 ** attempt)
            _record_failure(circuit_name)
            logger.warning(
                "Connection error on %s (attempt %d/%d): %s. Retrying in %.1fs",
                circuit_name, attempt + 1, max_retries + 1, str(e)[:80], delay,
            )
            if attempt < max_retries:
                await asyncio.sleep(delay)

    # All retries exhausted
    raise last_error or httpx.ConnectError(f"All {max_retries + 1} attempts failed for {circuit_name}")


def get_circuit_status() -> dict:
    """Get status of all circuit breakers."""
    return {
        name: {
            "state": circuit["state"],
            "failures": circuit["failures"],
            "last_failure": circuit["last_failure"],
        }
        for name, circuit in _circuit_state.items()
    }


def reset_circuit(name: str) -> None:
    """Reset a specific circuit breaker."""
    if name in _circuit_state:
        _circuit_state[name] = {
            "failures": 0,
            "state": "closed",
            "last_failure": 0.0,
        }
