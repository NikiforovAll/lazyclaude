"""Gitignore-based file filtering with directory pruning for performance."""

import fnmatch
import os
from collections.abc import Iterator
from pathlib import Path

import pathspec

DEFAULT_SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "build",
    "dist",
    ".eggs",
    ".tox",
    ".nox",
    "htmlcov",
    ".idea",
    ".vscode",
    "bin",
    "obj",
    ".vs",
    "packages",
}

DEFAULT_IGNORE_PATTERNS = [
    ".git/",
    "node_modules/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".mypy_cache/",
    ".pytest_cache/",
    "build/",
    "dist/",
    ".eggs/",
    "*.egg-info/",
    ".tox/",
    ".nox/",
    ".coverage",
    "htmlcov/",
    ".idea/",
    ".vscode/",
    "bin/",
    "obj/",
    ".vs/",
    "packages/",
]


class GitignoreFilter:
    """Filter for respecting gitignore patterns during file traversal."""

    def __init__(
        self, project_root: Path | None = None, use_gitignore: bool = True
    ) -> None:
        self._project_root = project_root
        self._skip_dirs = DEFAULT_SKIP_DIRS.copy()
        self._spec: pathspec.PathSpec | None = None

        patterns = DEFAULT_IGNORE_PATTERNS.copy()

        if use_gitignore and project_root:
            gitignore_patterns = self._load_gitignore(project_root)
            patterns.extend(gitignore_patterns)

        if patterns:
            self._spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    def _load_gitignore(self, root: Path) -> list[str]:
        """Load and parse .gitignore file if it exists."""
        gitignore_path = root / ".gitignore"
        if not gitignore_path.is_file():
            return []

        try:
            with gitignore_path.open("r", encoding="utf-8") as f:
                return [
                    line.strip()
                    for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]
        except (OSError, UnicodeDecodeError):
            return []

    def should_skip_dir(self, dirname: str) -> bool:
        """Fast check if directory name should be skipped."""
        return dirname in self._skip_dirs

    def is_ignored(self, path: Path) -> bool:
        """Check if path matches gitignore patterns."""
        if not self._spec:
            return False

        if not self._project_root:
            rel_path = path
        else:
            try:
                rel_path = path.relative_to(self._project_root)
            except ValueError:
                rel_path = path

        return self._spec.match_file(str(rel_path))

    def walk_filtered(self, root: Path, pattern: str) -> Iterator[Path]:
        """Walk directory tree with pruning, yielding paths matching pattern."""
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not self.should_skip_dir(d)]

            for filename in filenames:
                if fnmatch.fnmatch(filename, pattern):
                    file_path = Path(dirpath) / filename
                    if not self.is_ignored(file_path):
                        yield file_path
