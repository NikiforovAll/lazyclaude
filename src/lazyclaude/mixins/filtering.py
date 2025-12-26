"""Filtering mixin for LazyClaude application."""

from typing import TYPE_CHECKING

from lazyclaude.models.customization import ConfigLevel

if TYPE_CHECKING:
    from lazyclaude.services.discovery import ConfigDiscoveryService
    from lazyclaude.widgets.detail_pane import MainPane
    from lazyclaude.widgets.filter_input import FilterInput
    from lazyclaude.widgets.status_panel import StatusPanel
    from lazyclaude.widgets.type_panel import TypePanel


class FilterMixin:
    """Mixin providing filtering and search functionality."""

    _level_filter: ConfigLevel | None
    _plugin_enabled_filter: bool | None
    _last_focused_panel: "TypePanel | None"
    _main_pane: "MainPane | None"
    _filter_input: "FilterInput | None"
    _status_panel: "StatusPanel | None"
    _discovery_service: "ConfigDiscoveryService"

    def action_filter_all(self) -> None:
        """Show all customizations (clear level filter)."""
        self._level_filter = None
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()  # type: ignore[attr-defined]
        self._update_subtitle()  # type: ignore[attr-defined]
        self._update_status_filter("All")

    def action_filter_user(self) -> None:
        """Show only user-level customizations."""
        self._level_filter = ConfigLevel.USER
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()  # type: ignore[attr-defined]
        self._update_subtitle()  # type: ignore[attr-defined]
        self._update_status_filter("User")

    def action_filter_project(self) -> None:
        """Show only project-level customizations."""
        self._level_filter = ConfigLevel.PROJECT
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()  # type: ignore[attr-defined]
        self._update_subtitle()  # type: ignore[attr-defined]
        self._update_status_filter("Project")

    def action_filter_plugin(self) -> None:
        """Show only plugin-level customizations."""
        self._level_filter = ConfigLevel.PLUGIN
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()  # type: ignore[attr-defined]
        self._update_subtitle()  # type: ignore[attr-defined]
        self._update_status_filter("Plugin")

    def action_toggle_plugin_enabled_filter(self) -> None:
        """Toggle between enabled-only and showing all plugins."""
        if self._plugin_enabled_filter is True:
            self._plugin_enabled_filter = None
        else:
            self._plugin_enabled_filter = True

        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()  # type: ignore[attr-defined]
        self._update_subtitle()  # type: ignore[attr-defined]

    def action_search(self) -> None:
        """Activate search mode."""
        if self._filter_input:
            self._filter_input.show()

    def _update_status_filter(self, level: str) -> None:
        """Update status panel filter level and path display."""
        if self._status_panel:
            self._status_panel.filter_level = level
            if level == "User":
                self._status_panel.config_path = "~/.claude"
            elif level == "Project":
                self._status_panel.config_path = str(
                    self._discovery_service.project_config_path
                )
            elif level == "Plugin":
                self._status_panel.config_path = "~/.claude/plugins"
            else:
                project_name = self._discovery_service.project_root.name
                self._status_panel.config_path = project_name
