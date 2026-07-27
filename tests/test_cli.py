from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from devrelay.cli import main


class CliTests(unittest.TestCase):
    def make_repository(self, directory: str) -> Path:
        repository = Path(directory)
        subprocess.run(
            ["git", "-C", str(repository), "init", "-b", "main"],
            check=True,
            capture_output=True,
        )
        return repository

    def test_prints_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.make_repository(directory)
            output = StringIO()

            with redirect_stdout(output):
                result = main(["snapshot", "--repo", str(repository), "--format", "json"])

            self.assertEqual(result, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["branch"], "main")
            self.assertIsNone(payload["head"])

    def test_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.make_repository(directory)
            destination = repository / "handoff.md"

            result = main(
                ["snapshot", "--repo", str(repository), "--output", str(destination)]
            )

            self.assertEqual(result, 0)
            self.assertIn("# Development handoff", destination.read_text(encoding="utf-8"))

    def test_reports_expected_error_without_traceback(self) -> None:
        errors = StringIO()
        with tempfile.TemporaryDirectory() as directory, redirect_stderr(errors):
            result = main(["snapshot", "--repo", directory])

        self.assertEqual(result, 2)
        self.assertIn("Not a Git repository", errors.getvalue())
        self.assertNotIn("Traceback", errors.getvalue())

    def test_uses_project_configuration_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.make_repository(directory)
            (repository / ".devrelay.json").write_text(
                '{"snapshot": {"format": "json", "recent": 0}}\n',
                encoding="utf-8",
            )
            output = StringIO()

            with redirect_stdout(output):
                result = main(["snapshot", "--repo", str(repository)])

            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output.getvalue())["recent_commits"], [])

    def test_cli_options_override_project_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.make_repository(directory)
            (repository / ".devrelay.json").write_text(
                '{"snapshot": {"format": "json"}}\n',
                encoding="utf-8",
            )
            output = StringIO()

            with redirect_stdout(output):
                result = main(
                    [
                        "snapshot",
                        "--repo",
                        str(repository),
                        "--format",
                        "markdown",
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue(output.getvalue().startswith("# Development handoff"))

    def test_reports_invalid_project_configuration(self) -> None:
        errors = StringIO()
        with tempfile.TemporaryDirectory() as directory, redirect_stderr(errors):
            repository = self.make_repository(directory)
            (repository / ".devrelay.json").write_text(
                '{"snapshot": {"recent": -1}}\n',
                encoding="utf-8",
            )

            result = main(["snapshot", "--repo", str(repository)])

        self.assertEqual(result, 2)
        self.assertIn(
            "Invalid .devrelay.json: snapshot.recent must be a non-negative integer",
            errors.getvalue(),
        )
        self.assertNotIn("Traceback", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
