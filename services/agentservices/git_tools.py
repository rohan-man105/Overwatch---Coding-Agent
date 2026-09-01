import subprocess
from pathlib import Path


def run_git(args: list[str], project_path: str):
    project = Path(project_path).resolve()

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


def file_history(file_path: str, project_path: str):
    return run_git(
        ["log", "--oneline", "--follow", "--", file_path],
        project_path,
    )


def file_blame(file_path: str, project_path: str):
    return run_git(
        ["blame", "--", file_path],
        project_path,
    )