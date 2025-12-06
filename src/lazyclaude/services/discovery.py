"""Service for discovering Claude Code customizations."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    PluginInfo,
)
from lazyclaude.services.parsers.hook import HookParser
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
        self.project_root = (
            project_config_path.parent if project_config_path else Path.cwd()
        )

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
        customizations.extend(self._discover_hooks())
        customizations.extend(self._discover_plugins())

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

    def _discover_hooks(self) -> list[Customization]:
        """Discover hooks from settings files at user and project levels."""
        customizations: list[Customization] = []
        parser = HookParser()

        user_settings = self.user_config_path / "settings.json"
        if user_settings.is_file():
            customizations.extend(parser.parse(user_settings, ConfigLevel.USER))

        project_settings = self.project_config_path / "settings.json"
        if project_settings.is_file():
            customizations.extend(parser.parse(project_settings, ConfigLevel.PROJECT))

        project_local_settings = self.project_config_path / "settings.local.json"
        if project_local_settings.is_file():
            customizations.extend(
                parser.parse(project_local_settings, ConfigLevel.PROJECT_LOCAL)
            )

        return customizations

    def _discover_plugins(self) -> list[Customization]:
        """Discover customizations from installed and enabled plugins."""
        customizations: list[Customization] = []

        installed_plugins = self._load_installed_plugins()
        if not installed_plugins:
            return customizations

        enabled_plugins = self._load_enabled_plugins()

        for plugin_id, plugin_data in installed_plugins.items():
            if not enabled_plugins.get(plugin_id, True):
                continue

            plugin_info = self._create_plugin_info(plugin_id, plugin_data)
            if plugin_info is None:
                continue

            install_path = plugin_info.install_path
            if not install_path.is_dir():
                continue

            customizations.extend(
                self._discover_plugin_slash_commands(install_path, plugin_info)
            )
            customizations.extend(
                self._discover_plugin_subagents(install_path, plugin_info)
            )
            customizations.extend(
                self._discover_plugin_skills(install_path, plugin_info)
            )
            customizations.extend(self._discover_plugin_mcps(install_path, plugin_info))
            customizations.extend(
                self._discover_plugin_hooks(install_path, plugin_info)
            )

        return customizations

    def _load_installed_plugins(self) -> dict[str, Any]:
        """Load installed plugins from ~/.claude/plugins/installed_plugins.json."""
        plugins_file = self.user_config_path / "plugins" / "installed_plugins.json"
        if not plugins_file.is_file():
            return {}

        try:
            data = json.loads(plugins_file.read_text(encoding="utf-8"))
            return data.get("plugins", {})
        except (json.JSONDecodeError, OSError):
            return {}

    def _load_enabled_plugins(self) -> dict[str, bool]:
        """Load enabled plugins from ~/.claude/settings.json."""
        settings_file = self.user_config_path / "settings.json"
        if not settings_file.is_file():
            return {}

        try:
            data = json.loads(settings_file.read_text(encoding="utf-8"))
            return data.get("enabledPlugins", {})
        except (json.JSONDecodeError, OSError):
            return {}

    def _create_plugin_info(
        self, plugin_id: str, plugin_data: dict[str, Any]
    ) -> PluginInfo | None:
        """Create PluginInfo from plugin data."""
        install_path_str = plugin_data.get("installPath")
        if not install_path_str:
            return None

        short_name = plugin_id.split("@")[0] if "@" in plugin_id else plugin_id
        install_path = Path(install_path_str)

        if install_path.parent.is_dir():
            short_name_path = install_path.parent / short_name
            if short_name_path.is_dir() and (
                short_name_path != install_path or not install_path.is_dir()
            ):
                install_path = short_name_path

        return PluginInfo(
            plugin_id=plugin_id,
            short_name=short_name,
            version=plugin_data.get("version", "unknown"),
            install_path=install_path,
            is_local=plugin_data.get("isLocal", False),
        )

    def _discover_plugin_slash_commands(
        self, install_path: Path, plugin_info: PluginInfo
    ) -> list[Customization]:
        """Discover slash commands from a plugin."""
        customizations: list[Customization] = []
        commands_dir = install_path / "commands"

        if not commands_dir.is_dir():
            return customizations

        parser = SlashCommandParser(commands_dir)
        for md_file in commands_dir.rglob("*.md"):
            customization = parser.parse(md_file, ConfigLevel.PLUGIN)
            customization.plugin_info = plugin_info
            customizations.append(customization)

        return customizations

    def _discover_plugin_subagents(
        self, install_path: Path, plugin_info: PluginInfo
    ) -> list[Customization]:
        """Discover subagents from a plugin."""
        customizations: list[Customization] = []
        agents_dir = install_path / "agents"

        if not agents_dir.is_dir():
            return customizations

        parser = SubagentParser(agents_dir)
        for md_file in agents_dir.glob("*.md"):
            customization = parser.parse(md_file, ConfigLevel.PLUGIN)
            customization.plugin_info = plugin_info
            customizations.append(customization)

        return customizations

    def _discover_plugin_skills(
        self, install_path: Path, plugin_info: PluginInfo
    ) -> list[Customization]:
        """Discover skills from a plugin."""
        customizations: list[Customization] = []
        skills_dir = install_path / "skills"

        if not skills_dir.is_dir():
            return customizations

        parser = SkillParser(skills_dir)
        for skill_dir in skills_dir.iterdir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.is_file():
                customization = parser.parse(skill_md, ConfigLevel.PLUGIN)
                customization.plugin_info = plugin_info
                customizations.append(customization)

        return customizations

    def _discover_plugin_mcps(
        self, install_path: Path, plugin_info: PluginInfo
    ) -> list[Customization]:
        """Discover MCP configurations from a plugin."""
        customizations: list[Customization] = []
        mcp_file = install_path / ".mcp.json"

        if not mcp_file.is_file():
            return customizations

        parser = MCPParser()
        mcp_customizations = parser.parse(mcp_file, ConfigLevel.PLUGIN)
        for customization in mcp_customizations:
            customization.plugin_info = plugin_info
            customizations.append(customization)

        return customizations

    def _discover_plugin_hooks(
        self, install_path: Path, plugin_info: PluginInfo
    ) -> list[Customization]:
        """Discover hook configurations from a plugin."""
        customizations: list[Customization] = []
        hooks_file = install_path / "hooks" / "hooks.json"

        if not hooks_file.is_file():
            return customizations

        parser = HookParser()
        hook_customizations = parser.parse(hooks_file, ConfigLevel.PLUGIN)
        for customization in hook_customizations:
            customization.plugin_info = plugin_info
            customizations.append(customization)

        return customizations
