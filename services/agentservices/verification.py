import subprocess
from pathlib import Path


ALLOWED_PROGRAMS = {"python", "pytest"}


def run_verification(command: list[str], project_path: str):
    """Run one approved verification command in the project directory."""

    if not command:
        raise ValueError("Command cannot be empty")

    if command[0] not in ALLOWED_PROGRAMS:
        raise ValueError(f"Command is not allowed: {command[0]}")

    project = Path(project_path).resolve()
    if not project.is_dir():
        raise ValueError(f"Project does not exist: {project}")

    result = subprocess.run(
        command,
        cwd=project,
        capture_output=True,
        text=True,
        timeout=120,
        shell=False,
    )

    return {
        "command": command,
        "passed": result.returncode == 0,
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }