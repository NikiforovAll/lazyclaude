"""Main LazyClaude TUI Application."""

import os
import subprocess
import traceback
from pathlib import Path

import pyperclip
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.theme import Theme
from textual.widgets import Footer

from lazyclaude.bindings import APP_BINDINGS
from lazyclaude.mixins import (
    CustomizationActionsMixin,
    FilterMixin,
    HelpMixin,
    MarketplaceMixin,
    NavigationMixin,
)
from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    MemoryFileRef,
)
from lazyclaude.models.marketplace import MarketplacePlugin
from lazyclaude.models.settings import AppSettings
from lazyclaude.services.config_path_resolver import ConfigPathResolver
from lazyclaude.services.discovery import ConfigDiscoveryService
from lazyclaude.services.filter import FilterService
from lazyclaude.services.marketplace_loader import MarketplaceLoader
from lazyclaude.services.settings import SettingsService
from lazyclaude.themes import CUSTOM_THEMES
from lazyclaude.widgets.combined_panel import CombinedPanel
from lazyclaude.widgets.delete_confirm import DeleteConfirm
from lazyclaude.widgets.detail_pane import MainPane
from lazyclaude.widgets.filter_input import FilterInput
from lazyclaude.widgets.level_selector import LevelSelector
from lazyclaude.widgets.marketplace_modal import MarketplaceModal
from lazyclaude.widgets.plugin_confirm import PluginConfirm
from lazyclaude.widgets.status_panel import StatusPanel
from lazyclaude.widgets.type_panel import TypePanel


class LazyClaude(
    NavigationMixin,
    FilterMixin,
    MarketplaceMixin,
    CustomizationActionsMixin,
    HelpMixin,
    App,
):
    """A lazygit-style TUI for visualizing Claude Code customizations."""

    CSS_PATH = "styles/app.tcss"
    LAYERS = ["default", "overlay"]
    BINDINGS = APP_BINDINGS

    TITLE = "LazyClaude"
    SUB_TITLE = "Claude Code Customization Viewer"

    _COPYABLE_TYPES = (
        CustomizationType.SLASH_COMMAND,
        CustomizationType.SUBAGENT,
        CustomizationType.SKILL,
        CustomizationType.HOOK,
        CustomizationType.MCP,
        CustomizationType.MEMORY_FILE,
    )
    _PROJECT_LOCAL_TYPES = (CustomizationType.HOOK, CustomizationType.MCP)

    def __init__(
        self,
        discovery_service: ConfigDiscoveryService | None = None,
        user_config_path: Path | None = None,
        project_config_path: Path | None = None,
    ) -> None:
        """Initialize LazyClaude application."""
        super().__init__()
        self._user_config_path = user_config_path
        self._project_config_path = project_config_path
        self._discovery_service = discovery_service or ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=project_config_path,
        )
        self._filter_service = FilterService()
        self._customizations: list[Customization] = []
        self._level_filter: ConfigLevel | None = None
        self._search_query: str = ""
        self._plugin_enabled_filter: bool | None = True
        self._panels: list[TypePanel] = []
        self._combined_panel: CombinedPanel | None = None
        self._status_panel: StatusPanel | None = None
        self._main_pane: MainPane | None = None
        self._filter_input: FilterInput | None = None
        self._level_selector: LevelSelector | None = None
        self._plugin_confirm: PluginConfirm | None = None
        self._delete_confirm: DeleteConfirm | None = None
        self._marketplace_modal: MarketplaceModal | None = None
        self._marketplace_loader: MarketplaceLoader | None = None
        self._help_visible = False
        self._last_focused_panel: TypePanel | None = None
        self._last_focused_combined: bool = False
        self._pending_customization: Customization | None = None
        self._panel_before_selector: TypePanel | None = None
        self._combined_before_selector: bool = False
        self._config_path_resolver: ConfigPathResolver | None = None
        self._plugin_preview_mode: bool = False
        self._previewing_plugin: MarketplacePlugin | None = None
        self._plugin_customizations: list[Customization] = []
        self._settings_service = SettingsService()
        self._settings = AppSettings()

    def _fatal_error(self) -> None:
        """Print simple traceback instead of Rich's fancy one."""
        self.bell()
        traceback.print_exc()
        self.exit()

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        with Container(id="sidebar"):
            self._status_panel = StatusPanel(id="status-panel")
            yield self._status_panel

            separate_types = [
                CustomizationType.SLASH_COMMAND,
                CustomizationType.SUBAGENT,
                CustomizationType.SKILL,
            ]
            for i, ctype in enumerate(separate_types, start=1):
                panel = TypePanel(ctype, id=f"panel-{ctype.name.lower()}")
                panel.panel_number = i
                self._panels.append(panel)
                yield panel

            self._combined_panel = CombinedPanel(id="panel-combined")
            yield self._combined_panel

        self._main_pane = MainPane(id="main-pane")
        yield self._main_pane

        self._filter_input = FilterInput(id="filter-input")
        yield self._filter_input

        self._level_selector = LevelSelector(id="level-selector")
        yield self._level_selector

        self._plugin_confirm = PluginConfirm(id="plugin-confirm")
        yield self._plugin_confirm

        self._delete_confirm = DeleteConfirm(id="delete-confirm")
        yield self._delete_confirm

        self._marketplace_modal = MarketplaceModal(id="marketplace-modal")
        yield self._marketplace_modal

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event - load customizations."""
        for theme in CUSTOM_THEMES:
            self.register_theme(theme)
        self._settings = self._settings_service.load()
        self.theme = self._settings.theme
        self.theme_changed_signal.subscribe(self, self._on_theme_changed)
        self._load_customizations()
        self._update_status_panel()
        self._config_path_resolver = ConfigPathResolver(
            self._discovery_service._plugin_loader,
        )
        self._marketplace_loader = MarketplaceLoader(
            user_config_path=self._discovery_service.user_config_path,
            plugin_loader=self._discovery_service._plugin_loader,
        )
        if self._marketplace_modal:
            self._marketplace_modal.set_loader(self._marketplace_loader)

    def _on_theme_changed(self, theme: Theme) -> None:  # noqa: ARG002
        """Persist theme when changed via theme picker."""
        if self._settings.theme != self.theme:
            self._settings.theme = self.theme
            self._settings_service.save(self._settings)

    def check_action(
        self,
        action: str,
        parameters: tuple[object, ...],  # noqa: ARG002
    ) -> bool | None:
        """Control action availability based on current state."""
        if action == "exit_preview":
            return self._plugin_preview_mode

        if self._plugin_preview_mode:
            preview_allowed_actions = {
                "quit",
                "toggle_help",
                "search",
                "focus_next_panel",
                "focus_previous_panel",
                "focus_panel_1",
                "focus_panel_2",
                "focus_panel_3",
                "focus_panel_4",
                "focus_panel_5",
                "focus_panel_6",
                "focus_panel_7",
                "focus_main_pane",
                "prev_view",
                "next_view",
                "exit_preview",
            }
            return action in preview_allowed_actions

        if action == "toggle_plugin_enabled":
            if not self._main_pane or not self._main_pane.customization:
                return False
            return self._main_pane.customization.plugin_info is not None

        if action in (
            "copy_customization",
            "move_customization",
            "delete_customization",
        ):
            if not self._main_pane or not self._main_pane.customization:
                return False

            if self._is_skill_subfile_selected():
                return False

            customization = self._main_pane.customization

            if customization.type not in self._COPYABLE_TYPES:
                return False
            if (
                action in ("delete_customization", "move_customization")
                and customization.level == ConfigLevel.PLUGIN
            ):
                return False

        return True

    def _update_status_panel(self) -> None:
        """Update status panel with current config path and filter level."""
        if self._status_panel:
            project_name = self._discovery_service.project_root.name
            self._status_panel.config_path = project_name
            self._status_panel.filter_level = "All"

    def _load_customizations(self) -> None:
        """Load customizations from discovery service."""
        self._customizations = self._discovery_service.discover_all()
        self._update_panels()

    def _update_panels(self) -> None:
        """Update all panels with filtered customizations."""
        if self._plugin_preview_mode:
            customizations = self._filter_service.filter(
                self._plugin_customizations,
                query=self._search_query,
                level=None,
                plugin_enabled=None,
            )
        else:
            customizations = self._get_filtered_customizations()
        for panel in self._panels:
            panel.set_customizations(customizations)
        if self._combined_panel:
            self._combined_panel.set_customizations(customizations)

    def _get_filtered_customizations(self) -> list[Customization]:
        """Get customizations filtered by current level and search query."""
        return self._filter_service.filter(
            self._customizations,
            query=self._search_query,
            level=self._level_filter,
            plugin_enabled=self._plugin_enabled_filter,
        )

    def _update_display_path(self, customization: Customization | None) -> None:
        """Update main pane display path with resolved path for plugins."""
        if not self._main_pane:
            return

        if not customization or not self._config_path_resolver:
            self._main_pane.display_path = None
            return

        resolved = self._config_path_resolver.resolve_file(customization)
        self._main_pane.display_path = resolved

    def _update_subtitle(self) -> None:
        """Update subtitle to reflect current filter state."""
        if self._plugin_preview_mode and self._previewing_plugin:
            self.sub_title = f"Preview: {self._previewing_plugin.name} | Esc to exit"
            return

        parts = []
        if self._level_filter == ConfigLevel.USER:
            parts.append("User Level")
        elif self._level_filter == ConfigLevel.PROJECT:
            parts.append("Project Level")
        elif self._level_filter == ConfigLevel.PLUGIN:
            parts.append("Plugin Level")
        else:
            parts.append("All Levels")

        if self._plugin_enabled_filter is True:
            parts.append("Enabled Only")

        if self._search_query:
            parts.append(f'Search: "{self._search_query}"')

        self.sub_title = " | ".join(parts)

    # Panel selection message handlers

    def on_type_panel_selection_changed(
        self, message: TypePanel.SelectionChanged
    ) -> None:
        """Handle selection change in a type panel."""
        if self._main_pane:
            self._update_display_path(message.customization)
            self._main_pane.customization = message.customization
        self.refresh_bindings()

    def on_type_panel_drill_down(self, message: TypePanel.DrillDown) -> None:
        """Handle drill down into a customization."""
        if self._main_pane:
            self._last_focused_panel = self._get_focused_panel()
            self._last_focused_combined = False
            self._update_display_path(message.customization)
            self._main_pane.customization = message.customization
            self._main_pane.focus()

    def on_combined_panel_selection_changed(
        self, message: CombinedPanel.SelectionChanged
    ) -> None:
        """Handle selection change in the combined panel."""
        if self._main_pane:
            self._update_display_path(message.customization)
            self._main_pane.customization = message.customization
        self.refresh_bindings()

    def on_combined_panel_drill_down(self, message: CombinedPanel.DrillDown) -> None:
        """Handle drill down from the combined panel."""
        if self._main_pane:
            self._last_focused_panel = None
            self._last_focused_combined = True
            self._update_display_path(message.customization)
            self._main_pane.customization = message.customization
            self._main_pane.focus()

    def on_type_panel_skill_file_selected(
        self, message: TypePanel.SkillFileSelected
    ) -> None:
        """Handle skill file selection in the skills tree."""
        if self._main_pane:
            self._main_pane.selected_file = message.file_path
            customization = self._main_pane.customization
            if customization and self._config_path_resolver:
                path_to_resolve = message.file_path or customization.path
                resolved = self._config_path_resolver.resolve_path(
                    customization, path_to_resolve
                )
                self._main_pane.display_path = resolved

    def on_type_panel_memory_file_ref_selected(
        self, message: TypePanel.MemoryFileRefSelected
    ) -> None:
        """Handle memory file ref selection in the memory files tree."""
        self._handle_memory_file_ref_selected(message.ref)

    def on_combined_panel_memory_file_ref_selected(
        self, message: CombinedPanel.MemoryFileRefSelected
    ) -> None:
        """Handle memory file ref selection in the combined panel."""
        self._handle_memory_file_ref_selected(message.ref)

    def _handle_memory_file_ref_selected(self, ref: MemoryFileRef | None) -> None:
        """Handle memory file ref selection from any panel."""
        if self._main_pane:
            self._main_pane.selected_ref = ref
            customization = self._main_pane.customization
            if customization and self._config_path_resolver:
                path_to_resolve = ref.path if ref and ref.path else None
                if path_to_resolve:
                    resolved = self._config_path_resolver.resolve_path(
                        customization, path_to_resolve
                    )
                    self._main_pane.display_path = resolved
                else:
                    self._main_pane.display_path = (
                        self._config_path_resolver.resolve_path(
                            customization, customization.path
                        )
                    )

    # Filter input message handlers

    def on_filter_input_filter_changed(
        self, message: FilterInput.FilterChanged
    ) -> None:
        """Handle filter query changes (real-time filtering)."""
        self._search_query = message.query
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()
        self._update_subtitle()

    def on_filter_input_filter_cancelled(
        self,
        message: FilterInput.FilterCancelled,  # noqa: ARG002
    ) -> None:
        """Handle filter cancellation."""
        self._search_query = ""
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()
        self._update_subtitle()
        self.refresh_bindings()

    def on_filter_input_filter_applied(
        self,
        message: FilterInput.FilterApplied,  # noqa: ARG002
    ) -> None:
        """Handle filter application (Enter key)."""
        if self._filter_input:
            self._filter_input.hide()
        self.refresh_bindings()

    # Basic actions

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_refresh(self) -> None:
        """Refresh customizations from disk."""
        self._customizations = self._discovery_service.refresh()
        self._update_panels()

    def action_open_in_editor(self) -> None:
        """Open the selected customization file in $EDITOR."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if self._main_pane.selected_file:
            file_path = self._main_pane.selected_file
        elif customization.type == CustomizationType.SKILL:
            file_path = customization.path.parent
        else:
            file_path = customization.path

        if customization.level == ConfigLevel.PLUGIN and self._config_path_resolver:
            resolved = self._config_path_resolver.resolve_path(customization, file_path)
            if resolved:
                file_path = resolved

        if not file_path.exists():
            return

        editor = os.environ.get("EDITOR", "vi")
        subprocess.Popen([editor, str(file_path)], shell=True)

    def _open_paths_in_editor(self, paths: list[Path]) -> None:
        """Open paths in $EDITOR with error handling."""
        valid_paths = [p for p in paths if p.exists()]
        if not valid_paths:
            self.notify("No valid paths to open", severity="warning")
            return

        editor = os.environ.get("EDITOR", "vi")
        subprocess.Popen([editor] + [str(p) for p in valid_paths], shell=True)

    def action_open_user_config(self) -> None:
        """Open user config folder (~/.claude/) and settings file in $EDITOR."""
        config_path = Path.home() / ".claude"
        settings_path = Path.home() / ".claude.json"

        paths_to_open = [p for p in [config_path, settings_path] if p.exists()]

        if not paths_to_open:
            self.notify("No user config found", severity="warning")
            return

        self._open_paths_in_editor(paths_to_open)

    def action_copy_config_path(self) -> None:
        """Copy file path of selected customization or focused file to clipboard."""
        if not self._main_pane or not self._main_pane.customization:
            self.notify("No customization selected", severity="warning")
            return

        customization = self._main_pane.customization

        if not self._config_path_resolver:
            self.notify("Path resolver not initialized", severity="error")
            return

        file_path = self._main_pane.selected_file or customization.path
        path = self._config_path_resolver.resolve_path(customization, file_path)

        if not path:
            self.notify("Cannot resolve path", severity="error")
            return

        path_str = str(path)
        pyperclip.copy(path_str)
        self.notify(f"Copied: {path_str}", severity="information")

    # Shared utilities

    def _get_focused_panel(self) -> TypePanel | None:
        """Get the currently focused TypePanel (not combined panel)."""
        for panel in self._panels:
            if panel.has_focus:
                return panel
        return None

    def _is_skill_subfile_selected(self) -> bool:
        """Check if a skill subfile is currently selected (not root skill)."""
        panel = self._get_focused_panel()
        if (
            panel
            and panel._is_skills_panel
            and panel._flat_items
            and 0 <= panel.selected_index < len(panel._flat_items)
        ):
            _, file_path = panel._flat_items[panel.selected_index]
            return file_path is not None
        return False

    def _restore_focus_after_selector(self) -> None:
        """Restore focus to the panel that was focused before the level selector."""
        if self._combined_before_selector and self._combined_panel:
            self._combined_panel.focus()
            self._combined_before_selector = False
            self._panel_before_selector = None
        elif self._panel_before_selector:
            self._panel_before_selector.focus()
            self._panel_before_selector = None
            self._combined_before_selector = False
        elif self._panels:
            self._panels[0].focus()

    def _show_status_success(self, message: str) -> None:
        """Show success toast notification."""
        self.notify(message, severity="information", timeout=3.0)

    def _show_status_error(self, message: str) -> None:
        """Show error toast notification."""
        self.notify(message, severity="error", timeout=3.0)


def create_app(
    user_config_path: Path | None = None,
    project_config_path: Path | None = None,
) -> LazyClaude:
    """
    Create application with all dependencies wired.

    Args:
        user_config_path: Override for ~/.claude (testing)
        project_config_path: Override for ./.claude (testing)

    Returns:
        Configured LazyClaude application instance.
    """
    discovery_service = ConfigDiscoveryService(
        user_config_path=user_config_path,
        project_config_path=project_config_path,
    )
    return LazyClaude(discovery_service=discovery_service)
