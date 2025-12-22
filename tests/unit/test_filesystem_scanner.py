"""Unit tests for FilesystemScanner with gitignore filtering."""

from pathlib import Path

from lazyclaude.services.filesystem_scanner import (
    FilesystemScanner,
    GlobStrategy,
    ScanConfig,
)
from lazyclaude.services.gitignore_filter import GitignoreFilter
from lazyclaude.services.parsers.slash_command import SlashCommandParser


def test_glob_strategy_respects_gitignore_file_patterns(tmp_path: Path) -> None:
    """Test that GLOB strategy filters files matching gitignore patterns."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.draft\n")

    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "production.md").write_text("---\nname: prod\n---\nContent")
    (agents_dir / "experimental.draft").write_text("---\nname: exp\n---\nContent")

    filter_service = GitignoreFilter(project_root=tmp_path)
    scanner = FilesystemScanner(gitignore_filter=filter_service)

    config = ScanConfig(
        subdir="agents",
        pattern="*",
        strategy=GlobStrategy.GLOB,
        parser_factory=SlashCommandParser,
    )

    results = scanner._get_files(agents_dir, config)

    assert len(results) == 1
    file_names = [f.name for f in results]
    assert "production.md" in file_names
    assert "experimental.draft" not in file_names


def test_glob_strategy_respects_gitignore_path_patterns(tmp_path: Path) -> None:
    """Test that GLOB strategy filters files matching path-based gitignore patterns."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("agents/secret.md\n")

    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "public.md").write_text("---\nname: public\n---\nContent")
    (agents_dir / "secret.md").write_text("---\nname: secret\n---\nContent")

    filter_service = GitignoreFilter(project_root=tmp_path)
    scanner = FilesystemScanner(gitignore_filter=filter_service)

    config = ScanConfig(
        subdir="agents",
        pattern="*.md",
        strategy=GlobStrategy.GLOB,
        parser_factory=SlashCommandParser,
    )

    results = scanner._get_files(agents_dir, config)

    assert len(results) == 1
    assert results[0].name == "public.md"


def test_glob_strategy_works_without_filter(tmp_path: Path) -> None:
    """Test that GLOB strategy works when no gitignore filter is provided."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "agent1.md").write_text("---\nname: a1\n---\nContent")
    (agents_dir / "agent2.md").write_text("---\nname: a2\n---\nContent")

    scanner = FilesystemScanner(gitignore_filter=None)

    config = ScanConfig(
        subdir="agents",
        pattern="*.md",
        strategy=GlobStrategy.GLOB,
        parser_factory=SlashCommandParser,
    )

    results = scanner._get_files(agents_dir, config)

    assert len(results) == 2


def test_subdir_strategy_respects_gitignore_file_patterns(tmp_path: Path) -> None:
    """Test that SUBDIR strategy filters files matching gitignore patterns."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("SKILL.md\n")

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    (skills_dir / "skill1").mkdir()
    (skills_dir / "skill1" / "SKILL.md").write_text("---\nname: skill1\n---\nContent")

    (skills_dir / "skill2").mkdir()
    (skills_dir / "skill2" / "SKILL.md").write_text("---\nname: skill2\n---\nContent")

    filter_service = GitignoreFilter(project_root=tmp_path)
    scanner = FilesystemScanner(gitignore_filter=filter_service)

    config = ScanConfig(
        subdir="skills",
        pattern="SKILL.md",
        strategy=GlobStrategy.SUBDIR,
        parser_factory=SlashCommandParser,
    )

    results = scanner._get_files(skills_dir, config)

    assert len(results) == 0


def test_subdir_strategy_respects_gitignore_path_patterns(tmp_path: Path) -> None:
    """Test that SUBDIR strategy filters files matching path-based patterns."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("skills/draft-*/SKILL.md\n")

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    (skills_dir / "prod-feature").mkdir()
    (skills_dir / "prod-feature" / "SKILL.md").write_text(
        "---\nname: prod\n---\nContent"
    )

    (skills_dir / "draft-experiment").mkdir()
    (skills_dir / "draft-experiment" / "SKILL.md").write_text(
        "---\nname: draft\n---\nContent"
    )

    filter_service = GitignoreFilter(project_root=tmp_path)
    scanner = FilesystemScanner(gitignore_filter=filter_service)

    config = ScanConfig(
        subdir="skills",
        pattern="SKILL.md",
        strategy=GlobStrategy.SUBDIR,
        parser_factory=SlashCommandParser,
    )

    results = scanner._get_files(skills_dir, config)

    assert len(results) == 1
    assert results[0].parent.name == "prod-feature"


def test_subdir_strategy_works_without_filter(tmp_path: Path) -> None:
    """Test that SUBDIR strategy works when no gitignore filter is provided."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    (skills_dir / "skill1").mkdir()
    (skills_dir / "skill1" / "SKILL.md").write_text("---\nname: skill1\n---\nContent")

    (skills_dir / "skill2").mkdir()
    (skills_dir / "skill2" / "SKILL.md").write_text("---\nname: skill2\n---\nContent")

    scanner = FilesystemScanner(gitignore_filter=None)

    config = ScanConfig(
        subdir="skills",
        pattern="SKILL.md",
        strategy=GlobStrategy.SUBDIR,
        parser_factory=SlashCommandParser,
    )

    results = scanner._get_files(skills_dir, config)

    assert len(results) == 2


def test_subdir_strategy_filters_both_directories_and_files(tmp_path: Path) -> None:
    """Test that SUBDIR strategy filters both at directory and file level."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("skills/draft-*/\nskills/*/SKILL.local\n")

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    (skills_dir / "prod-feature").mkdir()
    (skills_dir / "prod-feature" / "SKILL.md").write_text(
        "---\nname: prod\n---\nContent"
    )
    (skills_dir / "prod-feature" / "SKILL.local").write_text(
        "---\nname: local\n---\nContent"
    )

    (skills_dir / "draft-experiment").mkdir()
    (skills_dir / "draft-experiment" / "SKILL.md").write_text(
        "---\nname: draft\n---\nContent"
    )

    filter_service = GitignoreFilter(project_root=tmp_path)
    scanner = FilesystemScanner(gitignore_filter=filter_service)

    config_md = ScanConfig(
        subdir="skills",
        pattern="SKILL.md",
        strategy=GlobStrategy.SUBDIR,
        parser_factory=SlashCommandParser,
    )

    config_local = ScanConfig(
        subdir="skills",
        pattern="SKILL.local",
        strategy=GlobStrategy.SUBDIR,
        parser_factory=SlashCommandParser,
    )

    results_md = scanner._get_files(skills_dir, config_md)
    results_local = scanner._get_files(skills_dir, config_local)

    assert len(results_md) == 1
    assert results_md[0].parent.name == "prod-feature"
    assert len(results_local) == 0
