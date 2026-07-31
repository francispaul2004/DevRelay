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
class VerificationResult:
    """Concise outcome from one configured verification command."""

    command: tuple[str, ...]
    exit_code: int
    output: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


@dataclass(frozen=True, slots=True)
class DiffStatistics:
    """Aggregate line changes reported by one Git diff view."""

    files_changed: int
    additions: int
    deletions: int
    binary_files: int


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
    staged_diff: DiffStatistics
    unstaged_diff: DiffStatistics
    recent_commits: tuple[RecentCommit, ...]
    verification_results: tuple[VerificationResult, ...]

    @property
    def is_dirty(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        payload = asdict(self)
        payload["is_dirty"] = self.is_dirty
        for result in payload["verification_results"]:
            result["passed"] = result["exit_code"] == 0
        return payload
