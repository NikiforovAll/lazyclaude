"""Confirmation widget for plugin toggle operations."""

from collections import Counter

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from lazyclaude.models.customization import Customization, CustomizationType, PluginInfo


class PluginConfirm(Widget):
    """Bottom bar for confirming plugin toggle operations."""

    BINDINGS = [
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "deny", "No", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    PluginConfirm {
        dock: bottom;
        height: 5;
        border: solid $accent;
        padding: 0 1;
        margin-bottom: 1;
        display: none;
        background: $surface;
    }

    PluginConfirm.visible {
        display: block;
    }

    PluginConfirm:focus {
        border: double $accent;
    }

    PluginConfirm #prompt {
        width: 100%;
        text-align: center;
    }
    """

    can_focus = True

    class PluginConfirmed(Message):
        """Emitted when plugin toggle is confirmed."""

        def __init__(self, plugin_info: PluginInfo) -> None:
            self.plugin_info = plugin_info
            super().__init__()

    class ConfirmationCancelled(Message):
        """Emitted when confirmation is cancelled."""

        pass

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize PluginConfirm."""
        super().__init__(name=name, id=id, classes=classes)
        self._plugin_info: PluginInfo | None = None

    def compose(self) -> ComposeResult:
        """Compose the confirmation bar."""
        yield Static("", id="prompt")

    def show(
        self, plugin_info: PluginInfo, customizations: list[Customization]
    ) -> None:
        """Show the confirmation bar and focus it."""
        self._plugin_info = plugin_info
        summary = self._build_summary(plugin_info, customizations)
        self._update_prompt(summary)
        self.add_class("visible")
        self.focus()

    def hide(self) -> None:
        """Hide the confirmation bar."""
        self.remove_class("visible")
        self._plugin_info = None

    def _build_summary(
        self, plugin_info: PluginInfo, customizations: list[Customization]
    ) -> str:
        """Build summary of affected customizations."""
        plugin_items = [
            c
            for c in customizations
            if c.plugin_info and c.plugin_info.plugin_id == plugin_info.plugin_id
        ]

        type_counts = Counter(c.type for c in plugin_items)

        type_labels = {
            CustomizationType.SLASH_COMMAND: "Commands",
            CustomizationType.SUBAGENT: "Agents",
            CustomizationType.SKILL: "Skills",
            CustomizationType.MEMORY_FILE: "Memory Files",
            CustomizationType.MCP: "MCPs",
            CustomizationType.HOOK: "Hooks",
        }

        if not type_counts:
            summary = "(0) items"
        else:
            parts = [
                f"({count}) {type_labels[t]}"
                for t, count in sorted(type_counts.items(), key=lambda x: x[0].value)
            ]
            summary = ", ".join(parts)

        accent = self.app.get_css_variables().get("accent", "cyan")
        action = "Enable" if not plugin_info.is_enabled else "Disable"
        return f"{action} [bold {accent}]{plugin_info.short_name}[/] plugin? Affects: {summary}"

    def _update_prompt(self, summary: str) -> None:
        """Update the prompt text."""
        prompt_widget = self.query_one("#prompt", Static)
        prompt_widget.update(f"{summary}\n\n\\[y] Yes  \\[n] No  Cancel")

    def action_confirm(self) -> None:
        """Confirm the toggle."""
        if self._plugin_info:
            plugin_info = self._plugin_info
            self.hide()
            self.post_message(self.PluginConfirmed(plugin_info))

    def action_deny(self) -> None:
        """Deny the toggle."""
        self.hide()
        self.post_message(self.ConfirmationCancelled())

    def action_cancel(self) -> None:
        """Cancel the toggle."""
        self.hide()
        self.post_message(self.ConfirmationCancelled())

    @property
    def is_visible(self) -> bool:
        """Check if the confirmation bar is visible."""
        return self.has_class("visible")
