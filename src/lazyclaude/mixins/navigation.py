"""Navigation mixin for LazyClaude application."""

from typing import TYPE_CHECKING

from lazyclaude.models.customization import CustomizationType

if TYPE_CHECKING:
    from lazyclaude.widgets.combined_panel import CombinedPanel
    from lazyclaude.widgets.detail_pane import MainPane
    from lazyclaude.widgets.type_panel import TypePanel


class NavigationMixin:
    """Mixin providing panel navigation and focus management."""

    _panels: list["TypePanel"]
    _combined_panel: "CombinedPanel | None"
    _main_pane: "MainPane | None"
    _last_focused_panel: "TypePanel | None"
    _last_focused_combined: bool
    _plugin_preview_mode: bool

    def action_focus_next_panel(self) -> None:
        """Focus the next panel (panels 1-3, then combined panel)."""
        current = self._get_focused_panel_index()
        if current is None:
            if self._panels:
                self._panels[0].focus()
        elif current < len(self._panels) - 1:
            self._panels[current + 1].focus()
        elif current == len(self._panels) - 1 and self._combined_panel:
            self._combined_panel.switch_to_type(CustomizationType.MEMORY_FILE)
            self._combined_panel.focus()
        elif self._panels:
            self._panels[0].focus()

    def action_focus_previous_panel(self) -> None:
        """Focus the previous panel (combined panel, then panels 3-1)."""
        current = self._get_focused_panel_index()
        if current is None or current == 0:
            if self._combined_panel:
                self._combined_panel.switch_to_type(CustomizationType.HOOK)
                self._combined_panel.focus()
            elif self._panels:
                self._panels[-1].focus()
        elif current == len(self._panels) and self._panels:
            self._panels[-1].focus()
        elif current > 0:
            self._panels[current - 1].focus()

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

    def action_focus_panel_7(self) -> None:
        """Focus combined panel and switch to LSP Servers."""
        if self._combined_panel:
            self._combined_panel.switch_to_type(CustomizationType.LSP_SERVER)
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

    async def action_back(self) -> None:
        """Go back - exit preview mode, or return focus to panel from main pane."""
        if self._plugin_preview_mode:
            self._exit_plugin_preview()  # type: ignore[attr-defined]
            return

        if self._main_pane and self._main_pane.has_focus:
            if self._last_focused_combined and self._combined_panel:
                self._combined_panel.focus()
            elif self._last_focused_panel:
                self._last_focused_panel.focus()
            elif self._panels:
                self._panels[0].focus()
