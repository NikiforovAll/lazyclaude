"""Custom application footer with dynamic filter highlighting."""

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from lazyclaude.widgets.helpers.rendering import format_keybinding


class AppFooter(Widget):
    """Footer widget that highlights active filters."""

    DEFAULT_CSS = """
    AppFooter {
        dock: bottom;
        height: 1;
        background: $panel;
    }

    AppFooter .footer-content {
        width: 100%;
        text-align: center;
    }
    """

    filter_level: reactive[str] = reactive("All")
    search_active: reactive[bool] = reactive(False)
    disabled_filter_active: reactive[bool] = reactive(False)

    # Mode states
    preview_mode: reactive[bool] = reactive(False)
    marketplace_modal_visible: reactive[bool] = reactive(False)

    # Action availability
    can_refresh: reactive[bool] = reactive(True)
    can_edit: reactive[bool] = reactive(False)
    can_copy: reactive[bool] = reactive(False)
    can_move: reactive[bool] = reactive(False)
    can_delete: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static(self._get_footer_text(), classes="footer-content")

    def _get_footer_text(self) -> str:
        """Render footer with highlighted active filters."""
        parts = ["[bold]q[/] Quit", "[bold]?[/] Help"]

        # Conditional actions based on mode and state
        if not self.preview_mode:
            if self.can_refresh:
                parts.append("[bold]r[/] Refresh")
            if self.can_edit:
                parts.append("[bold]e[/] Edit")
            if self.can_copy:
                parts.append("[bold]c[/] Copy")
            if self.can_move:
                parts.append("[bold]m[/] Move")
            if self.can_delete:
                parts.append("[bold]d[/] Delete")

        # Filter keys (hidden when marketplace modal is visible or in preview mode)
        if not self.marketplace_modal_visible and not self.preview_mode:
            all_key = format_keybinding("a", "All", active=self.filter_level == "All")
            user_key = format_keybinding(
                "u", "User", active=self.filter_level == "User"
            )
            project_key = format_keybinding(
                "p", "Project", active=self.filter_level == "Project"
            )
            plugin_key = format_keybinding(
                "P", "Plugin", active=self.filter_level == "Plugin"
            )
            disabled_key = format_keybinding(
                "D", "Disabled", active=self.disabled_filter_active
            )
            parts.extend([all_key, user_key, project_key, plugin_key, disabled_key])

        # Search (always visible)
        search_key = format_keybinding("/", "Search", active=self.search_active)
        parts.append(search_key)

        # Marketplace or Exit Preview
        if not self.preview_mode:
            parts.append("[bold]M[/] Marketplace")
        else:
            parts.append("[bold]Esc[/] Exit")

        # Palette (always visible)
        parts.append("│  [bold][$accent]^p[/][/] Palette")

        return "  ".join(parts)

    def _update_content(self) -> None:
        """Update the footer content display."""
        if self.is_mounted:
            try:
                content = self.query_one(".footer-content", Static)
                content.update(self._get_footer_text())
            except Exception:
                pass

    def watch_filter_level(self, level: str) -> None:  # noqa: ARG002
        """React to filter level changes."""
        self._update_content()

    def watch_search_active(self, active: bool) -> None:  # noqa: ARG002
        """React to search active changes."""
        self._update_content()

    def watch_disabled_filter_active(self, active: bool) -> None:  # noqa: ARG002
        """React to disabled filter changes."""
        self._update_content()

    def watch_preview_mode(self, mode: bool) -> None:  # noqa: ARG002
        """React to preview mode changes."""
        self._update_content()

    def watch_marketplace_modal_visible(self, visible: bool) -> None:  # noqa: ARG002
        """React to marketplace modal visibility changes."""
        self._update_content()

    def watch_can_refresh(self, can: bool) -> None:  # noqa: ARG002
        """React to can_refresh changes."""
        self._update_content()

    def watch_can_edit(self, can: bool) -> None:  # noqa: ARG002
        """React to can_edit changes."""
        self._update_content()

    def watch_can_copy(self, can: bool) -> None:  # noqa: ARG002
        """React to can_copy changes."""
        self._update_content()

    def watch_can_move(self, can: bool) -> None:  # noqa: ARG002
        """React to can_move changes."""
        self._update_content()

    def watch_can_delete(self, can: bool) -> None:  # noqa: ARG002
        """React to can_delete changes."""
        self._update_content()
