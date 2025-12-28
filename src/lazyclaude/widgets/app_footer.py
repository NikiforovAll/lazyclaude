"""Custom application footer with dynamic filter highlighting."""

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


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
        all_key = (
            "[bold]a[/] [$primary]All[/]"
            if self.filter_level == "All"
            else "[bold]a[/] All"
        )
        user_key = (
            "[bold]u[/] [$primary]User[/]"
            if self.filter_level == "User"
            else "[bold]u[/] User"
        )
        project_key = (
            "[bold]p[/] [$primary]Project[/]"
            if self.filter_level == "Project"
            else "[bold]p[/] Project"
        )
        plugin_key = (
            "[bold]P[/] [$primary]Plugin[/]"
            if self.filter_level == "Plugin"
            else "[bold]P[/] Plugin"
        )
        disabled_key = (
            "[bold]D[/] [$primary]Disabled[/]"
            if self.disabled_filter_active
            else "[bold]D[/] Disabled"
        )
        search_key = (
            "[bold]/[/] [$primary]Search[/]"
            if self.search_active
            else "[bold]/[/] Search"
        )

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
