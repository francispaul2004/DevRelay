"""Git subprocess boundary for repository snapshot collection."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess

from .models import FileChange, RecentCommit, RepositorySnapshot, VerificationResult


class GitRepositoryError(RuntimeError):
    """Raised when a path cannot be inspected as a Git repository."""


def _run_git(
    repository: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise GitRepositoryError(message)
    return result


def _optional_git(repository: Path, *arguments: str) -> str | None:
    result = _run_git(repository, *arguments, check=False)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _parse_status(output: str) -> tuple[FileChange, ...]:
    changes: list[FileChange] = []
    for line in output.splitlines():
        if len(line) < 3:
            continue
        changes.append(FileChange(status=line[:2], path=line[3:]))
    return tuple(changes)


def _recent_commits(repository: Path, limit: int) -> tuple[RecentCommit, ...]:
    if limit <= 0:
        return ()
    output = _optional_git(
        repository,
        "log",
        f"-{limit}",
        "--pretty=format:%h%x09%s",
    )
    if not output:
        return ()

    commits: list[RecentCommit] = []
    for line in output.splitlines():
        short_hash, separator, subject = line.partition("\t")
        if separator:
            commits.append(RecentCommit(short_hash=short_hash, subject=subject))
    return tuple(commits)


def repository_root(path: str | Path = ".") -> Path:
    """Return the repository root containing *path*."""

    requested_path = Path(path).expanduser()
    if not requested_path.exists():
        raise GitRepositoryError(f"Path does not exist: {requested_path}")

    root_text = _optional_git(requested_path, "rev-parse", "--show-toplevel")
    if not root_text:
        raise GitRepositoryError(f"Not a Git repository: {requested_path}")
    return Path(root_text).resolve()


def capture_snapshot(
    path: str | Path = ".",
    recent_limit: int = 5,
    verification_results: tuple[VerificationResult, ...] = (),
) -> RepositorySnapshot:
    """Capture the current Git context for *path*.

    The path may point anywhere inside a worktree. Expected user errors are
    normalized into :class:`GitRepositoryError` for concise CLI reporting.
    """

    root = repository_root(path)
    branch = _optional_git(root, "symbolic-ref", "--short", "-q", "HEAD") or "(detached HEAD)"
    head = _optional_git(root, "rev-parse", "--short", "HEAD")
    upstream = _optional_git(
        root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    )

    ahead: int | None = None
    behind: int | None = None
    if upstream and head:
        counts = _optional_git(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        if counts:
            left, separator, right = counts.partition("\t")
            if separator:
                ahead, behind = int(left), int(right)

    status = _run_git(root, "status", "--short", "--untracked-files=all").stdout
    return RepositorySnapshot(
        schema_version=1,
        captured_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        repository_name=root.name,
        repository_root=str(root),
        branch=branch,
        head=head,
        upstream=upstream,
        ahead=ahead,
        behind=behind,
        changes=_parse_status(status),
        recent_commits=_recent_commits(root, recent_limit),
        verification_results=verification_results,
    )
