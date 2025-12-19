"""Tests for memory file reference resolution."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, MemoryFileRef
from lazyclaude.services.parsers.memory_file import MemoryFileParser


class TestMemoryFileRefResolution:
    """Tests for _resolve_references() method."""

    def test_resolve_relative_reference(
        self,
        fs,
        fake_home: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        """Relative reference is resolved from memory file's directory."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(
            project_config / "CLAUDE.md",
            contents="@code-style.md\n\n# Project",
        )
        fs.create_file(
            project_config / "code-style.md",
            contents="# Code Style Guide",
        )

        parser = MemoryFileParser()
        result = parser.parse(project_config / "CLAUDE.md", ConfigLevel.PROJECT)

        refs: list[MemoryFileRef] = result.metadata.get("refs", [])
        assert len(refs) == 1
        assert refs[0].name == "code-style.md"
        assert refs[0].exists is True
        assert refs[0].content is not None
        assert "Code Style Guide" in refs[0].content

    def test_resolve_primary_memory_file_references(
        self,
        fs,
        fake_home: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        """References to primary memory files are resolved."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(
            project_config / "CLAUDE.md",
            contents="@AGENTS.md\n@CLAUDE.local.md\n\n# Root",
        )
        fs.create_file(project_config / "AGENTS.md", contents="# Agents")
        fs.create_file(project_config / "CLAUDE.local.md", contents="# Local")

        parser = MemoryFileParser()
        result = parser.parse(project_config / "CLAUDE.md", ConfigLevel.PROJECT)

        refs: list[MemoryFileRef] = result.metadata.get("refs", [])
        assert len(refs) == 2
        names = [r.name for r in refs]
        assert "AGENTS.md" in names
        assert "CLAUDE.local.md" in names

    def test_resolve_missing_reference(
        self,
        fs,
        fake_home: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        """Missing reference is marked as non-existent."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(
            project_config / "CLAUDE.md",
            contents="@missing-file.md\n\n# Project",
        )

        parser = MemoryFileParser()
        result = parser.parse(project_config / "CLAUDE.md", ConfigLevel.PROJECT)

        refs: list[MemoryFileRef] = result.metadata.get("refs", [])
        assert len(refs) == 1
        assert refs[0].name == "missing-file.md"
        assert refs[0].exists is False
        assert refs[0].content is None

    def test_resolve_home_reference(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Reference with ~/ prefix resolves to home directory."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(
            project_config / "CLAUDE.md",
            contents="@~/.claude/user-guide.md\n\n# Project",
        )
        user_claude = fake_home / ".claude"
        fs.create_dir(user_claude)
        fs.create_file(
            user_claude / "user-guide.md",
            contents="# User Guide",
        )

        parser = MemoryFileParser()
        result = parser.parse(project_config / "CLAUDE.md", ConfigLevel.PROJECT)

        refs: list[MemoryFileRef] = result.metadata.get("refs", [])
        assert len(refs) == 1
        assert refs[0].name == "~/.claude/user-guide.md"
        assert refs[0].exists is True
        assert "User Guide" in refs[0].content

    def test_resolve_nested_references_recursive(
        self,
        fs,
        fake_home: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        """Nested @references are resolved recursively."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(
            project_config / "CLAUDE.md",
            contents="@level1.md\n\n# Root",
        )
        fs.create_file(
            project_config / "level1.md",
            contents="@level2.md\n\n# Level 1",
        )
        fs.create_file(
            project_config / "level2.md",
            contents="# Level 2",
        )

        parser = MemoryFileParser()
        result = parser.parse(project_config / "CLAUDE.md", ConfigLevel.PROJECT)

        refs: list[MemoryFileRef] = result.metadata.get("refs", [])
        assert len(refs) == 1
        assert refs[0].name == "level1.md"
        assert refs[0].exists is True
        assert len(refs[0].children) == 1
        assert refs[0].children[0].name == "level2.md"
        assert refs[0].children[0].exists is True

    def test_resolve_stops_at_max_depth(
        self,
        fs,
        fake_home: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        """Reference resolution stops at depth 5 with unresolved refs."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)

        for i in range(7):
            next_ref = f"@level{i + 1}.md" if i < 6 else ""
            fs.create_file(
                project_config / f"level{i}.md",
                contents=f"{next_ref}\n\n# Level {i}",
            )

        fs.create_file(
            project_config / "CLAUDE.md",
            contents="@level0.md\n\n# Root",
        )

        parser = MemoryFileParser()
        result = parser.parse(project_config / "CLAUDE.md", ConfigLevel.PROJECT)

        def find_deepest_ref(
            refs: list[MemoryFileRef],
        ) -> MemoryFileRef | None:
            for ref in refs:
                if ref.children:
                    deeper = find_deepest_ref(ref.children)
                    if deeper:
                        return deeper
                return ref
            return None

        refs: list[MemoryFileRef] = result.metadata.get("refs", [])
        deepest = find_deepest_ref(refs)
        assert deepest is not None
        assert deepest.exists is False
        assert deepest.content is None

    def test_resolve_circular_reference(
        self,
        fs,
        fake_home: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        """Circular references are detected and handled."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(
            project_config / "CLAUDE.md",
            contents="@file-a.md\n\n# Root",
        )
        fs.create_file(
            project_config / "file-a.md",
            contents="@file-b.md\n\n# A",
        )
        fs.create_file(
            project_config / "file-b.md",
            contents="@file-a.md\n\n# B (circular)",
        )

        parser = MemoryFileParser()
        result = parser.parse(project_config / "CLAUDE.md", ConfigLevel.PROJECT)

        refs: list[MemoryFileRef] = result.metadata.get("refs", [])
        assert len(refs) == 1
        assert refs[0].name == "file-a.md"

        file_b_children = refs[0].children
        assert len(file_b_children) == 1
        assert file_b_children[0].name == "file-b.md"
        assert len(file_b_children[0].children) == 1
        assert file_b_children[0].children[0].name == "file-a.md"
        assert file_b_children[0].children[0].children == []

    def test_resolve_multiple_references(
        self,
        fs,
        fake_home: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        """Multiple @references in same file are all resolved."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(
            project_config / "CLAUDE.md",
            contents="@file1.md\n@file2.md\n@file3.md\n\n# Root",
        )
        fs.create_file(project_config / "file1.md", contents="# File 1")
        fs.create_file(project_config / "file2.md", contents="# File 2")
        fs.create_file(project_config / "file3.md", contents="# File 3")

        parser = MemoryFileParser()
        result = parser.parse(project_config / "CLAUDE.md", ConfigLevel.PROJECT)

        refs: list[MemoryFileRef] = result.metadata.get("refs", [])
        assert len(refs) == 3
        names = [r.name for r in refs]
        assert "file1.md" in names
        assert "file2.md" in names
        assert "file3.md" in names


class TestUserMemoryFileDiscovery:
    """Tests for user-level memory file discovery."""

    def test_discover_user_claude_local_md(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """User-level CLAUDE.local.md is discovered at ~/.claude/."""
        from lazyclaude.services.discovery import ConfigDiscoveryService

        user_config = fake_home / ".claude"
        fs.create_dir(user_config)
        fs.create_file(
            user_config / "CLAUDE.local.md",
            contents="# User Local Preferences",
        )

        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        memory_files = service._discover_memory_files()

        user_local = [m for m in memory_files if m.name == "CLAUDE.local.md"]
        assert len(user_local) == 1
        assert user_local[0].level == ConfigLevel.USER
        assert "User Local Preferences" in (user_local[0].content or "")


class TestUserRulesDiscovery:
    """Tests for user-level rules discovery."""

    def test_discover_rules_from_user_rules_dir(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Rules in ~/.claude/rules/ are discovered as MEMORY_FILE type with USER level."""
        from lazyclaude.models.customization import CustomizationType
        from lazyclaude.services.discovery import ConfigDiscoveryService

        user_config = fake_home / ".claude"
        fs.create_dir(user_config / "rules")
        fs.create_file(
            user_config / "rules" / "global-style.md",
            contents="# Global Style Rules",
        )

        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        rules = service._discover_rules()

        user_rules = [r for r in rules if r.level == ConfigLevel.USER]
        assert len(user_rules) == 1
        assert user_rules[0].name == "global-style.md"
        assert user_rules[0].type == CustomizationType.MEMORY_FILE

    def test_discover_both_user_and_project_rules(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Both user and project rules are discovered."""
        from lazyclaude.services.discovery import ConfigDiscoveryService

        user_config = fake_home / ".claude"
        fs.create_dir(user_config / "rules")
        fs.create_file(
            user_config / "rules" / "user-rule.md",
            contents="# User Rule",
        )

        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config / "rules")
        fs.create_file(
            project_config / "rules" / "project-rule.md",
            contents="# Project Rule",
        )

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        rules = service._discover_rules()

        user_rules = [r for r in rules if r.level == ConfigLevel.USER]
        project_rules = [r for r in rules if r.level == ConfigLevel.PROJECT]

        assert len(user_rules) == 1
        assert user_rules[0].name == "user-rule.md"
        assert len(project_rules) == 1
        assert project_rules[0].name == "project-rule.md"


class TestRecursiveClaudeMdDiscovery:
    """Tests for recursive CLAUDE.md discovery in project subfolders."""

    def test_discover_claude_md_in_subfolders(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """CLAUDE.md files in project subdirectories are discovered."""
        from lazyclaude.services.discovery import ConfigDiscoveryService

        user_config = fake_home / ".claude"
        fs.create_dir(user_config)

        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(project_config / "CLAUDE.md", contents="# Root")

        src_dir = fake_project_root / "src"
        fs.create_dir(src_dir)
        fs.create_file(src_dir / "CLAUDE.md", contents="# Src Guide")

        docs_dir = fake_project_root / "docs"
        fs.create_dir(docs_dir)
        fs.create_file(docs_dir / "CLAUDE.md", contents="# Docs Guide")

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        memory_files = service._discover_memory_files()

        memory_names = [m.name for m in memory_files]
        assert any("CLAUDE.md" in n for n in memory_names)
        assert any("src" in n for n in memory_names)
        assert any("docs" in n for n in memory_names)

    def test_discover_project_local_at_claude_level(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """CLAUDE.local.md at .claude/ level is discovered."""
        from lazyclaude.services.discovery import ConfigDiscoveryService

        user_config = fake_home / ".claude"
        fs.create_dir(user_config)

        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)
        fs.create_file(project_config / "CLAUDE.local.md", contents="# Local")

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        memory_files = service._discover_memory_files()

        local_files = [m for m in memory_files if m.level == ConfigLevel.PROJECT_LOCAL]
        assert len(local_files) == 1
        assert local_files[0].name == "CLAUDE.local.md"
