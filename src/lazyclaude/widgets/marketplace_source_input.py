"""Input widget for entering marketplace source with suggestions."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Key
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static

KNOWN_MARKETPLACES = [
    ("anthropics/claude-plugins-official", "Anthropic Plugins"),
    ("NikiforovAll/claude-code-rules", "cc-handbook"),
]

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
        Binding("escape", "cancel", "Cancel", show=False, priority=True),
        Binding("enter", "submit", "Submit", show=False, priority=True),
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

    def compose(self) -> ComposeResult:
        """Compose the source input with suggestions."""
        self._input = NavigableInput(
            placeholder="Enter source (owner/repo, URL, or path) or select below..."
        )
        yield self._input

        with Vertical(id="suggestions"):
            yield Static("Known marketplaces:", id="suggestions-label")
            for i, (source, display_name) in enumerate(KNOWN_MARKETPLACES):
                option = Static(
                    f"  {display_name} [dim]({source})[/]",
                    classes="option",
                    id=f"option-{i}",
                )
                self._options.append(option)
                yield option

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
        elif event.key == "enter":
            self.action_submit()
            event.stop()
            event.prevent_default()

    def action_move_down(self) -> None:
        """Move selection down."""
        if self._selected_index < len(KNOWN_MARKETPLACES) - 1:
            self._selected_index += 1
            self._update_selection()

    def action_move_up(self) -> None:
        """Move selection up."""
        if self._selected_index > -1:
            self._selected_index -= 1
            self._update_selection()

    def action_cancel(self) -> None:
        """Cancel and close."""
        self.clear()
        self.hide()
        self.post_message(self.SourceCancelled())

    def action_submit(self) -> None:
        """Submit selected option or typed value."""
        if self._selected_index >= 0:
            source, _ = KNOWN_MARKETPLACES[self._selected_index]
            self._submit_source(source)
        elif self._input:
            source = self._input.value.strip()
            if source:
                self._submit_source(source)

    def _submit_source(self, source: str) -> None:
        """Submit the selected source."""
        self.hide()
        self.post_message(self.SourceSubmitted(source))

    def _update_selection(self) -> None:
        """Update the visual selection indicator."""
        for i, option in enumerate(self._options):
            source, display_name = KNOWN_MARKETPLACES[i]
            if i == self._selected_index:
                option.update(f"> {display_name} [dim]({source})[/]")
                option.add_class("option-selected")
            else:
                option.update(f"  {display_name} [dim]({source})[/]")
                option.remove_class("option-selected")

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
