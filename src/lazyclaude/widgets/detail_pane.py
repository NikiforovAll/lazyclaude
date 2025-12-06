"""MainPane widget for displaying customization details."""

import re

from rich.console import Group, RenderableType
from rich.syntax import Syntax
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from lazyclaude.models.customization import Customization

TEXTUAL_TO_PYGMENTS_THEME: dict[str, str] = {
    "dracula": "dracula",
    "gruvbox": "gruvbox-dark",
    "monokai": "monokai",
    "nord": "nord",
    "solarized-light": "solarized-light",
    "catppuccin-latte": "default",
    "catppuccin-mocha": "monokai",
    "flexoki": "default",
    "textual-ansi": "default",
    "textual-dark": "monokai",
    "textual-light": "default",
    "tokyo-night": "nord",
}

DEFAULT_SYNTAX_THEME = "monokai"


class MainPane(Widget):
    """Main pane with switchable content/metadata views."""

    BINDINGS = [
        Binding("[", "prev_view", "Prev View", show=False),
        Binding("]", "next_view", "Next View", show=False),
        Binding("j", "scroll_down", "Scroll down", show=False),
        Binding("k", "scroll_up", "Scroll up", show=False),
        Binding("down", "scroll_down", "Scroll down", show=False),
        Binding("up", "scroll_up", "Scroll up", show=False),
        Binding("g", "scroll_top", "Scroll top", show=False),
        Binding("G", "scroll_bottom", "Scroll bottom", show=False, key_display="shift+g"),
    ]

    DEFAULT_CSS = """
    MainPane {
        height: 100%;
        border: solid $primary;
        padding: 1;
        overflow-y: auto;
        border-title-align: left;
    }

    MainPane:focus {
        border: double $accent;
    }

    MainPane .pane-content {
        width: 100%;
    }
    """

    customization: reactive[Customization | None] = reactive(None)
    view_mode: reactive[str] = reactive("content")

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize MainPane."""
        super().__init__(name=name, id=id, classes=classes)
        self.can_focus = True

    def compose(self):
        """Compose the pane content."""
        yield Static(self._render_content(), classes="pane-content")

    def _render_content(self) -> RenderableType:
        """Render content based on current view mode."""
        if self.view_mode == "metadata":
            return self._render_metadata()
        return self._render_file_content()

    def _render_metadata(self) -> str:
        """Render metadata view."""
        if not self.customization:
            return "[dim italic]Select a customization[/]"

        c = self.customization
        lines = [
            f"[bold]{c.name}[/]",
            "",
            f"[dim]Type:[/] {c.type_label}",
            f"[dim]Level:[/] {c.level_label}",
            f"[dim]Path:[/] {c.path}",
        ]
        if c.description:
            lines.append(f"[dim]Description:[/] {c.description}")
        if c.has_error:
            lines.append("")
            lines.append(f"[red]Error:[/] {c.error}")
        return "\n".join(lines)

    def _get_syntax_theme(self) -> str:
        """Get Pygments theme based on current app theme."""
        app_theme = self.app.theme or "textual-dark"
        return TEXTUAL_TO_PYGMENTS_THEME.get(app_theme, DEFAULT_SYNTAX_THEME)

    def _extract_frontmatter_text(self, content: str) -> tuple[str | None, str]:
        """Extract raw frontmatter text and body from markdown content."""
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, content

    def _render_markdown_with_frontmatter(self, content: str) -> RenderableType:
        """Render markdown with separate frontmatter highlighting."""
        theme = self._get_syntax_theme()
        frontmatter_text, body = self._extract_frontmatter_text(content)

        if frontmatter_text:
            parts: list[RenderableType] = [
                Syntax(frontmatter_text, "yaml", theme=theme, word_wrap=True),
                "",
                Syntax(body, "markdown", theme=theme, word_wrap=True),
            ]
            return Group(*parts)

        return Syntax(content, "markdown", theme=theme, word_wrap=True)

    def _render_file_content(self) -> RenderableType:
        """Render file content view with syntax highlighting."""
        if not self.customization:
            return "[dim italic]No content to display[/]"
        if self.customization.has_error:
            return f"[red]Error:[/] {self.customization.error}"
        content = self.customization.content
        if not content:
            return "[dim italic]Empty[/]"

        suffix = self.customization.path.suffix.lower()
        if suffix == ".md":
            return self._render_markdown_with_frontmatter(content)

        lexer_map = {".json": "json"}
        lexer = lexer_map.get(suffix, "text")

        return Syntax(content, lexer, theme=self._get_syntax_theme(), line_numbers=True, word_wrap=True)

    def on_mount(self) -> None:
        """Handle mount event."""
        self._update_title()
        self.border_subtitle = self._render_footer()
        self.watch(self.app, "theme", self._on_theme_changed)

    def _on_theme_changed(self) -> None:
        """Handle app theme changes."""
        self._refresh_display()

    def _update_title(self) -> None:
        """Update border title based on view mode."""
        accent = self.app.get_css_variables().get("accent", "cyan")
        if self.view_mode == "content":
            tabs = f"[bold {accent}]Content[/] - Metadata"
        else:
            tabs = f"Content - [bold {accent}]Metadata[/]"
        self.border_title = f"[0]-{tabs}-"

    def _render_footer(self) -> str:
        """Render the panel footer with file path."""
        if not self.customization:
            return ""
        return str(self.customization.path)

    def watch_view_mode(self, mode: str) -> None:  # noqa: ARG002
        """React to view mode changes."""
        self._update_title()
        self._refresh_display()

    def watch_customization(
        self, customization: Customization | None  # noqa: ARG002
    ) -> None:
        """React to customization changes."""
        self.border_subtitle = self._render_footer()
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the pane display."""
        try:
            content = self.query_one(".pane-content", Static)
            content.update(self._render_content())
        except Exception:
            pass

    def action_next_view(self) -> None:
        """Switch to next view."""
        self.view_mode = "metadata" if self.view_mode == "content" else "content"

    def action_prev_view(self) -> None:
        """Switch to previous view."""
        self.view_mode = "content" if self.view_mode == "metadata" else "metadata"

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
