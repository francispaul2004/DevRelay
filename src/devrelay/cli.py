"""Command-line interface for DevRelay."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

from . import __version__
from .git import GitRepositoryError, capture_snapshot
from .render import render_json, render_markdown


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
        default="markdown",
        help="Output format (default: markdown).",
    )
    snapshot.add_argument("--output", help="Write to a file instead of standard output.")
    snapshot.add_argument(
        "--recent",
        type=int,
        default=5,
        metavar="COUNT",
        help="Number of recent commits to include (default: 5).",
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


def main(arguments: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = _parser()
    options = parser.parse_args(arguments)
    if options.command != "snapshot":
        parser.error("a command is required")

    if options.recent < 0:
        parser.error("--recent must be zero or greater")

    try:
        snapshot = capture_snapshot(options.repo, recent_limit=options.recent)
        content = render_json(snapshot) if options.format == "json" else render_markdown(snapshot)
        if options.output:
            _atomic_write(Path(options.output), content)
        else:
            sys.stdout.write(content)
        return 0
    except (GitRepositoryError, OSError) as error:
        print(f"devrelay: {error}", file=sys.stderr)
        return 2


def entrypoint() -> None:
    """Console-script adapter."""

    raise SystemExit(main())

