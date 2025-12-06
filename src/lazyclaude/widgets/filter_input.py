"""FilterInput widget for searching customizations."""

from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input


class FilterInput(Widget):
    """Search/filter input field."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    FilterInput {
        dock: bottom;
        height: 3;
        border: solid $accent;
        padding: 0 1;
        display: none;
    }

    FilterInput.visible {
        display: block;
    }

    FilterInput:focus-within {
        border: double $accent;
    }

    FilterInput Input {
        width: 100%;
    }
    """

    query: reactive[str] = reactive("")

    class FilterChanged(Message):
        """Emitted when filter query changes."""

        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    class FilterCancelled(Message):
        """Emitted when filter is cancelled."""

        pass

    class FilterApplied(Message):
        """Emitted when filter is applied."""

        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize FilterInput."""
        super().__init__(name=name, id=id, classes=classes)
        self._input: Input | None = None

    def compose(self):
        """Compose the filter input."""
        self._input = Input(placeholder="Filter by name...")
        yield self._input

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        self.query = event.value
        self.post_message(self.FilterChanged(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        self.post_message(self.FilterApplied(event.value))

    def action_cancel(self) -> None:
        """Cancel filtering."""
        self.clear()
        self.hide()
        self.post_message(self.FilterCancelled())

    def show(self) -> None:
        """Show the filter input and focus it."""
        self.add_class("visible")
        if self._input:
            self._input.focus()

    def hide(self) -> None:
        """Hide the filter input."""
        self.remove_class("visible")

    def clear(self) -> None:
        """Clear the filter query."""
        if self._input:
            self._input.value = ""
        self.query = ""

    @property
    def is_visible(self) -> bool:
        """Check if the filter input is visible."""
        return self.has_class("visible")
