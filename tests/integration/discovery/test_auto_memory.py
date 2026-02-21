"""Tests for auto memory discovery."""

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestProjectSlug:
    """Tests for project slug derivation."""

    def test_separators_become_hyphens(
        self, fs: FakeFilesystem, fake_home: Path
    ) -> None:
        """Path separators and special chars are replaced with hyphens."""
        project = Path("/home/user/dev/myproject")
        fs.create_dir(project)
        fs.create_dir(fake_home / ".claude")
        service = ConfigDiscoveryService(
            user_config_path=fake_home / ".claude",
            project_config_path=project / ".claude",
        )
        slug = service._get_project_slug()
        assert slug.endswith("-home-user-dev-myproject")
        assert "/" not in slug
        assert "\\" not in slug

    def test_dotfiles_in_path(self, fs: FakeFilesystem, fake_home: Path) -> None:
        """Dots in directory names are replaced with hyphens."""
        project = Path("/home/user/.config/tool")
        fs.create_dir(project)
        fs.create_dir(fake_home / ".claude")
        service = ConfigDiscoveryService(
            user_config_path=fake_home / ".claude",
            project_config_path=project / ".claude",
        )
        slug = service._get_project_slug()
        assert "--config-" in slug


class TestAutoMemoryDiscovery:
    """Tests for auto memory file discovery."""

    def _make_service(
        self,
        fs: FakeFilesystem,
        fake_home: Path,
        fake_project_root: Path,
    ) -> ConfigDiscoveryService:
        """Create a discovery service with auto memory directory set up."""
        user_claude = fake_home / ".claude"
        fs.create_dir(user_claude)
        return ConfigDiscoveryService(
            user_config_path=user_claude,
            project_config_path=fake_project_root / ".claude",
        )

    def test_no_auto_memory_dir_returns_empty(
        self, fs: FakeFilesystem, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Missing memory directory returns empty list."""
        service = self._make_service(fs, fake_home, fake_project_root)
        result = service._discover_auto_memory()
        assert result == []

    def test_discovers_memory_md_entrypoint(
        self, fs: FakeFilesystem, fake_home: Path, fake_project_root: Path
    ) -> None:
        """MEMORY.md is discovered as PROJECT_LOCAL level."""
        service = self._make_service(fs, fake_home, fake_project_root)
        slug = service._get_project_slug()
        memory_dir = fake_home / ".claude" / "projects" / slug / "memory"
        fs.create_file(
            memory_dir / "MEMORY.md", contents="# Auto Memory\nProject notes"
        )

        result = service._discover_auto_memory()

        assert len(result) == 1
        assert result[0].name == "MEMORY.md"
        assert result[0].level == ConfigLevel.PROJECT_LOCAL
        assert result[0].type == CustomizationType.MEMORY_FILE
        assert "Auto Memory" in result[0].content

    def test_topic_files_become_refs(
        self, fs: FakeFilesystem, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Sibling .md files are synthesized as MemoryFileRef children."""
        service = self._make_service(fs, fake_home, fake_project_root)
        slug = service._get_project_slug()
        memory_dir = fake_home / ".claude" / "projects" / slug / "memory"
        fs.create_file(memory_dir / "MEMORY.md", contents="# Index")
        fs.create_file(memory_dir / "debugging.md", contents="# Debug notes")
        fs.create_file(memory_dir / "patterns.md", contents="# Patterns")

        result = service._discover_auto_memory()

        assert len(result) == 1
        refs = result[0].metadata.get("refs", [])
        ref_names = {r.name for r in refs}
        assert "debugging.md" in ref_names
        assert "patterns.md" in ref_names

    def test_topic_file_content_loaded(
        self, fs: FakeFilesystem, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Synthesized refs have content loaded."""
        service = self._make_service(fs, fake_home, fake_project_root)
        slug = service._get_project_slug()
        memory_dir = fake_home / ".claude" / "projects" / slug / "memory"
        fs.create_file(memory_dir / "MEMORY.md", contents="# Index")
        fs.create_file(memory_dir / "api.md", contents="# API conventions")

        result = service._discover_auto_memory()

        refs = result[0].metadata["refs"]
        api_ref = next(r for r in refs if r.name == "api.md")
        assert api_ref.exists is True
        assert "API conventions" in api_ref.content

    def test_no_memory_md_discovers_individual_files(
        self, fs: FakeFilesystem, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Without MEMORY.md, each .md file is a standalone customization."""
        service = self._make_service(fs, fake_home, fake_project_root)
        slug = service._get_project_slug()
        memory_dir = fake_home / ".claude" / "projects" / slug / "memory"
        fs.create_file(memory_dir / "debugging.md", contents="# Debug")
        fs.create_file(memory_dir / "patterns.md", contents="# Patterns")

        result = service._discover_auto_memory()

        assert len(result) == 2
        names = {c.name for c in result}
        assert names == {"debugging.md", "patterns.md"}
        assert all(c.level == ConfigLevel.PROJECT_LOCAL for c in result)

    def test_non_md_files_ignored(
        self, fs: FakeFilesystem, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Non-.md files in memory dir are ignored."""
        service = self._make_service(fs, fake_home, fake_project_root)
        slug = service._get_project_slug()
        memory_dir = fake_home / ".claude" / "projects" / slug / "memory"
        fs.create_file(memory_dir / "MEMORY.md", contents="# Index")
        fs.create_file(memory_dir / "notes.txt", contents="not markdown")

        result = service._discover_auto_memory()

        assert len(result) == 1
        refs = result[0].metadata.get("refs", [])
        assert len(refs) == 0

    def test_existing_imports_not_duplicated(
        self, fs: FakeFilesystem, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Files already referenced via @import in MEMORY.md are not duplicated."""
        service = self._make_service(fs, fake_home, fake_project_root)
        slug = service._get_project_slug()
        memory_dir = fake_home / ".claude" / "projects" / slug / "memory"
        fs.create_file(
            memory_dir / "MEMORY.md",
            contents="# Index\nSee @debugging.md for debug notes",
        )
        fs.create_file(memory_dir / "debugging.md", contents="# Debug")
        fs.create_file(memory_dir / "extra.md", contents="# Extra")

        result = service._discover_auto_memory()

        refs = result[0].metadata["refs"]
        ref_names = [r.name for r in refs]
        assert ref_names.count("debugging.md") == 1
        assert "extra.md" in ref_names
