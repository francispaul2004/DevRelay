"""Reject tool-specific wording from files and public Git metadata."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _text(points: tuple[int, ...]) -> str:
    return "".join(chr(point) for point in points)


_SINGLE_WORDS = tuple(
    _text(points)
    for points in (
        (97, 105),
        (99, 104, 97, 116, 103, 112, 116),
        (99, 111, 100, 101, 120),
        (111, 112, 101, 110, 97, 105),
        (108, 108, 109),
    )
)

_PHRASES = tuple(
    _text(points)
    for points in (
        (97, 114, 116, 105, 102, 105, 99, 105, 97, 108, 32, 105, 110, 116, 101, 108, 108, 105, 103, 101, 110, 99, 101),
        (108, 97, 110, 103, 117, 97, 103, 101, 32, 109, 111, 100, 101, 108),
        (108, 97, 114, 103, 101, 32, 108, 97, 110, 103, 117, 97, 103, 101, 32, 109, 111, 100, 101, 108),
        (105, 109, 112, 108, 101, 109, 101, 110, 116, 97, 116, 105, 111, 110, 32, 97, 115, 115, 105, 115, 116, 97, 110, 116),
        (116, 101, 120, 116, 32, 103, 101, 110, 101, 114, 97, 116, 105, 111, 110),
        (116, 101, 120, 116, 45, 103, 101, 110, 101, 114, 97, 116, 105, 111, 110),
        (97, 117, 116, 111, 109, 97, 116, 101, 100, 32, 97, 117, 116, 104, 111, 114, 115, 104, 105, 112),
        (109, 97, 99, 104, 105, 110, 101, 32, 103, 101, 110, 101, 114, 97, 116, 101, 100),
        (109, 97, 99, 104, 105, 110, 101, 45, 103, 101, 110, 101, 114, 97, 116, 101, 100),
        (29983, 24037, 26234, 33021),
        (22823, 35821, 35328, 27169, 22411),
        (29983, 25104, 24335, 20154, 24037, 26234, 33021),
        (26234, 33021, 21161, 25163),
        (26426, 22120, 29983, 25104),
        (27169, 22411, 29983, 25104),
    )
)

_WORD_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9_])(?:{'|'.join(re.escape(term) for term in _SINGLE_WORDS)})(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
_PHRASE_PATTERN = re.compile(
    "|".join(re.escape(term) for term in _PHRASES),
    re.IGNORECASE,
)


def _search_pattern() -> str:
    words = "|".join(re.escape(term) for term in _SINGLE_WORDS)
    phrases = "|".join(re.escape(term) for term in _PHRASES)
    return rf"(?<![A-Za-z0-9_])(?:{words})(?![A-Za-z0-9_])|(?:{phrases})"


def contains_restricted_wording(value: str) -> bool:
    """Return whether *value* contains wording excluded from public output."""

    return bool(_WORD_PATTERN.search(value) or _PHRASE_PATTERN.search(value))


def _git(*arguments: str, input_text: str | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        input=None if input_text is None else input_text.encode(),
        check=False,
        capture_output=True,
    )


def _decode_paths(output: bytes) -> tuple[str, ...]:
    return tuple(part.decode("utf-8", errors="surrogateescape") for part in output.split(b"\0") if part)


def _is_text(content: bytes) -> bool:
    return b"\0" not in content[:8192]


def _scan_content(label: str, content: bytes, issues: list[str]) -> None:
    if not _is_text(content):
        return
    text = content.decode("utf-8", errors="replace")
    for number, line in enumerate(text.splitlines(), start=1):
        if contains_restricted_wording(line):
            issues.append(f"{label}:{number}: restricted public wording")


def _scan_path(label: str, issues: list[str]) -> None:
    if contains_restricted_wording(label):
        issues.append(f"{label}: restricted wording in path")


def _scan_added_patch(label: str, patch: bytes, issues: list[str]) -> None:
    text = patch.decode("utf-8", errors="replace")
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("+++ "):
            _scan_path(line[4:], issues)
        elif line.startswith("+") and contains_restricted_wording(line[1:]):
            issues.append(f"{label}:{number}: restricted public wording")


def scan_worktree(issues: list[str]) -> None:
    search = shutil.which("rg")
    if search:
        common = [
            search,
            "--hidden",
            "--glob",
            "!.git/**",
            "--glob",
            "!*.pyc",
            "--no-messages",
        ]
        paths = subprocess.run(
            [*common, "--files"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if paths.returncode not in (0, 1):
            raise RuntimeError(paths.stderr.decode(errors="replace").strip())
        for relative in paths.stdout.decode("utf-8", errors="replace").splitlines():
            _scan_path(relative, issues)

        matches = subprocess.run(
            [*common, "--line-number", "--ignore-case", "--pcre2", _search_pattern(), "."],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if matches.returncode == 0:
            issues.append("working tree: restricted public wording")
        elif matches.returncode > 1:
            raise RuntimeError(matches.stderr.decode(errors="replace").strip())
        return

    result = _git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    for relative in _decode_paths(result.stdout):
        _scan_path(relative, issues)
        path = ROOT / relative
        if path.is_file():
            _scan_content(relative, path.read_bytes(), issues)


def scan_staged(issues: list[str]) -> None:
    result = _git(
        "diff",
        "--cached",
        "--no-ext-diff",
        "--no-renames",
        "--text",
        "--unified=0",
        "--",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    _scan_added_patch("staged diff", result.stdout, issues)


def scan_history(issues: list[str]) -> None:
    branches = _git("for-each-ref", "--format=%(refname:short)", "refs/heads")
    if branches.returncode == 0:
        _scan_content("branch names", branches.stdout, issues)

def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate wording intended for public Git output.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--staged", action="store_true", help="Check files staged for commit.")
    scope.add_argument("--history", action="store_true", help="Check files and local Git history.")
    scope.add_argument("--message", type=Path, help="Check a pending commit message file.")
    options = parser.parse_args(arguments)

    issues: list[str] = []
    try:
        if options.staged:
            scan_staged(issues)
        elif options.message:
            _scan_content("commit message", options.message.read_bytes(), issues)
        elif options.history:
            scan_worktree(issues)
            scan_history(issues)
        else:
            scan_worktree(issues)
    except (OSError, RuntimeError) as error:
        print(f"public-text check failed: {error}", file=sys.stderr)
        return 2

    if issues:
        print("Public-text validation failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print("Public-text validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
