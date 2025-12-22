"""Unit tests for GitignoreFilter service."""

from pathlib import Path

from lazyclaude.services.gitignore_filter import (
    DEFAULT_SKIP_DIRS,
    GitignoreFilter,
)


def test_default_patterns_without_gitignore(tmp_path: Path) -> None:
    """Test that default patterns are applied without .gitignore file."""
    filter_service = GitignoreFilter(project_root=tmp_path)

    assert filter_service.should_skip_dir("node_modules")
    assert filter_service.should_skip_dir(".venv")
    assert filter_service.should_skip_dir("__pycache__")
    assert not filter_service.should_skip_dir("src")


def test_patterns_from_gitignore(tmp_path: Path) -> None:
    """Test that patterns from .gitignore file are loaded and applied."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("*.log\ntemp/\n# comment\n\n")

    filter_service = GitignoreFilter(project_root=tmp_path)

    test_file = tmp_path / "test.log"
    assert filter_service.is_ignored(test_file)

    normal_file = tmp_path / "test.txt"
    assert not filter_service.is_ignored(normal_file)


def test_walk_filtered_basic(tmp_path: Path) -> None:
    """Test walk_filtered returns only non-ignored paths."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "test.md").write_text("test")

    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "test.md").write_text("test")

    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "test.md").write_text("test")

    filter_service = GitignoreFilter(project_root=tmp_path)
    results = list(filter_service.walk_filtered(tmp_path, "*.md"))

    assert len(results) == 1
    assert results[0] == tmp_path / "src" / "test.md"


def test_walk_filtered_with_custom_gitignore(tmp_path: Path) -> None:
    """Test walk_filtered respects custom .gitignore patterns."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("*.log\ntemp/\n")

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "file.txt").write_text("test")
    (tmp_path / "src" / "debug.log").write_text("log")

    (tmp_path / "temp").mkdir()
    (tmp_path / "temp" / "file.txt").write_text("test")

    filter_service = GitignoreFilter(project_root=tmp_path)
    results = list(filter_service.walk_filtered(tmp_path, "*.txt"))

    assert len(results) == 1
    assert results[0] == tmp_path / "src" / "file.txt"


def test_works_without_project_root() -> None:
    """Test that filter works with defaults only (no project_root)."""
    filter_service = GitignoreFilter(project_root=None)

    assert filter_service.should_skip_dir("node_modules")
    assert filter_service.should_skip_dir(".git")
    assert not filter_service.should_skip_dir("src")


def test_use_gitignore_flag(tmp_path: Path) -> None:
    """Test use_gitignore flag controls whether .gitignore is loaded."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("*.log\n")

    filter_with = GitignoreFilter(project_root=tmp_path, use_gitignore=True)
    filter_without = GitignoreFilter(project_root=tmp_path, use_gitignore=False)

    test_file = tmp_path / "test.log"
    assert filter_with.is_ignored(test_file)
    assert not filter_without.is_ignored(test_file)


def test_default_skip_dirs_comprehensive() -> None:
    """Test all default skip directories are recognized."""
    filter_service = GitignoreFilter(project_root=None)

    for dir_name in DEFAULT_SKIP_DIRS:
        assert filter_service.should_skip_dir(dir_name)


def test_walk_filtered_nested_structure(tmp_path: Path) -> None:
    """Test walk_filtered handles nested directory structures correctly."""
    (tmp_path / "src" / "components").mkdir(parents=True)
    (tmp_path / "src" / "components" / "test.md").write_text("test")
    (tmp_path / "src" / "utils").mkdir()
    (tmp_path / "src" / "utils" / "helper.md").write_text("test")

    (tmp_path / "node_modules" / "lib").mkdir(parents=True)
    (tmp_path / "node_modules" / "lib" / "test.md").write_text("test")

    filter_service = GitignoreFilter(project_root=tmp_path)
    results = sorted(filter_service.walk_filtered(tmp_path, "*.md"))

    assert len(results) == 2
    assert results[0] == tmp_path / "src" / "components" / "test.md"
    assert results[1] == tmp_path / "src" / "utils" / "helper.md"


def test_gitignore_with_comments_and_blank_lines(tmp_path: Path) -> None:
    """Test that .gitignore parser handles comments and blank lines."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(
        """
# This is a comment
*.log

# Another comment
temp/

"""
    )

    filter_service = GitignoreFilter(project_root=tmp_path)

    log_file = tmp_path / "test.log"
    assert filter_service.is_ignored(log_file)


def test_is_ignored_relative_path_handling(tmp_path: Path) -> None:
    """Test that is_ignored handles paths correctly relative to project root."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("src/*.log\n")

    filter_service = GitignoreFilter(project_root=tmp_path)

    log_in_src = tmp_path / "src" / "debug.log"
    log_in_root = tmp_path / "debug.log"

    assert filter_service.is_ignored(log_in_src)
    assert not filter_service.is_ignored(log_in_root)
