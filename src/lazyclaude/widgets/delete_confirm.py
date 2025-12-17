"""Confirmation widget for delete operations."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from lazyclaude.models.customization import Customization


class DeleteConfirm(Widget):
    """Bottom bar for confirming delete operations."""

    BINDINGS = [
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "deny", "No", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    DeleteConfirm {
        dock: bottom;
        height: 4;
        border: solid $error;
        padding: 0 1;
        margin-bottom: 1;
        display: none;
        background: $surface;
    }

    DeleteConfirm.visible {
        display: block;
    }

    DeleteConfirm:focus {
        border: double $error;
    }

    DeleteConfirm #prompt {
        width: 100%;
        text-align: center;
    }
    """

    can_focus = True

    class DeleteConfirmed(Message):
        """Emitted when delete is confirmed."""

        def __init__(self, customization: Customization) -> None:
            self.customization = customization
            super().__init__()

    class DeleteCancelled(Message):
        """Emitted when delete is cancelled."""

        pass

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize DeleteConfirm."""
        super().__init__(name=name, id=id, classes=classes)
        self._customization: Customization | None = None

    def compose(self) -> ComposeResult:
        """Compose the confirmation bar."""
        yield Static("", id="prompt")

    def show(self, customization: Customization) -> None:
        """Show the confirmation bar and focus it."""
        self._customization = customization
        self._update_prompt(customization)
        self.add_class("visible")
        self.focus()

    def hide(self) -> None:
        """Hide the confirmation bar."""
        self.remove_class("visible")
        self._customization = None

    def _update_prompt(self, customization: Customization) -> None:
        """Update the prompt text."""
        prompt_widget = self.query_one("#prompt", Static)
        error_color = self.app.get_css_variables().get("error", "red")
        prompt_widget.update(
            f'Delete [{error_color}]"{customization.name}"[/] ({customization.type_label})?\n'
            "\\[y] Yes  \\[n] No  \\[Esc] Cancel"
        )

    def action_confirm(self) -> None:
        """Confirm the delete."""
        if self._customization:
            customization = self._customization
            self.hide()
            self.post_message(self.DeleteConfirmed(customization))

    def action_deny(self) -> None:
        """Deny the delete."""
        self.hide()
        self.post_message(self.DeleteCancelled())

    def action_cancel(self) -> None:
        """Cancel the delete."""
        self.hide()
        self.post_message(self.DeleteCancelled())

    @property
    def is_visible(self) -> bool:
        """Check if the confirmation bar is visible."""
        return self.has_class("visible")
