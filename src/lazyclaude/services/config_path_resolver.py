"""Service for resolving config paths for customizations."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, Customization
from lazyclaude.services.plugin_loader import PluginLoader


class ConfigPathResolver:
    """Resolves config paths for customizations, handling plugin source translation."""

    def __init__(self, plugin_loader: PluginLoader) -> None:
        self._plugin_loader = plugin_loader

    def resolve_file(self, customization: Customization) -> Path | None:
        """Resolve the file path for a customization.

        For non-PLUGIN levels: returns path as-is.
        For PLUGIN level with directory source: translates install path to source path.
        For PLUGIN level without directory source: returns path as-is.

        Args:
            customization: The customization to resolve path for.

        Returns:
            Resolved absolute path, or None if customization.path is None.
        """
        return self.resolve_path(customization, customization.path)

    def resolve_path(
        self, customization: Customization, file_path: Path | None
    ) -> Path | None:
        """Resolve any file path within a customization's context.

        For non-PLUGIN levels: returns file_path as-is.
        For PLUGIN level with directory source: translates install path to source path.
        For PLUGIN level without directory source: returns file_path as-is.

        Args:
            customization: The customization providing context (plugin info).
            file_path: The file path to resolve (can be any file within the plugin).

        Returns:
            Resolved absolute path, or None if file_path is None.
        """
        if file_path is None:
            return None

        if customization.level != ConfigLevel.PLUGIN:
            return file_path

        if not customization.plugin_info:
            return file_path

        source_root = self._plugin_loader.get_plugin_source_path(
            customization.plugin_info.plugin_id
        )

        if not source_root:
            return file_path

        install_path = customization.plugin_info.install_path

        if source_root == install_path:
            return file_path

        try:
            relative_path = file_path.relative_to(install_path)
            return source_root / relative_path
        except ValueError:
            return file_path
