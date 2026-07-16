"""Immutable data structures shared by collection and rendering."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FileChange:
    """One line from Git's stable porcelain status."""

    status: str
    path: str


@dataclass(frozen=True, slots=True)
class RecentCommit:
    """Compact commit context useful when resuming work."""

    short_hash: str
    subject: str


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    """Portable description of a repository at one point in time."""

    schema_version: int
    captured_at: str
    repository_name: str
    repository_root: str
    branch: str
    head: str | None
    upstream: str | None
    ahead: int | None
    behind: int | None
    changes: tuple[FileChange, ...]
    recent_commits: tuple[RecentCommit, ...]

    @property
    def is_dirty(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        payload = asdict(self)
        payload["is_dirty"] = self.is_dirty
        return payload

