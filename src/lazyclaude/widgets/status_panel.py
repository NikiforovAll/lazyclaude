"""StatusPanel widget for displaying current configuration status."""

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

    def compose(self):
        """Compose the panel content."""
        yield Static(self._render_content(), classes="status-content")

    def _render_content(self) -> str:
        """Render the status content with path and filter level."""
        return f"{self.config_path} | [bold]{self.filter_level}[/]"

    def on_mount(self) -> None:
        """Handle mount event."""
        self.border_title = "[0]-Status-"

    def _update_content(self) -> None:
        """Update the status content display."""
        if self.is_mounted:
            try:
                content = self.query_one(".status-content", Static)
                content.update(self._render_content())
            except Exception:
                pass

    def watch_config_path(self, path: str) -> None:  # noqa: ARG002
        """React to config path changes."""
        self._update_content()

    def watch_filter_level(self, level: str) -> None:  # noqa: ARG002
        """React to filter level changes."""
        self._update_content()
