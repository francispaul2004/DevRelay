"""Run project-configured verification commands."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .models import VerificationResult


OUTPUT_LIMIT = 1000


def _concise_output(stdout: str, stderr: str) -> str:
    output = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
    if len(output) <= OUTPUT_LIMIT:
        return output
    return output[: OUTPUT_LIMIT - 1].rstrip() + "…"


def run_verification_commands(
    repository: Path,
    commands: tuple[tuple[str, ...], ...],
) -> tuple[VerificationResult, ...]:
    """Run configured argument lists in *repository* and return their outcomes."""

    results: list[VerificationResult] = []
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            results.append(
                VerificationResult(
                    command=command,
                    exit_code=completed.returncode,
                    output=_concise_output(completed.stdout, completed.stderr),
                )
            )
        except OSError as error:
            results.append(
                VerificationResult(command=command, exit_code=127, output=str(error))
            )
    return tuple(results)
