"""Service for writing and deleting customizations on disk."""

import json
import shutil
from pathlib import Path
from typing import Any

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    PluginInfo,
    PluginScope,
)


class CustomizationWriter:
    """Writes and deletes customizations on disk (inverse of parsers)."""

    def write_customization(
        self,
        customization: Customization,
        target_level: ConfigLevel,
        user_config_path: Path,
        project_config_path: Path,
    ) -> tuple[bool, str]:
        """
        Copy customization to target level.

        Args:
            customization: The customization to copy
            target_level: Target configuration level (USER or PROJECT)
            user_config_path: Path to user config directory (~/.claude)
            project_config_path: Path to project config directory (./.claude)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            base_path = self._get_target_base_path(
                target_level, user_config_path, project_config_path
            )
            target_path = self._build_target_path(customization, base_path)

            if self._check_conflict(customization, target_path):
                return (
                    False,
                    f"{customization.type_label} '{customization.name}' already exists at {target_level.label} level",
                )

            self._ensure_parent_dirs(target_path)

            if customization.type == CustomizationType.SKILL:
                self._copy_skill_directory(customization.path.parent, target_path)
            else:
                self._write_file(customization.path, target_path)

            return (
                True,
                f"Copied '{customization.name}' to {target_level.label} level",
            )

        except PermissionError as e:
            return (False, f"Permission denied writing to {e.filename}")
        except OSError as e:
            return (False, f"Failed to copy '{customization.name}': {e}")

    def delete_customization(
        self,
        customization: Customization,
    ) -> tuple[bool, str]:
        """
        Delete customization from disk.

        Args:
            customization: The customization to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if customization.type == CustomizationType.SKILL:
                self._delete_skill_directory(customization.path.parent)
            else:
                self._delete_file(customization.path)

            return (True, f"Deleted '{customization.name}'")

        except PermissionError as e:
            return (False, f"Permission denied deleting {e.filename}")
        except OSError as e:
            return (False, f"Failed to delete '{customization.name}': {e}")

    def write_hook_customization(
        self,
        customization: Customization,
        target_level: ConfigLevel,
        user_config_path: Path,
        project_config_path: Path,
    ) -> tuple[bool, str]:
        """
        Copy hooks to target level, merging with existing hooks.

        Args:
            customization: The hook customization to copy
            target_level: Target configuration level (USER, PROJECT, or PROJECT_LOCAL)
            user_config_path: Path to user config directory (~/.claude)
            project_config_path: Path to project config directory (./.claude)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            target_path = self._get_hook_settings_path(
                target_level, user_config_path, project_config_path
            )
            if target_path is None:
                return (False, "No project config path available")

            source_hooks = self._parse_hook_content(customization.content)
            if not source_hooks:
                return (False, "No hooks to copy")

            settings = self._read_settings_json(target_path)
            existing_hooks: dict[str, list[Any]] = settings.get("hooks", {})

            merged_hooks = self._merge_hooks(existing_hooks, source_hooks)
            settings["hooks"] = merged_hooks

            self._write_settings_json(target_path, settings)

            return (
                True,
                f"Copied hooks to {target_level.label} level",
            )

        except PermissionError as e:
            return (False, f"Permission denied writing to {e.filename}")
        except OSError as e:
            return (False, f"Failed to copy hooks: {e}")

    def delete_hook_customization(
        self,
        customization: Customization,
    ) -> tuple[bool, str]:
        """
        Delete hooks from a settings file (for move operation).

        Removes only the "hooks" key, preserving other settings like enabledPlugins.

        Args:
            customization: The hook customization to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            settings_path = customization.path

            settings = self._read_settings_json(settings_path)
            if "hooks" not in settings:
                return (False, "No hooks found to delete")

            del settings["hooks"]

            if settings:
                self._write_settings_json(settings_path, settings)
            else:
                settings_path.unlink()

            return (True, "Deleted hooks")

        except PermissionError as e:
            return (False, f"Permission denied deleting {e.filename}")
        except OSError as e:
            return (False, f"Failed to delete hooks: {e}")

    def write_mcp_customization(
        self,
        customization: Customization,
        target_level: ConfigLevel,
        project_config_path: Path,
    ) -> tuple[bool, str]:
        """
        Copy MCP server to target level.

        Args:
            customization: The MCP customization to copy
            target_level: Target configuration level (USER, PROJECT, or PROJECT_LOCAL)
            project_config_path: Path to project config directory (./.claude)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            target_path = self._get_mcp_file_path(target_level, project_config_path)

            mcp_config = self._parse_mcp_content(customization.content)
            if not mcp_config:
                return (False, "Invalid MCP configuration")

            data = self._read_settings_json(target_path)

            if target_level == ConfigLevel.PROJECT_LOCAL:
                project_path = str(project_config_path.parent).replace("\\", "/")
                projects: dict[str, Any] = data.setdefault("projects", {})
                project_data: dict[str, Any] = projects.setdefault(project_path, {})
                mcp_servers: dict[str, Any] = project_data.setdefault("mcpServers", {})
            else:
                mcp_servers = data.setdefault("mcpServers", {})

            if customization.name in mcp_servers:
                return (
                    False,
                    f"MCP '{customization.name}' already exists at {target_level.label} level",
                )

            mcp_servers[customization.name] = mcp_config
            self._write_settings_json(target_path, data)

            return (
                True,
                f"Copied MCP '{customization.name}' to {target_level.label} level",
            )

        except PermissionError as e:
            return (False, f"Permission denied writing to {e.filename}")
        except OSError as e:
            return (False, f"Failed to copy MCP: {e}")

    def delete_mcp_customization(
        self,
        customization: Customization,
        project_config_path: Path,
    ) -> tuple[bool, str]:
        """
        Delete MCP server from its source file (for move operation).

        Removes only the specific MCP server, preserving other servers and settings.

        Args:
            customization: The MCP customization to delete
            project_config_path: Path to project config directory (./.claude)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            source_path = customization.path
            source_level = customization.level

            data = self._read_settings_json(source_path)

            if source_level == ConfigLevel.PROJECT_LOCAL:
                project_path = str(project_config_path.parent).replace("\\", "/")
                projects = data.get("projects", {})
                project_data = projects.get(project_path) or projects.get(
                    project_path.replace("/", "\\"), {}
                )
                mcp_servers = project_data.get("mcpServers", {})

                if customization.name not in mcp_servers:
                    return (False, f"MCP '{customization.name}' not found")

                del mcp_servers[customization.name]
                if not mcp_servers and "mcpServers" in project_data:
                    del project_data["mcpServers"]
            else:
                mcp_servers = data.get("mcpServers", {})

                if customization.name not in mcp_servers:
                    return (False, f"MCP '{customization.name}' not found")

                del mcp_servers[customization.name]
                if not mcp_servers and "mcpServers" in data:
                    del data["mcpServers"]

            if source_level == ConfigLevel.PROJECT and not data:
                source_path.unlink()
            else:
                self._write_settings_json(source_path, data)

            return (True, f"Deleted MCP '{customization.name}'")

        except PermissionError as e:
            return (False, f"Permission denied deleting {e.filename}")
        except OSError as e:
            return (False, f"Failed to delete MCP: {e}")

    def _get_mcp_file_path(
        self,
        level: ConfigLevel,
        project_config_path: Path,
    ) -> Path:
        """Get MCP config file path for target level."""
        if level == ConfigLevel.USER:
            return Path.home() / ".claude.json"
        elif level == ConfigLevel.PROJECT:
            return project_config_path.parent / ".mcp.json"
        elif level == ConfigLevel.PROJECT_LOCAL:
            return Path.home() / ".claude.json"
        raise ValueError(f"Unsupported level for MCP: {level}")

    def _parse_mcp_content(self, content: str | None) -> dict[str, Any]:
        """Parse MCP content JSON string to dict."""
        if not content:
            return {}
        try:
            result: dict[str, Any] = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {}

    def _get_hook_settings_path(
        self,
        level: ConfigLevel,
        user_config_path: Path,
        project_config_path: Path | None,
    ) -> Path | None:
        """Get the settings file path for hooks at the given level."""
        if level == ConfigLevel.USER:
            return user_config_path / "settings.json"
        elif level == ConfigLevel.PROJECT:
            if project_config_path is None:
                return None
            return project_config_path / "settings.json"
        elif level == ConfigLevel.PROJECT_LOCAL:
            if project_config_path is None:
                return None
            return project_config_path / "settings.local.json"
        return None

    def _parse_hook_content(self, content: str | None) -> dict[str, list[Any]]:
        """Parse hook content JSON string to dict."""
        if not content:
            return {}
        try:
            result: dict[str, list[Any]] = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {}

    def _merge_hooks(
        self,
        existing: dict[str, list[Any]],
        source: dict[str, list[Any]],
    ) -> dict[str, list[Any]]:
        """
        Merge source hooks into existing hooks.

        For each event type, appends source matchers to existing matchers.
        """
        merged = dict(existing)
        for event_name, source_matchers in source.items():
            if event_name in merged:
                merged[event_name] = merged[event_name] + source_matchers
            else:
                merged[event_name] = source_matchers
        return merged

    def _get_target_base_path(
        self,
        level: ConfigLevel,
        user_config_path: Path,
        project_config_path: Path,
    ) -> Path:
        """Get base path for target configuration level."""
        if level == ConfigLevel.USER:
            return user_config_path
        elif level == ConfigLevel.PROJECT:
            return project_config_path
        else:
            raise ValueError(f"Unsupported target level: {level}")

    def _build_target_path(self, customization: Customization, base_path: Path) -> Path:
        """
        Construct target file path based on customization type.

        For slash commands: Preserve nested structure (nested:cmd → commands/nested/cmd.md)
        For subagents: Flat structure (agent → agents/agent.md)
        For skills: Directory path (skill → skills/skill/)
        """
        if customization.type == CustomizationType.SLASH_COMMAND:
            parts = customization.name.split(":")
            if len(parts) > 1:
                nested_path = Path(*parts[:-1])
                filename = f"{parts[-1]}.md"
                return base_path / "commands" / nested_path / filename
            else:
                return base_path / "commands" / f"{customization.name}.md"

        elif customization.type == CustomizationType.SUBAGENT:
            return base_path / "agents" / f"{customization.name}.md"

        elif customization.type == CustomizationType.SKILL:
            return base_path / "skills" / customization.name

        elif customization.type == CustomizationType.MEMORY_FILE:
            return base_path / customization.path.name

        else:
            raise ValueError(f"Unsupported customization type: {customization.type}")

    def _check_conflict(self, customization: Customization, target_path: Path) -> bool:
        """Check if target file or directory already exists."""
        if customization.type == CustomizationType.SKILL:
            return target_path.exists() and target_path.is_dir()
        else:
            return target_path.exists() and target_path.is_file()

    def _ensure_parent_dirs(self, target_path: Path) -> None:
        """Create parent directories if they don't exist."""
        target_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_file(self, source_path: Path, target_path: Path) -> None:
        """Copy file from source to target."""
        content = source_path.read_text(encoding="utf-8")
        target_path.write_text(content, encoding="utf-8")

    def _copy_skill_directory(self, source_dir: Path, target_dir: Path) -> None:
        """
        Copy entire skill directory tree.

        Args:
            source_dir: Path to source skill directory (parent of SKILL.md)
            target_dir: Path to target skill directory location
        """
        shutil.copytree(
            source_dir,
            target_dir,
            dirs_exist_ok=False,
        )

    def _delete_file(self, file_path: Path) -> None:
        """Delete a file from disk."""
        file_path.unlink()

    def _delete_skill_directory(self, skill_dir: Path) -> None:
        """Recursively delete skill directory."""
        shutil.rmtree(skill_dir)

    def toggle_plugin_enabled(
        self,
        plugin_info: PluginInfo,
        user_config_path: Path,
        project_config_path: Path | None,
    ) -> tuple[bool, str]:
        """
        Toggle plugin enabled state in the appropriate settings file.

        Args:
            plugin_info: Plugin to toggle
            user_config_path: Path to ~/.claude
            project_config_path: Path to ./.claude (may be None)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            settings_path = self._get_settings_path(
                plugin_info.scope, user_config_path, project_config_path
            )
            if settings_path is None:
                return (
                    False,
                    "No project config path available for project-scoped plugin",
                )

            settings = self._read_settings_json(settings_path)

            enabled_plugins = settings.setdefault("enabledPlugins", {})
            current_state = enabled_plugins.get(plugin_info.plugin_id, True)
            new_state = not current_state
            enabled_plugins[plugin_info.plugin_id] = new_state

            self._write_settings_json(settings_path, settings)

            state_label = "enabled" if new_state else "disabled"
            return (True, f"Plugin '{plugin_info.short_name}' {state_label}")

        except PermissionError as e:
            return (False, f"Permission denied writing to {e.filename}")
        except OSError as e:
            return (False, f"Failed to toggle plugin: {e}")

    def _get_settings_path(
        self,
        scope: PluginScope,
        user_config_path: Path,
        project_config_path: Path | None,
    ) -> Path | None:
        """Get the settings file path for the given plugin scope."""
        if scope == PluginScope.USER:
            return user_config_path / "settings.json"
        elif scope == PluginScope.PROJECT:
            if project_config_path is None:
                return None
            return project_config_path / "settings.json"
        elif scope == PluginScope.PROJECT_LOCAL:
            if project_config_path is None:
                return None
            return project_config_path / "settings.local.json"
        return None

    def _read_settings_json(self, path: Path) -> dict[str, Any]:
        """Read settings JSON, returning empty dict if file doesn't exist."""
        if not path.is_file():
            return {}
        try:
            result: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return result
        except json.JSONDecodeError:
            return {}

    def _write_settings_json(self, path: Path, data: dict[str, Any]) -> None:
        """Write settings JSON with proper formatting."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
