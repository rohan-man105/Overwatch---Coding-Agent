import subprocess
from pathlib import Path

from agents import function_tool
from services.weaviate import utils


def _project_root() -> Path:
    project = Path(utils.url).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f"Selected project does not exist: {project}")
    return project


def _project_file(file_path: str, project: Path) -> str:
    candidate = Path(file_path)
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (project / candidate).resolve()

    try:
        return str(candidate.relative_to(project))
    except ValueError as error:
        raise ValueError("File path must be inside the selected project") from error


def run_git(args: list[str]):
    project = _project_root()

    result = subprocess.run(
        ["git", *args],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )

    return {
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@function_tool()
def file_history(file_path: str) -> dict:
    """Show Git commit history for one file in the selected repository."""
    project = _project_root()
    return run_git(
        ["log", "--oneline", "--follow", "--", _project_file(file_path, project)],
    )


@function_tool()
def file_blame(file_path: str) -> dict:
    """Show Git blame for one file in the selected repository."""
    project = _project_root()
    return run_git(
        ["blame", "--", _project_file(file_path, project)],
    )
