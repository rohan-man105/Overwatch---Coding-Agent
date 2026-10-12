import pytest

from services.agentservices import verification
from services.weaviate import utils


@pytest.fixture(autouse=True)
def selected_project(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "url", str(tmp_path))
    return tmp_path


def test_py_compile_succeeds_for_file_in_selected_project(selected_project):
    source = selected_project / "valid.py"
    source.write_text("value = 1\n", encoding="utf-8")

    result = verification.execute_verification(
        ["python", "-m", "py_compile", "valid.py"]
    )

    assert result["passed"] is True
    assert result["return_code"] == 0
    assert result["timed_out"] is False


def test_py_compile_reports_syntax_failure(selected_project):
    source = selected_project / "invalid.py"
    source.write_text("def broken(:\n", encoding="utf-8")

    result = verification.execute_verification(
        ["python", "-m", "py_compile", "invalid.py"]
    )

    assert result["passed"] is False
    assert result["return_code"] != 0


def test_rejects_non_verification_command():
    with pytest.raises(ValueError, match="Only Python compilation and pytest"):
        verification.execute_verification(["git", "status"])


def test_rejects_target_outside_selected_project(selected_project):
    outside = selected_project.parent / "outside.py"

    with pytest.raises(ValueError, match="inside the selected project"):
        verification.execute_verification(
            ["python", "-m", "py_compile", str(outside)]
        )


def test_verifier_tool_has_expected_name():
    assert verification.run_verification.name == "run_verification"
