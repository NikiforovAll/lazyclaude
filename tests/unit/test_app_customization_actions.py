"""Tests for app-level customization action constants and helpers."""

import pytest

from lazyclaude.app import LazyClaude
from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)


class TestCopyableTypesConstant:
    """Tests for _COPYABLE_TYPES class constant."""

    def test_includes_slash_command(self) -> None:
        """Slash commands are copyable."""
        assert CustomizationType.SLASH_COMMAND in LazyClaude._COPYABLE_TYPES

    def test_includes_subagent(self) -> None:
        """Subagents are copyable."""
        assert CustomizationType.SUBAGENT in LazyClaude._COPYABLE_TYPES

    def test_includes_skill(self) -> None:
        """Skills are copyable."""
        assert CustomizationType.SKILL in LazyClaude._COPYABLE_TYPES

    def test_includes_hook(self) -> None:
        """Hooks are copyable."""
        assert CustomizationType.HOOK in LazyClaude._COPYABLE_TYPES

    def test_includes_mcp(self) -> None:
        """MCPs are copyable."""
        assert CustomizationType.MCP in LazyClaude._COPYABLE_TYPES

    def test_includes_memory_file(self) -> None:
        """Memory files are copyable."""
        assert CustomizationType.MEMORY_FILE in LazyClaude._COPYABLE_TYPES

    def test_contains_exactly_six_types(self) -> None:
        """Copyable types has exactly 6 entries."""
        assert len(LazyClaude._COPYABLE_TYPES) == 6


class TestProjectLocalTypesConstant:
    """Tests for _PROJECT_LOCAL_TYPES class constant."""

    def test_includes_hook(self) -> None:
        """Hooks support project-local level."""
        assert CustomizationType.HOOK in LazyClaude._PROJECT_LOCAL_TYPES

    def test_includes_mcp(self) -> None:
        """MCPs support project-local level."""
        assert CustomizationType.MCP in LazyClaude._PROJECT_LOCAL_TYPES

    def test_does_not_include_slash_command(self) -> None:
        """Slash commands do not support project-local level."""
        assert CustomizationType.SLASH_COMMAND not in LazyClaude._PROJECT_LOCAL_TYPES

    def test_does_not_include_skill(self) -> None:
        """Skills do not support project-local level."""
        assert CustomizationType.SKILL not in LazyClaude._PROJECT_LOCAL_TYPES

    def test_does_not_include_memory_file(self) -> None:
        """Memory files do not support project-local level."""
        assert CustomizationType.MEMORY_FILE not in LazyClaude._PROJECT_LOCAL_TYPES

    def test_contains_exactly_two_types(self) -> None:
        """Project-local types has exactly 2 entries."""
        assert len(LazyClaude._PROJECT_LOCAL_TYPES) == 2


class TestGetAvailableTargetLevels:
    """Tests for _get_available_target_levels helper method."""

    @pytest.fixture
    def app(self) -> LazyClaude:
        """Create app instance for testing."""
        return LazyClaude()

    def _create_customization(
        self, ctype: CustomizationType, level: ConfigLevel
    ) -> Customization:
        """Create a test customization."""
        return Customization(
            name="test",
            type=ctype,
            level=level,
            path=None,  # type: ignore
        )

    def test_hook_from_user_includes_project_and_project_local(
        self, app: LazyClaude
    ) -> None:
        """Hook at user level can target project and project-local."""
        customization = self._create_customization(
            CustomizationType.HOOK, ConfigLevel.USER
        )
        levels = app._get_available_target_levels(customization)

        assert ConfigLevel.PROJECT in levels
        assert ConfigLevel.PROJECT_LOCAL in levels
        assert ConfigLevel.USER not in levels

    def test_mcp_from_project_includes_user_and_project_local(
        self, app: LazyClaude
    ) -> None:
        """MCP at project level can target user and project-local."""
        customization = self._create_customization(
            CustomizationType.MCP, ConfigLevel.PROJECT
        )
        levels = app._get_available_target_levels(customization)

        assert ConfigLevel.USER in levels
        assert ConfigLevel.PROJECT_LOCAL in levels
        assert ConfigLevel.PROJECT not in levels

    def test_slash_command_from_user_excludes_project_local(
        self, app: LazyClaude
    ) -> None:
        """Slash command at user level cannot target project-local."""
        customization = self._create_customization(
            CustomizationType.SLASH_COMMAND, ConfigLevel.USER
        )
        levels = app._get_available_target_levels(customization)

        assert ConfigLevel.PROJECT in levels
        assert ConfigLevel.USER not in levels
        assert ConfigLevel.PROJECT_LOCAL not in levels

    def test_skill_from_project_excludes_project_local(self, app: LazyClaude) -> None:
        """Skill at project level cannot target project-local."""
        customization = self._create_customization(
            CustomizationType.SKILL, ConfigLevel.PROJECT
        )
        levels = app._get_available_target_levels(customization)

        assert ConfigLevel.USER in levels
        assert ConfigLevel.PROJECT not in levels
        assert ConfigLevel.PROJECT_LOCAL not in levels

    def test_memory_file_from_user_excludes_project_local(
        self, app: LazyClaude
    ) -> None:
        """Memory file at user level cannot target project-local."""
        customization = self._create_customization(
            CustomizationType.MEMORY_FILE, ConfigLevel.USER
        )
        levels = app._get_available_target_levels(customization)

        assert ConfigLevel.PROJECT in levels
        assert ConfigLevel.USER not in levels
        assert ConfigLevel.PROJECT_LOCAL not in levels

    def test_subagent_from_project_excludes_project_local(
        self, app: LazyClaude
    ) -> None:
        """Subagent at project level cannot target project-local."""
        customization = self._create_customization(
            CustomizationType.SUBAGENT, ConfigLevel.PROJECT
        )
        levels = app._get_available_target_levels(customization)

        assert ConfigLevel.USER in levels
        assert ConfigLevel.PROJECT not in levels
        assert ConfigLevel.PROJECT_LOCAL not in levels
