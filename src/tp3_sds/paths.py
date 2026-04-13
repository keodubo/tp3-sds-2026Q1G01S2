from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        if (candidate / "CLAUDE.md").exists() and (candidate / "docs" / "wiki").exists():
            return candidate
    return current


def wiki_dir(root: Path) -> Path:
    return root / "docs" / "wiki"


def raw_dir(root: Path) -> Path:
    return root / "docs" / "raw"
