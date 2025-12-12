"""Level selector bar for copy/move operations."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from lazyclaude.models.customization import ConfigLevel


class LevelSelector(Widget):
    """Bottom bar for selecting target configuration level."""

    BINDINGS = [
        Binding("1", "select_user", "User", show=False),
        Binding("2", "select_project", "Project", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    LevelSelector {
        dock: bottom;
        height: 3;
        border: solid $accent;
        padding: 0 1;
        margin-bottom: 1;
        display: none;
        background: $surface;
    }

    LevelSelector.visible {
        display: block;
    }

    LevelSelector:focus {
        border: double $accent;
    }

    LevelSelector #prompt {
        width: 100%;
        text-align: center;
    }

    LevelSelector .key {
        color: $accent;
        text-style: bold;
    }
    """

    can_focus = True

    class LevelSelected(Message):
        """Emitted when a level is selected."""

        def __init__(self, level: ConfigLevel, operation: str) -> None:
            self.level = level
            self.operation = operation
            super().__init__()

    class SelectionCancelled(Message):
        """Emitted when selection is cancelled."""

        pass

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize LevelSelector."""
        super().__init__(name=name, id=id, classes=classes)
        self._operation: str = "copy"
        self._available_levels: list[ConfigLevel] = []

    def compose(self) -> ComposeResult:
        """Compose the level selector bar."""
        yield Static("", id="prompt")

    def show(
        self, available_levels: list[ConfigLevel], operation: str = "copy"
    ) -> None:
        """Show the level selector and focus it."""
        self._operation = operation
        self._available_levels = available_levels
        self._update_prompt()
        self.add_class("visible")
        self.focus()

    def hide(self) -> None:
        """Hide the level selector."""
        self.remove_class("visible")

    def _update_prompt(self) -> None:
        """Update the prompt text based on available levels."""
        op_label = "Copy" if self._operation == "copy" else "Move"

        options = []
        if ConfigLevel.USER in self._available_levels:
            options.append("[1] User")
        if ConfigLevel.PROJECT in self._available_levels:
            options.append("[2] Project")

        options_text = "  ".join(options)
        prompt_widget = self.query_one("#prompt", Static)
        prompt_widget.update(f"{op_label} to: {options_text}  \\[Esc] Cancel")

    def action_select_user(self) -> None:
        """Select user level."""
        if ConfigLevel.USER in self._available_levels:
            self.hide()
            self.post_message(self.LevelSelected(ConfigLevel.USER, self._operation))

    def action_select_project(self) -> None:
        """Select project level."""
        if ConfigLevel.PROJECT in self._available_levels:
            self.hide()
            self.post_message(self.LevelSelected(ConfigLevel.PROJECT, self._operation))

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.hide()
        self.post_message(self.SelectionCancelled())

    @property
    def is_visible(self) -> bool:
        """Check if the level selector is visible."""
        return self.has_class("visible")
