"""Service for discovering Claude Code customizations."""

from abc import ABC, abstractmethod
from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.parsers.mcp import MCPParser
from lazyclaude.services.parsers.memory_file import MemoryFileParser
from lazyclaude.services.parsers.skill import SkillParser
from lazyclaude.services.parsers.slash_command import SlashCommandParser
from lazyclaude.services.parsers.subagent import SubagentParser


class IConfigDiscoveryService(ABC):
    """Service for discovering Claude Code customizations."""

    @abstractmethod
    def discover_all(self) -> list[Customization]:
        """
        Discover all customizations from all configuration levels.

        Returns:
            List of all discovered customizations, ordered by type then name.
        """
        ...

    @abstractmethod
    def discover_by_level(self, level: ConfigLevel) -> list[Customization]:
        """
        Discover customizations from a specific configuration level.

        Args:
            level: The configuration level to scan.

        Returns:
            List of customizations from the specified level.
        """
        ...

    @abstractmethod
    def discover_by_type(self, ctype: CustomizationType) -> list[Customization]:
        """
        Discover customizations of a specific type from all levels.

        Args:
            ctype: The type of customization to find.

        Returns:
            List of customizations of the specified type.
        """
        ...

    @abstractmethod
    def refresh(self) -> list[Customization]:
        """
        Re-scan all configuration directories and return fresh results.

        Returns:
            Updated list of all customizations.
        """
        ...


class ConfigDiscoveryService(IConfigDiscoveryService):
    """Discovers and loads all Claude Code customizations from the filesystem."""

    def __init__(
        self,
        user_config_path: Path | None = None,
        project_config_path: Path | None = None,
    ) -> None:
        """
        Initialize the discovery service.

        Args:
            user_config_path: Override for ~/.claude (testing)
            project_config_path: Override for ./.claude (testing)
        """
        self.user_config_path = user_config_path or Path.home() / ".claude"
        self.project_config_path = project_config_path or Path.cwd() / ".claude"
        self.project_root = project_config_path.parent if project_config_path else Path.cwd()

        self._cache: list[Customization] | None = None

    def discover_all(self) -> list[Customization]:
        """Discover all customizations from all configuration levels."""
        if self._cache is not None:
            return self._cache

        customizations: list[Customization] = []

        customizations.extend(self._discover_slash_commands())
        customizations.extend(self._discover_subagents())
        customizations.extend(self._discover_skills())
        customizations.extend(self._discover_memory_files())
        customizations.extend(self._discover_mcps())

        customizations = self._sort_customizations(customizations)
        self._cache = customizations
        return customizations

    def discover_by_level(self, level: ConfigLevel) -> list[Customization]:
        """Discover customizations from a specific configuration level."""
        return [c for c in self.discover_all() if c.level == level]

    def discover_by_type(self, ctype: CustomizationType) -> list[Customization]:
        """Discover customizations of a specific type from all levels."""
        return [c for c in self.discover_all() if c.type == ctype]

    def refresh(self) -> list[Customization]:
        """Re-scan all configuration directories and return fresh results."""
        self._cache = None
        return self.discover_all()

    def get_active_config_path(self) -> Path:
        """Get the active configuration path (project if exists, else user)."""
        if self.project_config_path.is_dir():
            return self.project_config_path
        return self.user_config_path

    def _sort_customizations(
        self, customizations: list[Customization]
    ) -> list[Customization]:
        """Sort customizations by type order then name."""
        type_order = {t: i for i, t in enumerate(CustomizationType)}
        return sorted(
            customizations,
            key=lambda c: (type_order[c.type], c.name.lower()),
        )

    def _discover_slash_commands(self) -> list[Customization]:
        """Discover slash commands from user and project levels."""
        customizations: list[Customization] = []

        user_commands_dir = self.user_config_path / "commands"
        if user_commands_dir.is_dir():
            parser = SlashCommandParser(user_commands_dir)
            for md_file in user_commands_dir.rglob("*.md"):
                customizations.append(parser.parse(md_file, ConfigLevel.USER))

        project_commands_dir = self.project_config_path / "commands"
        if project_commands_dir.is_dir():
            parser = SlashCommandParser(project_commands_dir)
            for md_file in project_commands_dir.rglob("*.md"):
                customizations.append(parser.parse(md_file, ConfigLevel.PROJECT))

        return customizations

    def _discover_subagents(self) -> list[Customization]:
        """Discover subagents from user and project levels."""
        customizations: list[Customization] = []

        user_agents_dir = self.user_config_path / "agents"
        if user_agents_dir.is_dir():
            parser = SubagentParser(user_agents_dir)
            for md_file in user_agents_dir.glob("*.md"):
                customizations.append(parser.parse(md_file, ConfigLevel.USER))

        project_agents_dir = self.project_config_path / "agents"
        if project_agents_dir.is_dir():
            parser = SubagentParser(project_agents_dir)
            for md_file in project_agents_dir.glob("*.md"):
                customizations.append(parser.parse(md_file, ConfigLevel.PROJECT))

        return customizations

    def _discover_skills(self) -> list[Customization]:
        """Discover skills from user and project levels."""
        customizations: list[Customization] = []

        user_skills_dir = self.user_config_path / "skills"
        if user_skills_dir.is_dir():
            parser = SkillParser(user_skills_dir)
            for skill_dir in user_skills_dir.iterdir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.is_file():
                    customizations.append(parser.parse(skill_md, ConfigLevel.USER))

        project_skills_dir = self.project_config_path / "skills"
        if project_skills_dir.is_dir():
            parser = SkillParser(project_skills_dir)
            for skill_dir in project_skills_dir.iterdir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.is_file():
                    customizations.append(parser.parse(skill_md, ConfigLevel.PROJECT))

        return customizations

    def _discover_memory_files(self) -> list[Customization]:
        """Discover memory files from user and project levels."""
        customizations: list[Customization] = []
        parser = MemoryFileParser()

        user_memory_files = [
            self.user_config_path / "CLAUDE.md",
            self.user_config_path / "AGENTS.md",
        ]
        for memory_file in user_memory_files:
            if memory_file.is_file():
                customizations.append(parser.parse(memory_file, ConfigLevel.USER))

        project_memory_files = [
            self.project_config_path / "CLAUDE.md",
            self.project_config_path / "AGENTS.md",
            self.project_root / "CLAUDE.md",
            self.project_root / "AGENTS.md",
            self.project_root / "CLAUDE.local.md",
        ]

        seen_paths: set[Path] = set()
        for memory_file in project_memory_files:
            resolved = memory_file.resolve()
            if memory_file.is_file() and resolved not in seen_paths:
                seen_paths.add(resolved)
                customizations.append(parser.parse(memory_file, ConfigLevel.PROJECT))

        return customizations

    def _discover_mcps(self) -> list[Customization]:
        """Discover MCP configurations from user and project levels."""
        customizations: list[Customization] = []
        parser = MCPParser()

        user_mcp_file = Path.home() / ".claude.json"
        if user_mcp_file.is_file():
            customizations.extend(parser.parse(user_mcp_file, ConfigLevel.USER))

        project_mcp_file = self.project_root / ".mcp.json"
        if project_mcp_file.is_file():
            customizations.extend(parser.parse(project_mcp_file, ConfigLevel.PROJECT))

        return customizations
