"""Command-line interface for DevRelay."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

from . import __version__
from .config import ConfigurationError, load_config
from .git import GitRepositoryError, capture_snapshot, repository_root
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

    if options.recent is not None and options.recent < 0:
        parser.error("--recent must be zero or greater")

    try:
        root = repository_root(options.repo)
        config = load_config(root)
        output_format = options.format or config.format
        recent = options.recent if options.recent is not None else config.recent
        snapshot = capture_snapshot(root, recent_limit=recent)
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
