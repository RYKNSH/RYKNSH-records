"""Velie QA Agent — Repository Learning Engine.

Analyzes git commit history to build repo-specific bug pattern
knowledge. Extracts patterns from fix/bug commits to enhance
review accuracy with "institutional memory".
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_MEMORY_DIR = _DATA_DIR / "repo_memory"

# Common bug pattern categories
BUG_CATEGORIES = {
    "null_check": [
        r"\.get\(.*,\s*(None|''|\"\"|\[\]|\{\})\)",
        r"if\s+\w+\s+is\s+not\s+None",
        r"\?\.",  # Optional chaining added
        r"or\s+(''|\"\"|\[\]|\{\}|0|False)",
    ],
    "error_handling": [
        r"try\s*:",
        r"except\s+\w+",
        r"\.catch\(",
        r"raise\s+\w+",
    ],
    "type_safety": [
        r"int\(.*\)",
        r"str\(.*\)",
        r"isinstance\(",
        r":\s*(int|str|float|bool|list|dict)\b",
    ],
    "security": [
        r"\.strip\(",
        r"escape\(",
        r"sanitize",
        r"\.replace\(",
    ],
    "performance": [
        r"\.select_related\(",
        r"\.prefetch_related\(",
        r"async\s+def",
        r"await\s+",
        r"\bcache\b",
    ],
    "import_fix": [
        r"^[+-]\s*(from|import)\s+",
    ],
}


def _run_git(args: list[str], cwd: str) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.stdout


def extract_fix_commits(repo_path: str, limit: int = 500) -> list[dict]:
    """Extract fix/bug commits from a git repository.

    Args:
        repo_path: Path to the git repository.
        limit: Maximum number of commits to extract.

    Returns:
        List of commit dicts with sha, message, date.
    """
    # Get commits with fix/bug/hotfix in message
    log_output = _run_git(
        [
            "log",
            f"-n{limit}",
            "--grep=fix",
            "--grep=bug",
            "--grep=hotfix",
            "--grep=patch",
            "--all-match",
            "-i",  # case insensitive
            "--format=%H|||%s|||%ai",
        ],
        cwd=repo_path,
    )

    # Also get commits with "fix:" prefix (conventional commits)
    conventional_output = _run_git(
        [
            "log",
            f"-n{limit}",
            "--grep=^fix:",
            "--grep=^fix(",
            "--format=%H|||%s|||%ai",
        ],
        cwd=repo_path,
    )

    all_output = log_output + conventional_output
    commits = []
    seen_shas = set()

    for line in all_output.strip().splitlines():
        if not line or "|||" not in line:
            continue
        parts = line.split("|||", 2)
        if len(parts) < 3:
            continue

        sha, message, date = parts
        sha = sha.strip()
        if sha in seen_shas:
            continue
        seen_shas.add(sha)

        commits.append({
            "sha": sha,
            "message": message.strip(),
            "date": date.strip(),
        })

    logger.info("Extracted %d fix commits from %s", len(commits), repo_path)
    return commits


def get_commit_diff(repo_path: str, sha: str) -> str:
    """Get the diff for a specific commit."""
    return _run_git(
        ["diff", f"{sha}~1", sha, "--", "*.py", "*.ts", "*.tsx", "*.js", "*.jsx"],
        cwd=repo_path,
    )


def classify_bug_pattern(diff: str) -> list[dict]:
    """Classify a diff into bug pattern categories.

    Returns:
        List of pattern dicts with category, pattern, and file.
    """
    patterns_found = []
    current_file = None

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            parts = line.split(" b/", 1)
            current_file = parts[1] if len(parts) == 2 else None
            continue

        # Only look at added lines (the fix)
        if not line.startswith("+") or line.startswith("+++"):
            continue

        added_content = line[1:]

        for category, patterns in BUG_CATEGORIES.items():
            for pattern in patterns:
                if re.search(pattern, added_content):
                    patterns_found.append({
                        "category": category,
                        "pattern": pattern,
                        "file": current_file or "unknown",
                        "line": added_content.strip()[:100],
                    })
                    break  # One category match per line is enough

    return patterns_found


def build_repo_memory(repo_path: str, repo_name: str, max_commits: int = 200) -> dict:
    """Build a complete repo memory from git history.

    Args:
        repo_path: Local path to the git repo.
        repo_name: Repository full name (e.g., "RYKNSH/app").
        max_commits: Maximum fix commits to analyze.

    Returns:
        Memory dict with patterns, hotspots, and stats.
    """
    commits = extract_fix_commits(repo_path, limit=max_commits)

    # Analyze each commit
    all_patterns: list[dict] = []
    file_fix_counts: dict[str, int] = {}

    for commit in commits:
        try:
            diff = get_commit_diff(repo_path, commit["sha"])
            if not diff:
                continue

            patterns = classify_bug_pattern(diff)
            for p in patterns:
                p["commit_sha"] = commit["sha"]
                p["commit_message"] = commit["message"]
                all_patterns.append(p)

                # Track file hotspots
                f = p["file"]
                file_fix_counts[f] = file_fix_counts.get(f, 0) + 1

        except Exception:
            logger.debug("Failed to analyze commit %s", commit["sha"][:8])
            continue

    # Aggregate statistics
    category_counts: dict[str, int] = {}
    for p in all_patterns:
        cat = p["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Find top hotspot files
    hotspots = sorted(file_fix_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    memory = {
        "repo": repo_name,
        "total_fix_commits": len(commits),
        "total_patterns": len(all_patterns),
        "category_counts": category_counts,
        "hotspots": [{"file": f, "fix_count": c} for f, c in hotspots],
        "recent_patterns": all_patterns[-50:],  # Keep last 50 patterns
    }

    # Save to disk
    _save_memory(repo_name, memory)

    logger.info(
        "Built repo memory for %s: %d commits, %d patterns, top categories: %s",
        repo_name, len(commits), len(all_patterns),
        ", ".join(f"{k}({v})" for k, v in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True,
        )[:3]),
    )

    return memory


def _save_memory(repo_name: str, memory: dict) -> None:
    """Save repo memory to disk."""
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = repo_name.replace("/", "__")
    path = _MEMORY_DIR / f"{safe_name}.json"
    path.write_text(json.dumps(memory, indent=2, ensure_ascii=False))


def load_memory(repo_name: str) -> dict | None:
    """Load saved repo memory."""
    safe_name = repo_name.replace("/", "__")
    path = _MEMORY_DIR / f"{safe_name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def get_context_prompt(repo_name: str) -> str:
    """Generate a context prompt from repo memory for injection into reviews.

    Returns:
        A string to prepend to the review prompt, or empty string if no memory.
    """
    memory = load_memory(repo_name)
    if not memory or memory.get("total_patterns", 0) == 0:
        return ""

    # Build context from memory
    parts = [
        "## Repo-Specific Context (Learned from Git History)\n",
        f"Repository: {memory['repo']}",
        f"Analyzed {memory['total_fix_commits']} fix commits.\n",
    ]

    # Top bug categories
    cats = memory.get("category_counts", {})
    if cats:
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
        parts.append("**Common bug patterns in this repo:**")
        for cat, count in sorted_cats[:5]:
            parts.append(f"- {cat}: {count} occurrences")
        parts.append("")

    # Hotspot files
    hotspots = memory.get("hotspots", [])
    if hotspots:
        parts.append("**Bug-prone files (pay extra attention):**")
        for h in hotspots[:5]:
            parts.append(f"- `{h['file']}`: {h['fix_count']} fixes")
        parts.append("")

    parts.append(
        "Use this context to prioritize your review. "
        "Focus especially on the bug-prone categories and files listed above.\n"
    )

    return "\n".join(parts)


async def clone_and_analyze(
    repo_full_name: str,
    token: str,
    max_commits: int = 200,
) -> dict:
    """Clone a repo (shallow) and build repo memory.

    Args:
        repo_full_name: Repository full name (e.g., "RYKNSH/app").
        token: GitHub token for cloning.
        max_commits: Maximum fix commits to analyze.

    Returns:
        Repo memory dict.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"

        # Shallow clone with enough history for fix analysis
        subprocess.run(
            ["git", "clone", "--depth", str(max_commits * 2), clone_url, tmpdir],
            capture_output=True,
            text=True,
            timeout=120,
        )

        return build_repo_memory(tmpdir, repo_full_name, max_commits)
