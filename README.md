# DevRelay

DevRelay is a small, local-first CLI for handing development work from one device or session to another. It captures the Git context that is easy to lose between machines and renders it as readable Markdown or structured JSON.

The project is deliberately dependency-light: the first release uses only Python's standard library and the local Git executable.

## Current capabilities

- Detect a repository's root, branch, commit, and upstream.
- Report ahead/behind counts when an upstream exists.
- Capture modified, staged, and untracked files.
- Include recent commits for quick orientation.
- Render a snapshot as Markdown or JSON.
- Write atomically to a file or print to standard output.

## Quick start

DevRelay supports Python 3.11 or newer.

```bash
PYTHONPATH=src python3 -m devrelay snapshot --repo .
PYTHONPATH=src python3 -m devrelay snapshot --repo . --format json
PYTHONPATH=src python3 -m devrelay snapshot --repo . --output HANDOFF.md
```

For an editable installation:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
devrelay snapshot --repo . --output HANDOFF.md
```

## Example handoff

```markdown
# Development handoff

- Repository: `devrelay`
- Branch: `agent/add-snapshot`
- HEAD: `a1b2c3d`
- Working tree: 2 changed files
- Sync: 1 ahead, 0 behind `origin/main`

## Working tree

- `M  src/devrelay/cli.py`
- `?? tests/test_cli.py`
```

## Development

Run the test suite without installing third-party test tools:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Scheduled development rules are documented in [`MAINTENANCE.md`](MAINTENANCE.md), while planned increments live in [`ROADMAP.md`](ROADMAP.md).

## License

MIT
