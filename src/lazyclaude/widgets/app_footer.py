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

    def compose(self) -> ComposeResult:
        yield Static(self._get_footer_text(), classes="footer-content")

    def _get_footer_text(self) -> str:
        """Render footer with highlighted active filters."""
        all_key = format_keybinding("a", "All", active=self.filter_level == "All")
        user_key = format_keybinding("u", "User", active=self.filter_level == "User")
        project_key = format_keybinding(
            "p", "Project", active=self.filter_level == "Project"
        )
        plugin_key = format_keybinding(
            "P", "Plugin", active=self.filter_level == "Plugin"
        )
        disabled_key = format_keybinding(
            "D", "Disabled", active=self.disabled_filter_active
        )
        search_key = format_keybinding("/", "Search", active=self.search_active)

        return (
            f"[bold]q[/] Quit  [bold]?[/] Help  [bold]r[/] Refresh  "
            f"[bold]e[/] Edit  [bold]c[/] Copy  [bold]m[/] Move  [bold]d[/] Delete  "
            f"{all_key}  {user_key}  {project_key}  {plugin_key}  "
            f"{disabled_key}  {search_key}  [bold]M[/] Marketplace"
        )

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
