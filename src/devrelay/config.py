"""Project configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


CONFIG_FILENAME = ".devrelay.json"


class ConfigurationError(ValueError):
    """Raised when a project configuration file is invalid."""


@dataclass(frozen=True, slots=True)
class SnapshotConfig:
    """Safe defaults for the snapshot command."""

    format: str = "markdown"
    recent: int = 5


def _invalid(path: Path, message: str) -> ConfigurationError:
    return ConfigurationError(f"Invalid {path.name}: {message}")


def _object(value: Any, path: Path, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _invalid(path, f"{location} must be an object")
    return value


def load_config(repository_root: Path) -> SnapshotConfig:
    """Load configuration from *repository_root*, or return safe defaults."""

    path = repository_root / CONFIG_FILENAME
    if not path.exists():
        return SnapshotConfig()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise _invalid(path, f"line {error.lineno}, column {error.colno}: {error.msg}") from error
    except OSError as error:
        raise ConfigurationError(f"Could not read {path}: {error}") from error

    root = _object(payload, path, "top level")
    unknown_root = sorted(set(root) - {"snapshot"})
    if unknown_root:
        raise _invalid(path, f"unknown top-level key: {unknown_root[0]}")

    snapshot = _object(root.get("snapshot", {}), path, "snapshot")
    unknown_snapshot = sorted(set(snapshot) - {"format", "recent"})
    if unknown_snapshot:
        raise _invalid(path, f"unknown snapshot key: {unknown_snapshot[0]}")

    output_format = snapshot.get("format", "markdown")
    if not isinstance(output_format, str) or output_format not in {"markdown", "json"}:
        raise _invalid(path, "snapshot.format must be \"markdown\" or \"json\"")

    recent = snapshot.get("recent", 5)
    if isinstance(recent, bool) or not isinstance(recent, int) or recent < 0:
        raise _invalid(path, "snapshot.recent must be a non-negative integer")

    return SnapshotConfig(format=output_format, recent=recent)
