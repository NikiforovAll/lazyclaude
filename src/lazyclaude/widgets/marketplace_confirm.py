"""Confirmation widget for marketplace remove operations."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from lazyclaude.models.marketplace import Marketplace


class MarketplaceConfirm(Widget):
    """Bottom bar for confirming marketplace removal."""

    BINDINGS = [
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "deny", "No", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    MarketplaceConfirm {
        dock: bottom;
        layer: overlay;
        height: 4;
        border: solid $warning;
        padding: 0 1;
        margin-bottom: 1;
        display: none;
        background: $surface;
    }

    MarketplaceConfirm.visible {
        display: block;
    }

    MarketplaceConfirm:focus {
        border: double $warning;
    }

    MarketplaceConfirm #prompt {
        width: 100%;
        text-align: center;
    }
    """

    can_focus = True

    class RemoveConfirmed(Message):
        """Emitted when remove is confirmed."""

        def __init__(self, marketplace: Marketplace) -> None:
            self.marketplace = marketplace
            super().__init__()

    class RemoveCancelled(Message):
        """Emitted when remove is cancelled."""

        pass

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize MarketplaceConfirm."""
        super().__init__(name=name, id=id, classes=classes)
        self._marketplace: Marketplace | None = None

    def compose(self) -> ComposeResult:
        """Compose the confirmation bar."""
        yield Static("", id="prompt")

    def show(self, marketplace: Marketplace) -> None:
        """Show the confirmation bar and focus it."""
        self._marketplace = marketplace
        self._update_prompt(marketplace)
        self.add_class("visible")
        self.focus()

    def hide(self) -> None:
        """Hide the confirmation bar."""
        self.remove_class("visible")
        self._marketplace = None

    def _update_prompt(self, marketplace: Marketplace) -> None:
        """Update the prompt text."""
        prompt_widget = self.query_one("#prompt", Static)
        warning_color = self.app.get_css_variables().get("warning", "yellow")
        plugin_count = len(marketplace.plugins)
        plugins_text = f" ({plugin_count} plugins)" if plugin_count > 0 else ""
        prompt_widget.update(
            f'Remove marketplace [{warning_color}]"{marketplace.entry.name}"[/]{plugins_text}?\n'
            "\\[y] Yes  \\[n] No  \\[Esc] Cancel"
        )

    def action_confirm(self) -> None:
        """Confirm the removal."""
        if self._marketplace:
            marketplace = self._marketplace
            self.hide()
            self.post_message(self.RemoveConfirmed(marketplace))

    def action_deny(self) -> None:
        """Deny the removal."""
        self.hide()
        self.post_message(self.RemoveCancelled())

    def action_cancel(self) -> None:
        """Cancel the removal."""
        self.hide()
        self.post_message(self.RemoveCancelled())

    @property
    def is_visible(self) -> bool:
        """Check if the confirmation bar is visible."""
        return self.has_class("visible")
