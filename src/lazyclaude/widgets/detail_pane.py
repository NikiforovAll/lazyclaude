"""DetailPane widget for displaying customization details."""

from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from lazyclaude.models.customization import Customization


class DetailPane(Widget):
    """Pane displaying full details of selected customization."""

    BINDINGS = [
        Binding("j", "scroll_down", "Scroll down", show=False),
        Binding("k", "scroll_up", "Scroll up", show=False),
        Binding("down", "scroll_down", "Scroll down", show=False),
        Binding("up", "scroll_up", "Scroll up", show=False),
        Binding("g", "scroll_top", "Scroll top", show=False),
        Binding("G", "scroll_bottom", "Scroll bottom", show=False, key_display="shift+g"),
    ]

    DEFAULT_CSS = """
    DetailPane {
        border: solid $primary;
        padding: 1;
        overflow-y: auto;
    }

    DetailPane:focus {
        border: double $accent;
    }

    DetailPane .detail-header {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    DetailPane .detail-metadata {
        color: $text-muted;
        padding-bottom: 1;
    }

    DetailPane .detail-content {
        color: $text;
    }

    DetailPane .detail-error {
        color: $error;
        text-style: bold;
    }

    DetailPane .empty-message {
        color: $text-muted;
        text-style: italic;
    }
    """

    customization: reactive[Customization | None] = reactive(None)

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize DetailPane."""
        super().__init__(name=name, id=id, classes=classes)
        self.can_focus = True

    def compose(self):
        """Compose the pane content."""
        yield Static(self._render_content(), classes="detail-content")

    def _render_content(self) -> str:
        """Render the detail content."""
        if not self.customization:
            return "[dim italic]Select a customization to view details[/]"

        c = self.customization
        lines = []

        lines.append(f"[bold]{c.name}[/]")
        lines.append("")

        lines.append(f"[dim]Type:[/] {c.type_label}")
        lines.append(f"[dim]Level:[/] {c.level_label}")
        lines.append(f"[dim]Path:[/] {c.path}")

        if c.description:
            lines.append(f"[dim]Description:[/] {c.description}")

        lines.append("")

        if c.has_error:
            lines.append(f"[red bold]Error:[/] [red]{c.error}[/]")
        elif c.content:
            lines.append("[dim]Content:[/]")
            lines.append("─" * 40)
            content_preview = c.content[:2000]
            if len(c.content) > 2000:
                content_preview += "\n... (truncated)"
            lines.append(content_preview)

        return "\n".join(lines)

    def watch_customization(
        self, customization: Customization | None  # noqa: ARG002
    ) -> None:
        """React to customization changes."""
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the pane display."""
        try:
            content = self.query_one(".detail-content", Static)
            content.update(self._render_content())
        except Exception:
            pass

    def action_scroll_down(self) -> None:
        """Scroll content down."""
        self.scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        """Scroll content up."""
        self.scroll_up(animate=False)

    def action_scroll_top(self) -> None:
        """Scroll to top."""
        self.scroll_home(animate=False)

    def action_scroll_bottom(self) -> None:
        """Scroll to bottom."""
        self.scroll_end(animate=False)
