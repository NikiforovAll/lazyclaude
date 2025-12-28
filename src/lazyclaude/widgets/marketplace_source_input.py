"""Input widget for entering marketplace source with suggestions."""

import webbrowser
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Key
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static

NAVIGATION_KEYS = {"up", "down", "escape", "j", "k"}


class NavigableInput(Input):
    """Input that passes navigation keys to parent."""

    async def _on_key(self, event: Key) -> None:
        if event.key in NAVIGATION_KEYS:
            return
        if event.key == "enter":
            return
        await super()._on_key(event)


class MarketplaceSourceInput(Widget):
    """Input field for marketplace source with always-visible suggestions."""

    BINDINGS = [
        Binding("down", "move_down", "Down", show=False, priority=True),
        Binding("up", "move_up", "Up", show=False, priority=True),
        Binding("j", "move_down", "Down", show=False, priority=True),
        Binding("k", "move_up", "Up", show=False, priority=True),
        Binding("o", "open_in_browser", "Open", show=False, priority=True),
        Binding("escape", "cancel", "Cancel", show=False, priority=True),
    ]

    DEFAULT_CSS = """
    MarketplaceSourceInput {
        dock: bottom;
        layer: overlay;
        height: auto;
        border: solid $accent;
        padding: 0 1;
        display: none;
        background: $surface;
    }

    MarketplaceSourceInput.visible {
        display: block;
    }

    MarketplaceSourceInput:focus-within,
    MarketplaceSourceInput:focus {
        border: double $accent;
    }

    MarketplaceSourceInput Input {
        width: 100%;
        margin-bottom: 0;
    }

    MarketplaceSourceInput #suggestions {
        margin-top: 1;
        height: auto;
    }

    MarketplaceSourceInput #suggestions-label {
        color: $text-muted;
        margin-bottom: 0;
    }

    MarketplaceSourceInput .option {
        padding: 0 1;
    }

    MarketplaceSourceInput .option-selected {
        background: $accent;
        color: $text;
    }

    MarketplaceSourceInput #source-footer {
        width: 100%;
        margin-top: 1;
        border-top: solid $primary;
        text-align: center;
    }
    """

    can_focus = True

    class SourceSubmitted(Message):
        """Emitted when source is submitted."""

        def __init__(self, source: str) -> None:
            self.source = source
            super().__init__()

    class SourceCancelled(Message):
        """Emitted when input is cancelled."""

        pass

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize MarketplaceSourceInput."""
        super().__init__(name=name, id=id, classes=classes)
        self._input: Input | None = None
        self._selected_index: int = -1  # -1 = input focused, 0+ = option selected
        self._options: list[Static] = []
        self._suggestions: dict[str, dict[str, Any]] = {}
        self._suggestion_items: list[tuple[str, list[str], int]] = []

    def compose(self) -> ComposeResult:
        """Compose the source input with suggestions."""
        self._input = NavigableInput(
            placeholder="Enter source (owner/repo, URL, or path) or select below..."
        )
        yield self._input

        with Vertical(id="suggestions"):
            yield Static("Popular Marketplaces:", id="suggestions-label")
            for i, (repo, tags, stars) in enumerate(self._suggestion_items):
                option = Static(
                    self._format_option(repo, tags, stars, selected=False),
                    classes="option",
                    id=f"option-{i}",
                )
                self._options.append(option)
                yield option

        sep = "[dim]│[/]"
        yield Static(
            f"[bold]Enter[/] Add  [bold]o[/] Open  {sep}  "
            f"[bold]j/k[/] Navigate  {sep}  [bold]Esc[/] Cancel",
            id="source-footer",
        )

    def on_key(self, event: Key) -> None:
        """Handle navigation keys that pass through from NavigableInput."""
        if event.key in NAVIGATION_KEYS:
            if event.key == "down" or event.key == "j":
                self.action_move_down()
            elif event.key == "up" or event.key == "k":
                self.action_move_up()
            elif event.key == "escape":
                self.action_cancel()
            event.stop()
            event.prevent_default()
        elif event.key == "o":
            self.action_open_in_browser()
            event.stop()
            event.prevent_default()
        elif event.key == "enter":
            self.action_submit()
            event.stop()
            event.prevent_default()

    def action_move_down(self) -> None:
        """Move selection down, cycling to input when at end."""
        if self._selected_index >= len(self._suggestion_items) - 1:
            self._selected_index = -1
        else:
            self._selected_index += 1
        self._update_selection()

    def action_move_up(self) -> None:
        """Move selection up, cycling to last option when at input."""
        if self._selected_index <= -1:
            self._selected_index = len(self._suggestion_items) - 1
        else:
            self._selected_index -= 1
        self._update_selection()

    def action_cancel(self) -> None:
        """Cancel and close."""
        self.clear()
        self.hide()
        self.post_message(self.SourceCancelled())

    def action_open_in_browser(self) -> None:
        """Open the selected marketplace in browser."""
        if self._selected_index >= 0 and self._selected_index < len(
            self._suggestion_items
        ):
            repo, _, _ = self._suggestion_items[self._selected_index]
            url = f"https://github.com/{repo}"
            webbrowser.open(url)

    def action_submit(self) -> None:
        """Submit selected option or typed value."""
        if self._selected_index >= 0 and self._selected_index < len(
            self._suggestion_items
        ):
            repo, _, _ = self._suggestion_items[self._selected_index]
            self._submit_source(repo)
        elif self._input:
            source = self._input.value.strip()
            if source:
                self._submit_source(source)

    def _submit_source(self, source: str) -> None:
        """Submit the selected source."""
        self.hide()
        self.post_message(self.SourceSubmitted(source))

    def _format_option(
        self, repo: str, tags: list[str], stars: int, selected: bool
    ) -> str:
        """Format an option for display."""
        prefix = "> " if selected else "  "
        stars_str = f" [yellow]⭐{stars}[/]" if stars else ""
        tags_str = f" [dim]\\[{', '.join(tags)}][/]" if tags else ""
        return f"{prefix}{repo}{stars_str}{tags_str}"

    def _update_selection(self) -> None:
        """Update the visual selection indicator."""
        for i, option in enumerate(self._options):
            if i >= len(self._suggestion_items):
                continue
            repo, tags, stars = self._suggestion_items[i]
            selected = i == self._selected_index
            option.update(self._format_option(repo, tags, stars, selected))
            if selected:
                option.add_class("option-selected")
            else:
                option.remove_class("option-selected")

        if self._selected_index >= 0 and self._input:
            self._input.blur()
            self.focus()
        elif self._selected_index == -1 and self._input:
            self._input.focus()

    def show(self) -> None:
        """Show the input and focus it."""
        self._selected_index = -1
        self._update_selection()
        self.add_class("visible")
        self.call_after_refresh(self._do_focus)

    def _do_focus(self) -> None:
        """Focus the input after widget is visible."""
        if self._input:
            self._input.focus()

    def hide(self) -> None:
        """Hide the input."""
        self.remove_class("visible")

    def clear(self) -> None:
        """Clear the input value."""
        if self._input:
            self._input.value = ""
        self._selected_index = -1
        self._update_selection()

    @property
    def is_visible(self) -> bool:
        """Check if the input is visible."""
        return self.has_class("visible")

    def set_suggestions(self, suggestions: dict[str, dict[str, Any]]) -> None:
        """Set the marketplace suggestions from settings.

        Handles any format gracefully - extracts tags/stars if present.
        Orders: anthropics first, handbook second, rest by stars descending.
        """
        self._suggestions = suggestions
        self._suggestion_items = []
        for repo, data in suggestions.items():
            if not isinstance(data, dict):
                data = {}
            tags = data.get("tags", [])
            if not isinstance(tags, list):
                tags = []
            stars = data.get("stars", 0)
            if not isinstance(stars, int):
                stars = 0
            self._suggestion_items.append((repo, tags, stars))
        self._suggestion_items = self._sort_suggestions(self._suggestion_items)
        self._rebuild_options()

    def _sort_suggestions(
        self, items: list[tuple[str, list[str], int]]
    ) -> list[tuple[str, list[str], int]]:
        """Sort suggestions: anthropics first, handbook second, rest by stars."""
        pinned_first = "anthropics/claude-plugins-official"
        pinned_second = "NikiforovAll/claude-code-rules"

        first = [i for i in items if i[0] == pinned_first]
        second = [i for i in items if i[0] == pinned_second]
        rest = [i for i in items if i[0] not in (pinned_first, pinned_second)]
        rest.sort(key=lambda x: x[2], reverse=True)

        return first + second + rest

    def _rebuild_options(self) -> None:
        """Rebuild option widgets when suggestions change."""
        try:
            suggestions_container = self.query_one("#suggestions", Vertical)
        except Exception:
            return

        for option in self._options:
            option.remove()
        self._options.clear()

        for i, (repo, tags, stars) in enumerate(self._suggestion_items):
            option = Static(
                self._format_option(repo, tags, stars, selected=False),
                classes="option",
                id=f"option-{i}",
            )
            self._options.append(option)
            suggestions_container.mount(option)

        self._selected_index = -1
