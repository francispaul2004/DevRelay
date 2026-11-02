"""Command-line interface for DevRelay."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile

from . import __version__
from .config import ConfigurationError, load_config
from .git import GitRepositoryError, capture_snapshot, repository_root
from .render import render_json, render_markdown
from .verify import run_verification_commands


class HandoffCheckError(ValueError):
    """Raised when a saved handoff cannot be checked."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="devrelay",
        description="Create a portable snapshot for resuming Git work elsewhere.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    snapshot = commands.add_parser("snapshot", help="Capture the current repository context.")
    snapshot.add_argument("--repo", default=".", help="Path inside the Git repository.")
    snapshot.add_argument(
        "--format",
        choices=("markdown", "json"),
        default=None,
        help="Output format (default: project configuration or markdown).",
    )
    snapshot.add_argument("--output", help="Write to a file instead of standard output.")
    snapshot.add_argument(
        "--recent",
        type=int,
        default=None,
        metavar="COUNT",
        help="Recent commits to include (default: project configuration or 5).",
    )

    check = commands.add_parser("check", help="Report whether a JSON handoff is stale.")
    check.add_argument("handoff", help="Path to a JSON handoff created by snapshot.")
    check.add_argument(
        "--max-age",
        type=float,
        default=24,
        metavar="HOURS",
        help="Maximum handoff age in hours (default: 24).",
    )
    return parser


def _atomic_write(destination: Path, content: str) -> None:
    destination = destination.expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        delete=False,
    ) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.replace(destination)


def _captured_at(handoff: Path) -> datetime:
    try:
        payload = json.loads(handoff.read_text(encoding="utf-8"))
    except OSError as error:
        raise HandoffCheckError(f"Unable to read handoff: {handoff}") from error
    except json.JSONDecodeError as error:
        raise HandoffCheckError("Handoff is not valid JSON") from error

    captured_at = payload.get("captured_at") if isinstance(payload, dict) else None
    if not isinstance(captured_at, str):
        raise HandoffCheckError("Handoff does not contain a captured_at timestamp")
    try:
        timestamp = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise HandoffCheckError("Handoff has an invalid captured_at timestamp") from error
    if timestamp.tzinfo is None:
        raise HandoffCheckError("Handoff captured_at timestamp must include a timezone")
    return timestamp.astimezone(timezone.utc)


def _check_handoff(handoff: Path, max_age_hours: float) -> int:
    if max_age_hours < 0:
        raise HandoffCheckError("--max-age must be zero or greater")

    captured_at = _captured_at(handoff)
    age = datetime.now(timezone.utc) - captured_at
    maximum_age = max_age_hours * 3600
    if age.total_seconds() > maximum_age:
        print(
            f"Handoff is stale: captured {age.total_seconds() / 3600:.1f} hours ago "
            f"(maximum {max_age_hours:g} hours)."
        )
        return 1
    print(
        f"Handoff is current: captured {age.total_seconds() / 3600:.1f} hours ago "
        f"(maximum {max_age_hours:g} hours)."
    )
    return 0


def main(arguments: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = _parser()
    options = parser.parse_args(arguments)
    if options.command == "check":
        try:
            return _check_handoff(Path(options.handoff), options.max_age)
        except HandoffCheckError as error:
            print(f"devrelay: {error}", file=sys.stderr)
            return 2

    if options.recent is not None and options.recent < 0:
        parser.error("--recent must be zero or greater")

    try:
        root = repository_root(options.repo)
        config = load_config(root)
        output_format = options.format or config.format
        recent = options.recent if options.recent is not None else config.recent
        verification_results = run_verification_commands(
            root, config.verification_commands
        )
        snapshot = capture_snapshot(
            root,
            recent_limit=recent,
            verification_results=verification_results,
            marker_exclusions=config.marker_exclusions,
        )
        content = render_json(snapshot) if output_format == "json" else render_markdown(snapshot)
        if options.output:
            _atomic_write(Path(options.output), content)
        else:
            sys.stdout.write(content)
        return 0
    except (ConfigurationError, GitRepositoryError, OSError) as error:
        print(f"devrelay: {error}", file=sys.stderr)
        return 2


def entrypoint() -> None:
    """Console-script adapter."""

    raise SystemExit(main())
