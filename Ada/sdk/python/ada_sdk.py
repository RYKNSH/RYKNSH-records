"""Ada SDK — Python Client.

Simple, intuitive Python client for the Ada Core API.

Usage:
    from ada_sdk import Ada

    client = Ada(api_key="ada_live_xxx", base_url="https://ada-core-api-production.up.railway.app")
    response = client.chat("Review this code", node_set="code_reviewer")
    print(response.content)
"""

from __future__ import annotations

import json
from typing import Any, Iterator

import httpx


class AdaResponse:
    """Response from Ada API."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        choices = data.get("choices", [])
        self.content = choices[0]["message"]["content"] if choices else ""
        self.model = data.get("model", "")
        self.usage = data.get("usage", {})
        self.id = data.get("id", "")

    def __repr__(self) -> str:
        return f"AdaResponse(model={self.model!r}, content={self.content[:50]!r}...)"


class Ada:
    """Ada API Client.

    Args:
        api_key: Your Ada API key (ada_live_xxx or ada_test_xxx)
        base_url: Ada API base URL
        timeout: Request timeout in seconds
    """

    DEFAULT_URL = "https://ada-core-api-production.up.railway.app"

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_URL,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def chat(
        self,
        message: str,
        *,
        model: str | None = None,
        node_set: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system: str | None = None,
    ) -> AdaResponse:
        """Send a chat message and get a response.

        Args:
            message: User message
            model: Optional model override
            node_set: Optional node set (code_reviewer, growth_hacker, creative_director)
            temperature: Temperature (0.0-2.0)
            max_tokens: Max response tokens
            system: Optional system prompt
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
        }
        if model:
            payload["model"] = model
        if max_tokens:
            payload["max_tokens"] = max_tokens

        resp = self._client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        return AdaResponse(resp.json())

    def stream(
        self,
        message: str,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> Iterator[str]:
        """Stream a chat response token by token.

        Yields content deltas as strings.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if model:
            payload["model"] = model

        with self._client.stream("POST", "/v1/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    def route(self, message: str) -> dict[str, str]:
        """Get model recommendation without executing."""
        resp = self._client.post("/v1/route", json={
            "messages": [{"role": "user", "content": message}],
        })
        resp.raise_for_status()
        return resp.json()

    def models(self) -> list[dict[str, Any]]:
        """List available models."""
        resp = self._client.get("/v1/models")
        resp.raise_for_status()
        return resp.json().get("data", [])

    def health(self) -> dict[str, Any]:
        """Check API health."""
        resp = self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> Ada:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
