"""Velie QA Agent — Auto-Fix PR Creator.

Creates fix branches, applies code corrections, and opens PRs
automatically when critical issues are detected.
"""

from __future__ import annotations

import base64
import logging
import re

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Threshold logic
# ---------------------------------------------------------------------------

_SEVERITY_RANK = {"critical": 2, "warning": 1, "clean": 0}


def should_auto_fix(severity: str, threshold: str) -> bool:
    """Determine if auto-fix should be triggered based on severity and threshold.

    Args:
        severity: Detected severity ("critical", "warning", "clean").
        threshold: Tenant setting ("critical", "warning", "off").

    Returns:
        True if auto-fix should be triggered.
    """
    if threshold == "off":
        return False

    severity_rank = _SEVERITY_RANK.get(severity, 0)
    threshold_rank = _SEVERITY_RANK.get(threshold, 0)

    return severity_rank >= threshold_rank


# ---------------------------------------------------------------------------
# GitHub API operations
# ---------------------------------------------------------------------------

async def get_default_branch(
    client: httpx.AsyncClient,
    repo: str,
    headers: dict,
) -> str:
    """Get the default branch name for a repository."""
    resp = await client.get(
        f"https://api.github.com/repos/{repo}",
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()["default_branch"]


async def get_pr_head_branch(
    client: httpx.AsyncClient,
    repo: str,
    pr_number: int,
    headers: dict,
) -> tuple[str, str]:
    """Get the head branch name and latest commit SHA for a PR.

    Returns:
        Tuple of (branch_name, head_sha).
    """
    resp = await client.get(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
        headers=headers,
    )
    resp.raise_for_status()
    pr_data = resp.json()
    return pr_data["head"]["ref"], pr_data["head"]["sha"]


async def create_fix_branch(
    client: httpx.AsyncClient,
    repo: str,
    base_sha: str,
    pr_number: int,
    headers: dict,
) -> str:
    """Create a fix branch from the PR's head SHA.

    Returns:
        The created branch name.
    """
    branch_name = f"velie/fix-pr-{pr_number}"

    resp = await client.post(
        f"https://api.github.com/repos/{repo}/git/refs",
        headers=headers,
        json={
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha,
        },
    )
    resp.raise_for_status()
    logger.info("Created fix branch %s from %s", branch_name, base_sha[:8])
    return branch_name


async def get_file_content(
    client: httpx.AsyncClient,
    repo: str,
    path: str,
    ref: str,
    headers: dict,
) -> tuple[str, str]:
    """Get file content and SHA from GitHub.

    Returns:
        Tuple of (decoded_content, file_sha).
    """
    resp = await client.get(
        f"https://api.github.com/repos/{repo}/contents/{path}",
        headers=headers,
        params={"ref": ref},
    )
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


async def commit_file_fix(
    client: httpx.AsyncClient,
    repo: str,
    branch: str,
    path: str,
    new_content: str,
    file_sha: str,
    message: str,
    headers: dict,
) -> None:
    """Commit a single file fix to the branch."""
    encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    resp = await client.put(
        f"https://api.github.com/repos/{repo}/contents/{path}",
        headers=headers,
        json={
            "message": message,
            "content": encoded,
            "sha": file_sha,
            "branch": branch,
        },
    )
    resp.raise_for_status()
    logger.info("Committed fix to %s on branch %s", path, branch)


async def apply_suggestions_to_branch(
    client: httpx.AsyncClient,
    repo: str,
    branch: str,
    suggestions: list[dict],
    headers: dict,
) -> int:
    """Apply suggestion fixes to files on the fix branch.

    Groups suggestions by file, fetches each file, applies the fixes,
    and commits the changes.

    Returns:
        Number of files successfully fixed.
    """
    # Group suggestions by file path
    by_file: dict[str, list[dict]] = {}
    for s in suggestions:
        by_file.setdefault(s["path"], []).append(s)

    fixed_count = 0

    for path, file_suggestions in by_file.items():
        try:
            content, file_sha = await get_file_content(
                client, repo, path, branch, headers,
            )

            # Apply each suggestion (simple string replacement)
            modified = content
            applied = []
            for s in file_suggestions:
                original = s["original"].strip()
                suggested = s["suggested"].strip()
                if original in modified:
                    modified = modified.replace(original, suggested, 1)
                    applied.append(s["reason"])

            if modified != content and applied:
                reasons = "; ".join(applied[:3])
                message = f"fix: {path} — {reasons}"
                await commit_file_fix(
                    client, repo, branch, path,
                    modified, file_sha, message, headers,
                )
                fixed_count += 1

        except Exception:
            logger.exception("Failed to apply fix to %s", path)
            continue

    return fixed_count


async def open_fix_pr(
    client: httpx.AsyncClient,
    repo: str,
    fix_branch: str,
    base_branch: str,
    pr_number: int,
    suggestions: list[dict],
    headers: dict,
) -> str:
    """Open a Fix PR targeting the original PR's branch.

    Returns:
        URL of the created Fix PR.
    """
    fix_summary = "\n".join(
        f"- `{s['path']}`: {s['reason']}"
        for s in suggestions[:10]
    )

    body = (
        f"## 🔧 Velie Auto-Fix for PR #{pr_number}\n\n"
        f"This PR contains automatic fixes for issues detected by Velie.\n\n"
        f"### Changes\n\n{fix_summary}\n\n"
        f"---\n"
        f"*Generated by [Velie CI](https://github.com/apps/velie-qa-agent) — "
        f"AI-powered code quality for every PR.*"
    )

    resp = await client.post(
        f"https://api.github.com/repos/{repo}/pulls",
        headers=headers,
        json={
            "title": f"🔧 Velie Auto-Fix: PR #{pr_number}",
            "body": body,
            "head": fix_branch,
            "base": base_branch,
        },
    )
    resp.raise_for_status()
    pr_url = resp.json()["html_url"]
    logger.info("Opened Fix PR: %s", pr_url)
    return pr_url
