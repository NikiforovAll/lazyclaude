"""Tests for skill discovery."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, CustomizationType, SkillFile
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestSkillDiscovery:
    """Tests for skill discovery."""

    def test_discovers_user_skills(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)

        user_skills = [s for s in skills if s.level == ConfigLevel.USER]
        assert len(user_skills) == 2
        skill_names = [s.name for s in user_skills]
        assert "task-tracker" in skill_names
        assert "full-skill" in skill_names

    def test_skill_metadata_parsed(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)

        tracker = next(s for s in skills if s.name == "task-tracker")
        assert tracker.description == "Track and manage development tasks"

    def test_discovers_project_skills(
        self, user_config_path: Path, project_config_path: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=project_config_path,
        )

        skills = service.discover_by_type(CustomizationType.SKILL)

        project_skills = [s for s in skills if s.level == ConfigLevel.PROJECT]
        assert len(project_skills) == 1
        assert project_skills[0].name == "project-skill"
        assert project_skills[0].description == "A project-specific skill"


class TestSkillFileDiscovery:
    """Tests for skill file tree discovery."""

    def test_skill_metadata_contains_files(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        """Verify that discovered skills have files populated in metadata."""
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)
        full_skill = next(s for s in skills if s.name == "full-skill")

        files = full_skill.metadata.get("files", [])
        assert len(files) > 0

    def test_skill_files_have_content(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        """Verify that file content is populated for text files."""
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)
        full_skill = next(s for s in skills if s.name == "full-skill")

        files: list[SkillFile] = full_skill.metadata.get("files", [])
        reference_file = next((f for f in files if f.name == "reference.md"), None)
        assert reference_file is not None
        assert reference_file.content is not None
        assert "API documentation" in reference_file.content

    def test_skill_nested_directories_discovered(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        """Verify nested directories are discovered with children."""
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)
        full_skill = next(s for s in skills if s.name == "full-skill")

        files: list[SkillFile] = full_skill.metadata.get("files", [])
        scripts_dir = next((f for f in files if f.name == "scripts"), None)
        assert scripts_dir is not None
        assert scripts_dir.is_directory
        assert len(scripts_dir.children) == 2
        child_names = [c.name for c in scripts_dir.children]
        assert "setup.sh" in child_names
        assert "run.py" in child_names

    def test_skill_has_reference_flag(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        """Verify has_reference flag is set when reference.md exists."""
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)
        full_skill = next(s for s in skills if s.name == "full-skill")

        assert full_skill.metadata.get("has_reference") is True

    def test_skill_has_scripts_flag(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        """Verify has_scripts flag is set when scripts/ directory exists."""
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)
        full_skill = next(s for s in skills if s.name == "full-skill")

        assert full_skill.metadata.get("has_scripts") is True

    def test_skill_tags_parsed(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        """Verify tags are parsed from frontmatter."""
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)
        full_skill = next(s for s in skills if s.name == "full-skill")

        tags = full_skill.metadata.get("tags", [])
        assert "testing" in tags
        assert "fixtures" in tags
