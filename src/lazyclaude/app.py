"""Main LazyClaude TUI Application."""

import os
import subprocess
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Static

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.discovery import ConfigDiscoveryService
from lazyclaude.services.filter import FilterService
from lazyclaude.widgets.detail_pane import MainPane
from lazyclaude.widgets.filter_input import FilterInput
from lazyclaude.widgets.status_panel import StatusPanel
from lazyclaude.widgets.type_panel import TypePanel


class LazyClaude(App):
    """A lazygit-style TUI for visualizing Claude Code customizations."""

    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "toggle_help", "Help"),
        Binding("R", "refresh", "Refresh", key_display="shift+r"),
        Binding("e", "open_in_editor", "Edit"),
        Binding("tab", "focus_next_panel", "Next Panel", show=False),
        Binding("shift+tab", "focus_previous_panel", "Prev Panel", show=False),
        Binding("escape", "back", "Back", show=False),
        Binding("a", "filter_all", "All"),
        Binding("u", "filter_user", "User"),
        Binding("p", "filter_project", "Project"),
        Binding("P", "filter_plugin", "Plugin"),
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
    ]

    TITLE = "LazyClaude"
    SUB_TITLE = "Claude Code Customization Viewer"

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
        self._panels: list[TypePanel] = []
        self._status_panel: StatusPanel | None = None
        self._main_pane: MainPane | None = None
        self._filter_input: FilterInput | None = None
        self._help_visible = False

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        with Container(id="sidebar"):
            self._status_panel = StatusPanel(id="status-panel")
            yield self._status_panel

            for i, ctype in enumerate(CustomizationType, start=1):
                panel = TypePanel(ctype, id=f"panel-{ctype.name.lower()}")
                panel.panel_number = i
                self._panels.append(panel)
                yield panel

        self._main_pane = MainPane(id="main-pane")
        yield self._main_pane

        self._filter_input = FilterInput(id="filter-input")
        yield self._filter_input

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event - load customizations."""
        self.theme = "gruvbox"
        self._load_customizations()
        self._update_status_panel()
        if self._panels:
            self._panels[0].focus()

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

    def _get_filtered_customizations(self) -> list[Customization]:
        """Get customizations filtered by current level and search query."""
        return self._filter_service.filter(
            self._customizations,
            query=self._search_query,
            level=self._level_filter,
        )

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

        if self._search_query:
            parts.append(f'Search: "{self._search_query}"')

        self.sub_title = " | ".join(parts)

    def on_type_panel_selection_changed(
        self, message: TypePanel.SelectionChanged
    ) -> None:
        """Handle selection change in a type panel."""
        if self._main_pane:
            self._main_pane.customization = message.customization

    def on_type_panel_drill_down(self, message: TypePanel.DrillDown) -> None:
        """Handle drill down into a customization."""
        if self._main_pane:
            self._main_pane.customization = message.customization
            self._main_pane.focus()

    def action_quit(self) -> None:
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

        file_path = self._main_pane.customization.path
        if not file_path.exists():
            return

        editor = os.environ.get("EDITOR", "vi")
        subprocess.Popen([editor, str(file_path)], shell=True)

    def action_back(self) -> None:
        """Go back - return focus to panel from main pane."""
        if self._main_pane and self._main_pane.has_focus:
            focused_panel = self._get_focused_panel()
            if focused_panel:
                focused_panel.focus()
            elif self._panels:
                self._panels[0].focus()

    def action_focus_next_panel(self) -> None:
        """Focus the next panel."""
        current = self._get_focused_panel_index()
        if current is not None and current < len(self._panels) - 1:
            self._panels[current + 1].focus()
        elif self._panels:
            self._panels[0].focus()

    def action_focus_previous_panel(self) -> None:
        """Focus the previous panel."""
        current = self._get_focused_panel_index()
        if current is not None and current > 0:
            self._panels[current - 1].focus()
        elif self._panels:
            self._panels[-1].focus()

    def _get_focused_panel(self) -> TypePanel | None:
        """Get the currently focused panel."""
        for panel in self._panels:
            if panel.has_focus:
                return panel
        return None

    def _get_focused_panel_index(self) -> int | None:
        """Get the index of the currently focused panel."""
        for i, panel in enumerate(self._panels):
            if panel.has_focus:
                return i
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
        """Focus panel 4 (Memory Files)."""
        self._focus_panel(3)

    def action_focus_panel_5(self) -> None:
        """Focus panel 5 (MCPs)."""
        self._focus_panel(4)

    def action_focus_panel_6(self) -> None:
        """Focus panel 6 (Hooks)."""
        self._focus_panel(5)

    def action_focus_main_pane(self) -> None:
        """Focus the main pane (panel 0)."""
        if self._main_pane:
            self._main_pane.focus()

    def action_prev_view(self) -> None:
        """Switch main pane to previous view."""
        if self._main_pane:
            self._main_pane.action_prev_view()

    def action_next_view(self) -> None:
        """Switch main pane to next view."""
        if self._main_pane:
            self._main_pane.action_next_view()

    def action_filter_all(self) -> None:
        """Show all customizations (clear level filter)."""
        self._level_filter = None
        self._update_panels()
        self._update_subtitle()
        self._update_status_filter("All")

    def action_filter_user(self) -> None:
        """Show only user-level customizations."""
        self._level_filter = ConfigLevel.USER
        self._update_panels()
        self._update_subtitle()
        self._update_status_filter("User")

    def action_filter_project(self) -> None:
        """Show only project-level customizations."""
        self._level_filter = ConfigLevel.PROJECT
        self._update_panels()
        self._update_subtitle()
        self._update_status_filter("Project")

    def action_filter_plugin(self) -> None:
        """Show only plugin-level customizations."""
        self._level_filter = ConfigLevel.PLUGIN
        self._update_panels()
        self._update_subtitle()
        self._update_status_filter("Plugin")

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
        self._update_panels()
        self._update_subtitle()

    def on_filter_input_filter_cancelled(
        self,
        message: FilterInput.FilterCancelled,  # noqa: ARG002
    ) -> None:
        """Handle filter cancellation."""
        self._search_query = ""
        self._update_panels()
        self._update_subtitle()
        if self._panels:
            self._panels[0].focus()

    def on_filter_input_filter_applied(
        self,
        message: FilterInput.FilterApplied,  # noqa: ARG002
    ) -> None:
        """Handle filter application (Enter key)."""
        if self._filter_input:
            self._filter_input.hide()
        if self._panels:
            self._panels[0].focus()

    def action_toggle_help(self) -> None:
        """Toggle help overlay visibility."""
        if self._help_visible:
            self._hide_help()
        else:
            self._show_help()

    def _show_help(self) -> None:
        """Show help overlay."""
        help_content = """[bold]LazyClaude Help[/]

[bold]Navigation[/]
  j/k or arrows  Move up/down in list
  g/G            Go to top/bottom
  1-6            Jump to panel by number
  Tab            Switch between panels
  Enter          View details
  Esc            Go back

[bold]Filtering[/]
  /              Search by name/description
  a              Show all levels
  u              Show user-level only
  p              Show project-level only
  P              Show plugin-level only

[bold]Actions[/]
  e              Open in $EDITOR
  R              Refresh from disk
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
