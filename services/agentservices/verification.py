"""Safe, local verification commands exposed to the Verifier agent."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agents import function_tool
from services.weaviate import utils


COMMAND_TIMEOUT_SECONDS = 120
MAX_OUTPUT_CHARS = 20_000


def _project_root() -> Path:
    """Return the repository selected by the CLI for the current CAS session."""
    project = Path(utils.url).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f"Selected project does not exist: {project}")
    return project


def _is_within_project(path_text: str, project: Path) -> bool:
    """Only allow verification targets inside the selected project."""
    target = Path(path_text)
    if not target.is_absolute():
        target = project / target

    try:
        target.resolve().relative_to(project)
    except ValueError:
        return False
    return True


def _validate_command(command: list[str], project: Path) -> list[str]:
    """Validate and normalize one narrowly scoped verification command."""
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("Command must be a non-empty list of strings")

    program = Path(command[0]).name.lower()
    if program in {"python", "python.exe"}:
        if len(command) < 4 or command[1:3] != ["-m", "py_compile"]:
            raise ValueError("Only 'python -m py_compile <file.py> [...]' is allowed")

        targets = command[3:]
        if any(not target.endswith(".py") for target in targets):
            raise ValueError("py_compile targets must be Python files")
        if any(not _is_within_project(target, project) for target in targets):
            raise ValueError("Verification targets must be inside the selected project")
        return [sys.executable, "-m", "py_compile", *targets]

    if program in {"pytest", "pytest.exe"}:
        targets = [part for part in command[1:] if not part.startswith("-")]
        if any(not _is_within_project(target, project) for target in targets):
            raise ValueError("Pytest targets must be inside the selected project")
        return [sys.executable, "-m", "pytest", *command[1:]]

    raise ValueError("Only Python compilation and pytest commands are allowed")


def _truncate(output: str) -> str:
    if len(output) <= MAX_OUTPUT_CHARS:
        return output
    return output[:MAX_OUTPUT_CHARS] + "\n...[output truncated]"


def _as_text(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def execute_verification(command: list[str]) -> dict:
    """Run one approved verification command against the selected repository."""
    project = _project_root()
    normalized_command = _validate_command(command, project)

    try:
        result = subprocess.run(
            normalized_command,
            cwd=project,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "command": normalized_command,
            "passed": False,
            "return_code": None,
            "stdout": _truncate(_as_text(error.stdout)),
            "stderr": _truncate(_as_text(error.stderr)),
            "timed_out": True,
            "error": f"Command timed out after {COMMAND_TIMEOUT_SECONDS} seconds",
        }

    return {
        "command": normalized_command,
        "passed": result.returncode == 0,
        "return_code": result.returncode,
        "stdout": _truncate(result.stdout),
        "stderr": _truncate(result.stderr),
        "timed_out": False,
        "error": None,
    }


@function_tool()
def run_verification(command: list[str]) -> dict:
    """Run an approved compile or pytest command in the repository selected by CAS.

    Allowed commands are `python -m py_compile <file.py> [...]` and
    `pytest [options] [path ...]`. Paths must stay inside the selected project.
    """
    return execute_verification(command)
