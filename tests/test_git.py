from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from devrelay.git import GitRepositoryError, capture_snapshot


def run_git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


class SnapshotTests(unittest.TestCase):
    def make_repository(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        repository = Path(temporary.name)
        run_git(repository, "init", "-b", "main")
        run_git(repository, "config", "user.name", "DevRelay Tests")
        run_git(repository, "config", "user.email", "devrelay@example.invalid")
        (repository / "README.md").write_text("# Demo\n", encoding="utf-8")
        run_git(repository, "add", "README.md")
        run_git(repository, "commit", "-m", "Initial commit")
        return temporary, repository

    def test_captures_clean_repository(self) -> None:
        temporary, repository = self.make_repository()
        self.addCleanup(temporary.cleanup)

        snapshot = capture_snapshot(repository)

        self.assertEqual(snapshot.repository_name, repository.name)
        self.assertEqual(snapshot.branch, "main")
        self.assertIsNotNone(snapshot.head)
        self.assertFalse(snapshot.is_dirty)
        self.assertEqual(snapshot.recent_commits[0].subject, "Initial commit")

    def test_captures_modified_and_untracked_files(self) -> None:
        temporary, repository = self.make_repository()
        self.addCleanup(temporary.cleanup)
        (repository / "README.md").write_text("# Changed\n", encoding="utf-8")
        (repository / "notes.txt").write_text("Next step\n", encoding="utf-8")

        snapshot = capture_snapshot(repository)

        self.assertTrue(snapshot.is_dirty)
        self.assertEqual(
            {(change.status, change.path) for change in snapshot.changes},
            {(" M", "README.md"), ("??", "notes.txt")},
        )

    def test_separates_staged_and_unstaged_diff_statistics(self) -> None:
        temporary, repository = self.make_repository()
        self.addCleanup(temporary.cleanup)
        (repository / "README.md").write_text("# Changed\nNew line\n", encoding="utf-8")
        run_git(repository, "add", "README.md")
        (repository / "README.md").write_text(
            "# Changed again\nNew line\nAnother line\n", encoding="utf-8"
        )

        snapshot = capture_snapshot(repository)

        self.assertEqual(snapshot.staged_diff.files_changed, 1)
        self.assertEqual(snapshot.staged_diff.additions, 2)
        self.assertEqual(snapshot.staged_diff.deletions, 1)
        self.assertEqual(snapshot.unstaged_diff.files_changed, 1)
        self.assertEqual(snapshot.unstaged_diff.additions, 2)
        self.assertEqual(snapshot.unstaged_diff.deletions, 1)

    def test_rejects_non_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(GitRepositoryError, "Not a Git repository"):
                capture_snapshot(directory)


if __name__ == "__main__":
    unittest.main()
