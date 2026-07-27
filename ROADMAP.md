# DevRelay roadmap

Each scheduled run should complete at most one unchecked item, including tests and documentation.

## 0.1 — Repository snapshot

- [x] Create the dependency-free CLI and package structure.
- [x] Capture repository root, branch, HEAD, upstream, sync counts, status, and recent commits.
- [x] Render snapshots as Markdown and JSON.
- [x] Add atomic file output and standard-library tests.

## 0.2 — Useful session context

- [x] Add a project configuration file with safe defaults and schema validation.
- [ ] Run configured verification commands and capture concise results.
- [ ] Summarize staged and unstaged diff statistics.
- [ ] Extract nearby TODO/FIXME markers with configurable exclusions.
- [ ] Add a `check` command that reports whether a handoff is stale.

## 0.3 — Resume workflow

- [ ] Add a structured "next actions" section supplied by CLI flags or config.
- [ ] Compare two snapshots and explain what changed between sessions.
- [ ] Generate shell-safe resume commands without executing them.
- [ ] Add redaction rules for paths and user-defined sensitive patterns.

## 0.4 — GitHub collaboration

- [ ] Optionally include linked issue and pull-request metadata through `gh`.
- [ ] Add a pull-request handoff template.
- [ ] Publish signed release artifacts for macOS, Linux, and Windows.
