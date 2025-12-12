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
