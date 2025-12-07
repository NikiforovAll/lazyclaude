"""Tests for skill discovery."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, CustomizationType
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
        assert len(user_skills) == 1
        assert user_skills[0].name == "task-tracker"

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
