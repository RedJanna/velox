"""Unit tests for project root resolution helpers."""

from pathlib import Path

from velox.utils.project_paths import get_project_root


def test_get_project_root_prefers_working_tree(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path / "demo"
    (project_root / "src" / "velox").mkdir(parents=True)
    (project_root / "data").mkdir()
    monkeypatch.chdir(project_root)

    resolved = get_project_root()

    assert resolved == project_root.resolve()


def test_get_project_root_respects_env_override(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path / "env-root"
    project_root.mkdir()
    monkeypatch.setenv("VELOX_PROJECT_ROOT", str(project_root))

    resolved = get_project_root(tmp_path / "other" / "file.py")

    assert resolved == project_root.resolve()
