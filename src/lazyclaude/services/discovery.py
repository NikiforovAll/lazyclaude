"""Service for discovering Claude Code customizations."""

import json
from abc import ABC, abstractmethod
from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    PluginInfo,
)
from lazyclaude.services.filesystem_scanner import (
    FilesystemScanner,
    GlobStrategy,
    ScanConfig,
)
from lazyclaude.services.parsers.hook import HookParser
from lazyclaude.services.parsers.lsp_server import LSPServerParser
from lazyclaude.services.parsers.mcp import MCPParser
from lazyclaude.services.parsers.memory_file import MemoryFileParser
from lazyclaude.services.parsers.skill import SkillParser
from lazyclaude.services.parsers.slash_command import SlashCommandParser
from lazyclaude.services.parsers.subagent import SubagentParser
from lazyclaude.services.plugin_loader import PluginLoader

SCAN_CONFIGS = {
    "slash_commands": ScanConfig(
        subdir="commands",
        pattern="*.md",
        strategy=GlobStrategy.RGLOB,
        parser_factory=SlashCommandParser,
    ),
    "subagents": ScanConfig(
        subdir="agents",
        pattern="*.md",
        strategy=GlobStrategy.GLOB,
        parser_factory=SubagentParser,
    ),
    "skills": ScanConfig(
        subdir="skills",
        pattern="SKILL.md",
        strategy=GlobStrategy.SUBDIR,
        parser_factory=SkillParser,
    ),
}


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

    @abstractmethod
    def discover_from_directory(
        self, plugin_dir: Path, plugin_info: PluginInfo | None = None
    ) -> list[Customization]:
        """
        Discover customizations from a specific directory (for plugin preview).

        Args:
            plugin_dir: The directory to scan for customizations.
            plugin_info: Optional plugin info to attach to customizations.

        Returns:
            List of customizations found in the directory.
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
        self.project_config_path = (
            project_config_path.resolve()
            if project_config_path
            else Path.cwd() / ".claude"
        )
        self.project_root = self.project_config_path.parent

        self._scanner = FilesystemScanner()
        self._plugin_loader = PluginLoader(
            self.user_config_path,
            project_config_path=self.project_config_path,
            project_root=self.project_root,
        )
        self._cache: list[Customization] | None = None

    def discover_all(self) -> list[Customization]:
        """Discover all customizations from all configuration levels."""
        if self._cache is not None:
            return self._cache

        customizations: list[Customization] = []

        for config in SCAN_CONFIGS.values():
            customizations.extend(
                self._scanner.scan_directory(
                    self.user_config_path, config, ConfigLevel.USER
                )
            )
            customizations.extend(
                self._scanner.scan_directory(
                    self.project_config_path, config, ConfigLevel.PROJECT
                )
            )

        customizations.extend(self._discover_memory_files())
        customizations.extend(self._discover_rules())
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
        self._plugin_loader.refresh()
        return self.discover_all()

    def get_active_config_path(self) -> Path:
        """Get the active configuration path (project if exists, else user)."""
        if self.project_config_path.is_dir():
            return self.project_config_path
        return self.user_config_path

    def discover_from_directory(
        self, plugin_dir: Path, plugin_info: PluginInfo | None = None
    ) -> list[Customization]:
        """Discover customizations from a specific directory (for plugin preview)."""
        customizations: list[Customization] = []
        level = ConfigLevel.PLUGIN

        for config in SCAN_CONFIGS.values():
            customizations.extend(
                self._scanner.scan_directory(plugin_dir, config, level, plugin_info)
            )

        if plugin_info:
            customizations.extend(self._discover_plugin_mcps(plugin_dir, plugin_info))
            customizations.extend(self._discover_plugin_hooks(plugin_dir, plugin_info))
            customizations.extend(
                self._discover_plugin_lsp_servers(plugin_dir, plugin_info)
            )

        return self._sort_customizations(customizations)

    def _sort_customizations(
        self, customizations: list[Customization]
    ) -> list[Customization]:
        """Sort customizations by type order then name."""
        type_order = {t: i for i, t in enumerate(CustomizationType)}
        return sorted(
            customizations,
            key=lambda c: (type_order[c.type], c.name.lower()),
        )

    def _discover_memory_files(self) -> list[Customization]:
        """Discover memory files from user and project levels."""
        customizations: list[Customization] = []
        parser = MemoryFileParser()
        seen_paths: set[Path] = set()

        user_memory_files = [
            self.user_config_path / "CLAUDE.md",
            self.user_config_path / "AGENTS.md",
        ]
        for memory_file in user_memory_files:
            if memory_file.is_file():
                resolved = memory_file.resolve()
                seen_paths.add(resolved)
                customizations.append(parser.parse(memory_file, ConfigLevel.USER))

        user_local_file = self.user_config_path / "CLAUDE.local.md"
        if user_local_file.is_file():
            resolved = user_local_file.resolve()
            seen_paths.add(resolved)
            customizations.append(parser.parse(user_local_file, ConfigLevel.USER))

        project_memory_files = [
            self.project_config_path / "CLAUDE.md",
            self.project_config_path / "AGENTS.md",
            self.project_root / "CLAUDE.md",
            self.project_root / "AGENTS.md",
        ]

        for memory_file in project_memory_files:
            resolved = memory_file.resolve()
            if memory_file.is_file() and resolved not in seen_paths:
                seen_paths.add(resolved)
                customizations.append(parser.parse(memory_file, ConfigLevel.PROJECT))

        for claude_md in self.project_root.rglob("CLAUDE.md"):
            resolved = claude_md.resolve()
            if resolved not in seen_paths:
                seen_paths.add(resolved)
                customization = parser.parse(claude_md, ConfigLevel.PROJECT)
                try:
                    rel_path = claude_md.relative_to(self.project_root)
                    customization.name = str(rel_path)
                except ValueError:
                    pass
                customizations.append(customization)

        project_local_files = [
            self.project_root / "CLAUDE.local.md",
            self.project_config_path / "CLAUDE.local.md",
        ]
        for local_file in project_local_files:
            resolved = local_file.resolve()
            if local_file.is_file() and resolved not in seen_paths:
                seen_paths.add(resolved)
                customizations.append(
                    parser.parse(local_file, ConfigLevel.PROJECT_LOCAL)
                )

        return customizations

    def _discover_rules(self) -> list[Customization]:
        """Discover rules from user and project levels."""
        customizations: list[Customization] = []
        parser = MemoryFileParser()
        seen_paths: set[Path] = set()

        user_rules_dir = self.user_config_path / "rules"
        if user_rules_dir.is_dir():
            for rule_file in user_rules_dir.rglob("*.md"):
                if not rule_file.is_file():
                    continue
                resolved = rule_file.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)

                customization = parser.parse(rule_file, ConfigLevel.USER)
                customization.name = str(rule_file.relative_to(user_rules_dir))
                customizations.append(customization)

        project_rules_dir = self.project_config_path / "rules"
        if project_rules_dir.is_dir():
            for rule_file in project_rules_dir.rglob("*.md"):
                if not rule_file.is_file():
                    continue
                resolved = rule_file.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)

                customization = parser.parse(rule_file, ConfigLevel.PROJECT)
                customization.name = str(rule_file.relative_to(project_rules_dir))
                customizations.append(customization)

        return customizations

    def _discover_mcps(self) -> list[Customization]:
        """Discover MCP configurations from user, local, and project levels."""
        customizations: list[Customization] = []
        parser = MCPParser()

        user_mcp_file = Path.home() / ".claude.json"
        if user_mcp_file.is_file():
            customizations.extend(parser.parse(user_mcp_file, ConfigLevel.USER))

        customizations.extend(self._discover_local_mcps())

        project_mcp_file = self.project_root / ".mcp.json"
        if project_mcp_file.is_file():
            customizations.extend(parser.parse(project_mcp_file, ConfigLevel.PROJECT))

        return customizations

    def _discover_local_mcps(self) -> list[Customization]:
        """Discover local-scoped MCPs from ~/.claude.json projects."""
        customizations: list[Customization] = []
        claude_json = Path.home() / ".claude.json"

        if not claude_json.is_file():
            return customizations

        try:
            data = json.loads(claude_json.read_text(encoding="utf-8"))
            projects = data.get("projects", {})

            project_path = str(self.project_root).replace("\\", "/")

            mcp_servers = None
            for key in [project_path, project_path.replace("/", "\\")]:
                if key in projects:
                    mcp_servers = projects[key].get("mcpServers", {})
                    break

            if not mcp_servers:
                return customizations

            parser = MCPParser()
            for server_name, server_config in mcp_servers.items():
                customization = parser.parse_server_config(
                    server_name, server_config, claude_json, ConfigLevel.PROJECT_LOCAL
                )
                customizations.append(customization)
        except (OSError, json.JSONDecodeError):
            pass

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
        """Discover customizations from ALL installed plugins (enabled and disabled)."""
        customizations: list[Customization] = []

        for plugin_info in self._plugin_loader.get_all_plugins():
            install_path = plugin_info.install_path

            for config in SCAN_CONFIGS.values():
                customizations.extend(
                    self._scanner.scan_directory(
                        install_path, config, ConfigLevel.PLUGIN, plugin_info
                    )
                )

            customizations.extend(self._discover_plugin_mcps(install_path, plugin_info))
            customizations.extend(
                self._discover_plugin_hooks(install_path, plugin_info)
            )
            customizations.extend(
                self._discover_plugin_lsp_servers(install_path, plugin_info)
            )

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
        for customization in parser.parse(mcp_file, ConfigLevel.PLUGIN):
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
        for customization in parser.parse(hooks_file, ConfigLevel.PLUGIN):
            customization.plugin_info = plugin_info
            customizations.append(customization)

        return customizations

    def _discover_plugin_lsp_servers(
        self, install_path: Path, plugin_info: PluginInfo
    ) -> list[Customization]:
        """Discover LSP server configurations from a plugin."""
        customizations: list[Customization] = []
        parser = LSPServerParser()

        lsp_file = install_path / ".lsp.json"
        if lsp_file.is_file():
            for customization in parser.parse(lsp_file, ConfigLevel.PLUGIN):
                customization.plugin_info = plugin_info
                customizations.append(customization)

        plugin_json = install_path / ".claude-plugin" / "plugin.json"
        if plugin_json.is_file():
            try:
                data = json.loads(plugin_json.read_text(encoding="utf-8"))
                lsp_servers = data.get("lspServers", {})
                if lsp_servers and isinstance(lsp_servers, dict):
                    for lang_name, server_config in lsp_servers.items():
                        if isinstance(server_config, dict):
                            customization = parser.parse_server_config(
                                lang_name,
                                server_config,
                                plugin_json,
                                ConfigLevel.PLUGIN,
                            )
                            customization.plugin_info = plugin_info
                            customizations.append(customization)
            except (OSError, json.JSONDecodeError):
                pass

        return customizations
