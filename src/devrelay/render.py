"""Render repository snapshots for people and tools."""

from __future__ import annotations

import json

from .models import RepositorySnapshot


def render_json(snapshot: RepositorySnapshot) -> str:
    """Render a stable, machine-readable snapshot."""

    return json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False) + "\n"


def _sync_summary(snapshot: RepositorySnapshot) -> str:
    if not snapshot.upstream:
        return "No upstream configured"
    if snapshot.ahead is None or snapshot.behind is None:
        return f"Tracking `{snapshot.upstream}`"
    return f"{snapshot.ahead} ahead, {snapshot.behind} behind `{snapshot.upstream}`"


def render_markdown(snapshot: RepositorySnapshot) -> str:
    """Render a compact handoff document."""

    head = snapshot.head or "No commits yet"
    lines = [
        "# Development handoff",
        "",
        f"- Captured: `{snapshot.captured_at}`",
        f"- Repository: `{snapshot.repository_name}`",
        f"- Branch: `{snapshot.branch}`",
        f"- HEAD: `{head}`",
        f"- Working tree: {len(snapshot.changes)} changed file(s)",
        f"- Sync: {_sync_summary(snapshot)}",
        "",
        "## Working tree",
        "",
    ]

    if snapshot.changes:
        lines.extend(f"- `{change.status} {change.path}`" for change in snapshot.changes)
    else:
        lines.append("Clean.")

    lines.extend(["", "## Recent commits", ""])
    if snapshot.recent_commits:
        lines.extend(
            f"- `{commit.short_hash}` {commit.subject}" for commit in snapshot.recent_commits
        )
    else:
        lines.append("No commits yet.")

    lines.extend(
        [
            "",
            "## Resume checklist",
            "",
            "- Fetch the latest remote changes.",
            "- Review the working tree and recent commits above.",
            "- Run the project's verification commands before continuing.",
            "",
        ]
    )
    return "\n".join(lines)

