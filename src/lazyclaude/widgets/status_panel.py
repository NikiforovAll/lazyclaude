"""StatusPanel widget for displaying current configuration status."""

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class StatusPanel(Widget):
    """Panel displaying current configuration folder status."""

    DEFAULT_CSS = """
    StatusPanel {
        height: 3;
        border: solid $primary;
        padding: 0 1;
        border-title-align: left;
    }

    StatusPanel:focus {
        border: double $accent;
    }

    StatusPanel .status-content {
        height: 1;
    }
    """

    config_path: reactive[str] = reactive("")
    filter_level: reactive[str] = reactive("All")
    search_active: reactive[bool] = reactive(False)
    disabled_filter_active: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        """Compose the panel content."""
        yield Static(self._get_status_text(), classes="status-content")

    def _get_status_text(self) -> str:
        """Render the status content with path and filter level."""
        level_display = (
            f"[$primary]{self.filter_level}[/]"
            if self.filter_level != "All"
            else self.filter_level
        )
        search_display = " | [$primary]Search[/]" if self.search_active else ""
        disabled_display = (
            " | [$primary]Disabled[/]" if self.disabled_filter_active else ""
        )
        return f"{self.config_path} | {level_display}{search_display}{disabled_display}"

    def on_mount(self) -> None:
        """Handle mount event."""
        self.border_title = "Status"

    def _update_content(self) -> None:
        """Update the status content display."""
        if self.is_mounted:
            try:
                content = self.query_one(".status-content", Static)
                content.update(self._get_status_text())
            except Exception:
                pass

    def watch_config_path(self, path: str) -> None:  # noqa: ARG002
        """React to config path changes."""
        self._update_content()

    def watch_filter_level(self, level: str) -> None:  # noqa: ARG002
        """React to filter level changes."""
        self._update_content()

    def watch_search_active(self, active: bool) -> None:  # noqa: ARG002
        """React to search active changes."""
        self._update_content()

    def watch_disabled_filter_active(self, active: bool) -> None:  # noqa: ARG002
        """React to disabled filter changes."""
        self._update_content()
