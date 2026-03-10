"""Helpers for resolving writable project paths across local and Docker runs."""

from __future__ import annotations

import os
from pathlib import Path


def get_project_root(start_path: str | Path | None = None) -> Path:
    """Resolve the Velox project root in both source and installed-package layouts."""
    env_root = os.getenv("VELOX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    candidates: list[Path] = []
    if start_path is not None:
        candidates.append(Path(start_path).resolve())
    candidates.append(Path.cwd().resolve())

    for candidate in candidates:
        for root in [candidate, *candidate.parents]:
            if _looks_like_project_root(root):
                return root

    return Path.cwd().resolve()


def _looks_like_project_root(path: Path) -> bool:
    if (path / "pyproject.toml").exists():
        return True
    return (path / "src" / "velox").exists() and (path / "data").exists()
