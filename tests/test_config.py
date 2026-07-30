from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from devrelay.config import ConfigurationError, SnapshotConfig, load_config


class ConfigurationTests(unittest.TestCase):
    def write_config(self, directory: str, payload: object) -> Path:
        path = Path(directory) / ".devrelay.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_missing_file_uses_safe_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_config(Path(directory)), SnapshotConfig())

    def test_loads_snapshot_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(
                directory,
                {"snapshot": {"format": "json", "recent": 12}},
            )

            self.assertEqual(
                load_config(Path(directory)),
                SnapshotConfig(format="json", recent=12),
            )

    def test_loads_verification_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(
                directory,
                {"verification": {"commands": [["python3", "-m", "unittest"]]}},
            )

            self.assertEqual(
                load_config(Path(directory)).verification_commands,
                (("python3", "-m", "unittest"),),
            )

    def test_rejects_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(directory, {"snapshot": {"output": "handoff.md"}})

            with self.assertRaisesRegex(
                ConfigurationError,
                "unknown snapshot key: output",
            ):
                load_config(Path(directory))

    def test_rejects_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".devrelay.json"
            path.write_text("{", encoding="utf-8")

            with self.assertRaisesRegex(ConfigurationError, "line 1, column 2"):
                load_config(Path(directory))

    def test_rejects_boolean_recent_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(directory, {"snapshot": {"recent": True}})

            with self.assertRaisesRegex(
                ConfigurationError,
                "snapshot.recent must be a non-negative integer",
            ):
                load_config(Path(directory))

    def test_rejects_non_string_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(directory, {"snapshot": {"format": ["json"]}})

            with self.assertRaisesRegex(
                ConfigurationError,
                'snapshot.format must be "markdown" or "json"',
            ):
                load_config(Path(directory))

    def test_rejects_invalid_verification_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(directory, {"verification": {"commands": ["test"]}})

            with self.assertRaisesRegex(
                ConfigurationError,
                r"verification\.commands\[0\] must be a non-empty array of strings",
            ):
                load_config(Path(directory))


if __name__ == "__main__":
    unittest.main()
