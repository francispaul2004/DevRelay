# DevRelay maintenance guide

This repository is developed through small scheduled maintenance runs and human review.

## Run contract

1. Read `README.md`, `ROADMAP.md`, and the current Git history before changing code.
2. Work on exactly one coherent, highest-priority unchecked roadmap item per run.
3. Keep the change small enough to review as one pull request. Avoid broad refactors and unrelated dependency upgrades.
4. Preserve all user changes. If the worktree is dirty for reasons unrelated to the task, stop and report the conflict.
5. Add or update tests for behavior changes and run the full standard-library test suite.
6. Update `ROADMAP.md` and relevant documentation only when the implementation actually changes their status.
7. Use a new `work/<short-description>` branch. Never commit directly to the default branch, force-push, rewrite published history, or delete unrelated user branches.
8. Keep all repository files and public Git metadata focused exclusively on the project. Remove unrelated provenance and tooling commentary.
9. Run the public-text check before committing and again before pushing. Correct every reported issue instead of bypassing the check.
10. Commit only files belonging to the selected task, push the branch, and open a ready pull request with validation results. Wait for required checks to complete successfully, squash-merge the pull request, delete its completed work branch, and synchronize the local default branch using fast-forward only. If a required check is pending or failing, or review is blocking, leave the pull request open for the next run; never bypass repository protections.
11. If GitHub authentication or networking is unavailable, do not start a new implementation. Report the blocker instead.

## Quality bar

- Support Python 3.11 and newer.
- Prefer the standard library until a dependency has a clear, documented benefit.
- Keep Git subprocess handling isolated in `src/devrelay/git.py`.
- Keep output rendering isolated in `src/devrelay/render.py`.
- Return actionable error messages without Python tracebacks for expected user errors.
- Never add placeholder filler, empty commits, fake timestamps, secrets, credentials, or machine-specific artifacts.
- Use neutral, project-specific language in files, commit messages, branch names, and pull-request text.

## Validation

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m devrelay snapshot --repo . --format json
python3 tools/check_public_text.py --history
git diff --check
```
