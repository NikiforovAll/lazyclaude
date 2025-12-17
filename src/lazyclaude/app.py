"""Main LazyClaude TUI Application."""

import os
import subprocess
import traceback
from pathlib import Path

import pyperclip
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Static

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.config_path_resolver import ConfigPathResolver
from lazyclaude.services.discovery import ConfigDiscoveryService
from lazyclaude.services.filter import FilterService
from lazyclaude.services.writer import CustomizationWriter
from lazyclaude.widgets.combined_panel import CombinedPanel
from lazyclaude.widgets.delete_confirm import DeleteConfirm
from lazyclaude.widgets.detail_pane import MainPane
from lazyclaude.widgets.filter_input import FilterInput
from lazyclaude.widgets.level_selector import LevelSelector
from lazyclaude.widgets.plugin_confirm import PluginConfirm
from lazyclaude.widgets.status_panel import StatusPanel
from lazyclaude.widgets.type_panel import TypePanel


class LazyClaude(App):
    """A lazygit-style TUI for visualizing Claude Code customizations."""

    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "toggle_help", "Help"),
        Binding("r", "refresh", "Refresh"),
        Binding("e", "open_in_editor", "Edit"),
        Binding("c", "copy_customization", "Copy"),
        Binding("m", "move_customization", "Move"),
        Binding("d", "delete_customization", "Delete"),
        Binding("C", "copy_config_path", "Copy Path"),
        Binding("tab", "focus_next_panel", "Next Panel", show=False),
        Binding("shift+tab", "focus_previous_panel", "Prev Panel", show=False),
        Binding("escape", "back", "Back", show=False),
        Binding("a", "filter_all", "All"),
        Binding("u", "filter_user", "User"),
        Binding("p", "filter_project", "Project"),
        Binding("P", "filter_plugin", "Plugin"),
        Binding("D", "toggle_plugin_enabled_filter", "Disabled"),
        Binding("t", "toggle_plugin_enabled", "Toggle"),
        Binding("/", "search", "Search"),
        Binding("[", "prev_view", "[", show=True),
        Binding("]", "next_view", "]", show=True),
        Binding("0", "focus_main_pane", "Panel 0", show=False),
        Binding("1", "focus_panel_1", "Panel 1", show=False),
        Binding("2", "focus_panel_2", "Panel 2", show=False),
        Binding("3", "focus_panel_3", "Panel 3", show=False),
        Binding("4", "focus_panel_4", "Panel 4", show=False),
        Binding("5", "focus_panel_5", "Panel 5", show=False),
        Binding("6", "focus_panel_6", "Panel 6", show=False),
        Binding("ctrl+u", "open_user_config", "User Config", show=False),
    ]

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
        self._help_visible = False
        self._last_focused_panel: TypePanel | None = None
        self._last_focused_combined: bool = False
        self._pending_customization: Customization | None = None
        self._panel_before_selector: TypePanel | None = None
        self._combined_before_selector: bool = False
        self._config_path_resolver: ConfigPathResolver | None = None

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

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event - load customizations."""
        self.theme = "gruvbox"
        self._load_customizations()
        self._update_status_panel()
        self._config_path_resolver = ConfigPathResolver(
            self._discovery_service._plugin_loader,
        )

    def check_action(
        self,
        action: str,
        parameters: tuple[object, ...],  # noqa: ARG002
    ) -> bool | None:
        """Control action availability based on current state."""
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
        filtered = self._get_filtered_customizations()
        for panel in self._panels:
            panel.set_customizations(filtered)
        if self._combined_panel:
            self._combined_panel.set_customizations(filtered)

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

    def action_copy_customization(self) -> None:
        """Copy selected customization to another level."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if customization.type not in self._COPYABLE_TYPES:
            self._show_status_error(
                f"Cannot copy {customization.type_label} customizations"
            )
            return

        available = self._get_available_target_levels(customization)
        if not available:
            self._show_status_error("No available target levels")
            return

        self._pending_customization = customization
        self._panel_before_selector = self._get_focused_panel()
        self._combined_before_selector = (
            self._combined_panel.has_focus if self._combined_panel else False
        )
        if self._level_selector:
            self._level_selector.show(available, "copy")

    def action_move_customization(self) -> None:
        """Move selected customization to another level."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if customization.type not in self._COPYABLE_TYPES:
            self._show_status_error(
                f"Cannot move {customization.type_label} customizations"
            )
            return

        if customization.level == ConfigLevel.PLUGIN:
            self._show_status_error("Cannot move from plugin-level customizations")
            return

        available = self._get_available_target_levels(customization)
        if not available:
            self._show_status_error("No available target levels")
            return

        self._pending_customization = customization
        self._panel_before_selector = self._get_focused_panel()
        self._combined_before_selector = (
            self._combined_panel.has_focus if self._combined_panel else False
        )
        if self._level_selector:
            self._level_selector.show(available, "move")

    def action_delete_customization(self) -> None:
        """Delete selected customization."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if customization.type not in self._COPYABLE_TYPES:
            self._show_status_error(
                f"Cannot delete {customization.type_label} customizations"
            )
            return

        if customization.level == ConfigLevel.PLUGIN:
            self._show_status_error("Cannot delete plugin-level customizations")
            return

        self._panel_before_selector = self._get_focused_panel()
        self._combined_before_selector = (
            self._combined_panel.has_focus if self._combined_panel else False
        )
        if self._delete_confirm:
            self._delete_confirm.show(customization)

    async def action_back(self) -> None:
        """Go back - return focus to panel from main pane, keep content visible."""
        if self._main_pane and self._main_pane.has_focus:
            if self._last_focused_combined and self._combined_panel:
                self._combined_panel.focus()
            elif self._last_focused_panel:
                self._last_focused_panel.focus()
            elif self._panels:
                self._panels[0].focus()

    def action_focus_next_panel(self) -> None:
        """Focus the next panel (panels 1-3, then combined panel)."""
        current = self._get_focused_panel_index()
        if current is None:
            if self._panels:
                self._panels[0].focus()
        elif current < len(self._panels) - 1:
            self._panels[current + 1].focus()
        elif current == len(self._panels) - 1 and self._combined_panel:
            self._combined_panel.focus()
        elif self._panels:
            self._panels[0].focus()

    def action_focus_previous_panel(self) -> None:
        """Focus the previous panel (combined panel, then panels 3-1)."""
        current = self._get_focused_panel_index()
        if current is None or current == 0:
            if self._combined_panel:
                self._combined_panel.focus()
            elif self._panels:
                self._panels[-1].focus()
        elif current == len(self._panels) and self._panels:
            self._panels[-1].focus()
        elif current > 0:
            self._panels[current - 1].focus()

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

    def _get_available_target_levels(
        self, customization: Customization
    ) -> list[ConfigLevel]:
        """Get available target levels for copy/move based on customization type."""
        if customization.type in self._PROJECT_LOCAL_TYPES:
            all_levels = [
                ConfigLevel.USER,
                ConfigLevel.PROJECT,
                ConfigLevel.PROJECT_LOCAL,
            ]
        else:
            all_levels = [ConfigLevel.USER, ConfigLevel.PROJECT]
        return [level for level in all_levels if level != customization.level]

    def _delete_customization(
        self, customization: Customization, writer: CustomizationWriter
    ) -> tuple[bool, str]:
        """Delete customization using type-specific method."""
        if customization.type == CustomizationType.MCP:
            return writer.delete_mcp_customization(
                customization, self._discovery_service.project_config_path
            )
        elif customization.type == CustomizationType.HOOK:
            return writer.delete_hook_customization(customization)
        else:
            return writer.delete_customization(customization)

    def _get_focused_panel_index(self) -> int | None:
        """Get the index of the currently focused panel (combined panel = len(panels))."""
        for i, panel in enumerate(self._panels):
            if panel.has_focus:
                return i
        if self._combined_panel and self._combined_panel.has_focus:
            return len(self._panels)
        return None

    def _focus_panel(self, index: int) -> None:
        """Focus a specific panel by index (0-based)."""
        if 0 <= index < len(self._panels):
            self._panels[index].focus()

    def action_focus_panel_1(self) -> None:
        """Focus panel 1 (Slash Commands)."""
        self._focus_panel(0)

    def action_focus_panel_2(self) -> None:
        """Focus panel 2 (Subagents)."""
        self._focus_panel(1)

    def action_focus_panel_3(self) -> None:
        """Focus panel 3 (Skills)."""
        self._focus_panel(2)

    def action_focus_panel_4(self) -> None:
        """Focus combined panel and switch to Memory Files."""
        if self._combined_panel:
            self._combined_panel.switch_to_type(CustomizationType.MEMORY_FILE)
            self._combined_panel.focus()

    def action_focus_panel_5(self) -> None:
        """Focus combined panel and switch to MCPs."""
        if self._combined_panel:
            self._combined_panel.switch_to_type(CustomizationType.MCP)
            self._combined_panel.focus()

    def action_focus_panel_6(self) -> None:
        """Focus combined panel and switch to Hooks."""
        if self._combined_panel:
            self._combined_panel.switch_to_type(CustomizationType.HOOK)
            self._combined_panel.focus()

    def action_focus_main_pane(self) -> None:
        """Focus the main pane (panel 0)."""
        if self._main_pane:
            self._main_pane.focus()

    def action_prev_view(self) -> None:
        """Switch view based on focused widget."""
        if self._combined_panel and self._combined_panel.has_focus:
            self._combined_panel.action_prev_tab()
        elif self._main_pane:
            self._main_pane.action_prev_view()

    def action_next_view(self) -> None:
        """Switch view based on focused widget."""
        if self._combined_panel and self._combined_panel.has_focus:
            self._combined_panel.action_next_tab()
        elif self._main_pane:
            self._main_pane.action_next_view()

    def action_filter_all(self) -> None:
        """Show all customizations (clear level filter)."""
        self._level_filter = None
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()
        self._update_subtitle()
        self._update_status_filter("All")

    def action_filter_user(self) -> None:
        """Show only user-level customizations."""
        self._level_filter = ConfigLevel.USER
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()
        self._update_subtitle()
        self._update_status_filter("User")

    def action_filter_project(self) -> None:
        """Show only project-level customizations."""
        self._level_filter = ConfigLevel.PROJECT
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()
        self._update_subtitle()
        self._update_status_filter("Project")

    def action_filter_plugin(self) -> None:
        """Show only plugin-level customizations."""
        self._level_filter = ConfigLevel.PLUGIN
        self._last_focused_panel = None
        if self._main_pane:
            self._main_pane.customization = None
        self._update_panels()
        self._update_subtitle()
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
        self._update_panels()
        self._update_subtitle()

    def action_toggle_plugin_enabled(self) -> None:
        """Toggle enabled state for selected plugin customization."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if not customization.plugin_info:
            self._show_status_error("Not a plugin customization")
            return

        self._panel_before_selector = self._get_focused_panel()
        self._combined_before_selector = (
            self._combined_panel.has_focus if self._combined_panel else False
        )
        if self._plugin_confirm:
            self._plugin_confirm.show(
                plugin_info=customization.plugin_info,
                customizations=self._customizations,
            )

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

    def action_search(self) -> None:
        """Activate search mode."""
        if self._filter_input:
            self._filter_input.show()

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

    def on_filter_input_filter_applied(
        self,
        message: FilterInput.FilterApplied,  # noqa: ARG002
    ) -> None:
        """Handle filter application (Enter key)."""
        if self._filter_input:
            self._filter_input.hide()

    def on_level_selector_level_selected(
        self, message: LevelSelector.LevelSelected
    ) -> None:
        """Handle level selection from the level selector bar."""
        if self._pending_customization:
            self._handle_copy_or_move(
                self._pending_customization, message.level, message.operation
            )
            self._pending_customization = None
        self._restore_focus_after_selector()

    def on_level_selector_selection_cancelled(
        self,
        message: LevelSelector.SelectionCancelled,  # noqa: ARG002
    ) -> None:
        """Handle level selector cancellation."""
        self._pending_customization = None
        self._restore_focus_after_selector()

    def on_plugin_confirm_plugin_confirmed(
        self, message: PluginConfirm.PluginConfirmed
    ) -> None:
        """Handle plugin toggle confirmation."""
        writer = CustomizationWriter()
        success, msg = writer.toggle_plugin_enabled(
            message.plugin_info,
            self._discovery_service.user_config_path,
            self._discovery_service.project_config_path,
        )

        if success:
            self.notify(msg, severity="information")
            self.action_refresh()
            self._restore_focus_after_selector()
        else:
            self.notify(msg, severity="error")
            self._restore_focus_after_selector()

    def on_plugin_confirm_confirmation_cancelled(
        self,
        message: PluginConfirm.ConfirmationCancelled,  # noqa: ARG002
    ) -> None:
        """Handle plugin confirmation cancellation."""
        self._restore_focus_after_selector()

    def on_delete_confirm_delete_confirmed(
        self, message: DeleteConfirm.DeleteConfirmed
    ) -> None:
        """Handle delete confirmation."""
        customization = message.customization
        writer = CustomizationWriter()
        success, msg = self._delete_customization(customization, writer)

        if success:
            self.notify(msg, severity="information")
            self.action_refresh()
        else:
            self.notify(msg, severity="error")
        self._restore_focus_after_selector()

    def on_delete_confirm_delete_cancelled(
        self,
        message: DeleteConfirm.DeleteCancelled,  # noqa: ARG002
    ) -> None:
        """Handle delete cancellation."""
        self._restore_focus_after_selector()

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

    def _handle_copy_or_move(
        self, customization: Customization, target_level: ConfigLevel, operation: str
    ) -> None:
        """Handle copy or move operation."""
        if operation == "move" and customization.level == ConfigLevel.PLUGIN:
            self._show_status_error("Cannot move from plugin (read-only source)")
            return

        writer = CustomizationWriter()

        if customization.type == CustomizationType.MCP:
            success, msg = writer.write_mcp_customization(
                customization,
                target_level,
                self._discovery_service.project_config_path,
            )
        elif customization.type == CustomizationType.HOOK:
            success, msg = writer.write_hook_customization(
                customization,
                target_level,
                self._discovery_service.user_config_path,
                self._discovery_service.project_config_path,
            )
        else:
            success, msg = writer.write_customization(
                customization,
                target_level,
                self._discovery_service.user_config_path,
                self._discovery_service.project_config_path,
            )

        if not success:
            self._show_status_error(msg)
            return

        if operation == "move":
            delete_success, delete_msg = self._delete_customization(
                customization, writer
            )
            if not delete_success:
                self._show_status_error(
                    f"Copied but failed to delete source: {delete_msg}"
                )
                return
            msg = f"Moved '{customization.name}' to {target_level.label} level"

        self._show_status_success(msg)
        self.action_refresh()

    def _show_status_success(self, message: str) -> None:
        """Show success toast notification."""
        self.notify(message, severity="information", timeout=3.0)

    def _show_status_error(self, message: str) -> None:
        """Show error toast notification."""
        self.notify(message, severity="error", timeout=3.0)

    def action_toggle_help(self) -> None:
        """Toggle help overlay visibility."""
        if self._help_visible:
            self._hide_help()
        else:
            self._show_help()

    def _show_help(self) -> None:
        """Show help overlay."""
        help_content = r"""[bold]LazyClaude Help[/]

[bold]Navigation[/]
  j/k or ↑/↓     Move up/down in list
  d/u            Page down/up (detail pane)
  g/G            Go to top/bottom
  0              Focus main pane
  1-3            Focus panel by number
  4-6            Focus combined panel tab
  Tab            Switch between panels
  Enter          Drill down
  Esc            Go back

[bold]Filtering[/]
  /              Search by name/description
  a              Show all levels
  u              Show user-level only
  p              Show project-level only
  P              Show plugin-level only
  D              Toggle disabled plugins

[bold]Views[/]
  \[ / ]         Main: content/metadata
                 Combined: switch tabs

[bold]Actions[/]
  e              Open in $EDITOR
  c              Copy to level
  m              Move to level
  t              Toggle plugin enabled
  C              Copy path to clipboard
  r              Refresh from disk
  Ctrl+u         Open user config
  ?              Toggle this help
  q              Quit

[dim]Press ? or Esc to close[/]"""

        if not self.query("#help-overlay"):
            help_widget = Static(help_content, id="help-overlay")
            self.mount(help_widget)
            self._help_visible = True

    def _hide_help(self) -> None:
        """Hide help overlay."""
        try:
            help_widget = self.query_one("#help-overlay")
            help_widget.remove()
            self._help_visible = False
        except Exception:
            pass


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
