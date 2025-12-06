"""TypePanel widget for displaying customizations of a single type."""

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from lazyclaude.models.customization import Customization, CustomizationType


class TypePanel(Widget):
    """Panel displaying customizations of a single type."""

    BINDINGS = [
        Binding("tab", "focus_next_panel", "Next Panel", show=False),
        Binding("shift+tab", "focus_previous_panel", "Prev Panel", show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("g", "cursor_top", "Top", show=False),
        Binding("G", "cursor_bottom", "Bottom", show=False, key_display="shift+g"),
        Binding("enter", "select", "Select", show=False),
    ]

    DEFAULT_CSS = """
    TypePanel {
        height: auto;
        min-height: 3;
        max-height: 12;
        border: solid $primary;
        padding: 0 1;
        border-title-align: left;
    }

    TypePanel:focus {
        border: double $accent;
    }

    TypePanel .items-container {
        height: auto;
    }

    TypePanel .item {
        height: 1;
        width: 100%;
    }

    TypePanel .item-selected {
        background: $accent;
        text-style: bold;
    }

    TypePanel .item-error {
        color: $error;
    }

    TypePanel .empty-message {
        color: $text-muted;
        text-style: italic;
    }
    """

    customization_type: reactive[CustomizationType] = reactive(
        CustomizationType.SLASH_COMMAND
    )
    customizations: reactive[list[Customization]] = reactive(list, always_update=True)
    selected_index: reactive[int] = reactive(0)
    panel_number: reactive[int] = reactive(1)
    is_active: reactive[bool] = reactive(False)

    class SelectionChanged(Message):
        """Emitted when selected customization changes."""

        def __init__(self, customization: Customization | None) -> None:
            self.customization = customization
            super().__init__()

    class DrillDown(Message):
        """Emitted when user drills into a customization."""

        def __init__(self, customization: Customization) -> None:
            self.customization = customization
            super().__init__()

    def __init__(
        self,
        customization_type: CustomizationType,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize TypePanel with a customization type."""
        super().__init__(name=name, id=id, classes=classes)
        self.customization_type = customization_type
        self.can_focus = True

    @property
    def type_label(self) -> str:
        """Get human-readable type label."""
        return {
            CustomizationType.SLASH_COMMAND: "Slash Commands",
            CustomizationType.SUBAGENT: "Subagents",
            CustomizationType.SKILL: "Skills",
            CustomizationType.MEMORY_FILE: "Memory Files",
            CustomizationType.MCP: "MCPs",
        }[self.customization_type]

    @property
    def selected_customization(self) -> Customization | None:
        """Get the currently selected customization."""
        if self.customizations and 0 <= self.selected_index < len(self.customizations):
            return self.customizations[self.selected_index]
        return None

    def compose(self):
        """Compose the panel content."""
        with VerticalScroll(classes="items-container"):
            if not self.customizations:
                yield Static("[dim italic]No items[/]", classes="empty-message")
            else:
                for i, item in enumerate(self.customizations):
                    yield Static(self._render_item(i, item), classes="item", id=f"item-{i}")

    def _render_header(self) -> str:
        """Render the panel header with type and count."""
        count = len(self.customizations)
        return f"[{self.panel_number}]-{self.type_label} ({count})-"

    def _render_item(self, index: int, item: Customization) -> str:
        """Render a single item."""
        is_selected = index == self.selected_index and self.is_active
        prefix = ">" if is_selected else " "
        error_marker = " [red]![/]" if item.has_error else ""
        return f"{prefix} {item.display_name}{error_marker}"

    def watch_customizations(self, customizations: list[Customization]) -> None:
        """React to customizations list changes."""
        if self.selected_index >= len(customizations):
            self.selected_index = max(0, len(customizations) - 1)
        if self.is_mounted:
            self.border_title = self._render_header()
            self.call_later(self._rebuild_items)
            if self.is_active:
                self.post_message(self.SelectionChanged(self.selected_customization))

    def watch_selected_index(self, index: int) -> None:  # noqa: ARG002
        """React to selected index changes."""
        self._refresh_display()
        self._scroll_to_selection()
        self.post_message(self.SelectionChanged(self.selected_customization))

    async def _rebuild_items(self) -> None:
        """Rebuild item widgets when customizations change."""
        if not self.is_mounted:
            return
        container = self.query_one(".items-container", VerticalScroll)
        await container.remove_children()
        if not self.customizations:
            await container.mount(Static("[dim italic]No items[/]", classes="empty-message"))
        else:
            for i, item in enumerate(self.customizations):
                is_selected = i == self.selected_index and self.is_active
                classes = "item item-selected" if is_selected else "item"
                await container.mount(Static(self._render_item(i, item), classes=classes))
        container.scroll_home(animate=False)

    def on_mount(self) -> None:
        """Handle mount event - rebuild items if customizations were set before mount."""
        self.border_title = self._render_header()
        if self.customizations:
            self.call_later(self._rebuild_items)

    def _refresh_display(self) -> None:
        """Refresh the panel display (updates existing widgets)."""
        try:
            items = list(self.query(".item"))
            for i, (item_widget, item) in enumerate(zip(items, self.customizations, strict=False)):
                item_widget.update(self._render_item(i, item))
                is_selected = i == self.selected_index and self.is_active
                item_widget.set_class(is_selected, "item-selected")
        except Exception:
            pass

    def _scroll_to_selection(self) -> None:
        """Scroll to keep the selected item visible."""
        if not self.customizations:
            return
        try:
            items = list(self.query(".item"))
            if 0 <= self.selected_index < len(items):
                items[self.selected_index].scroll_visible(animate=False)
        except Exception:
            pass

    def on_click(self) -> None:
        """Handle click - focus this panel."""
        self.focus()

    def on_focus(self) -> None:
        """Handle focus event."""
        self.is_active = True
        self._refresh_display()
        self.post_message(self.SelectionChanged(self.selected_customization))

    def on_blur(self) -> None:
        """Handle blur event."""
        self.is_active = False
        self._refresh_display()

    def action_cursor_down(self) -> None:
        """Move selection down."""
        if self.customizations and self.selected_index < len(self.customizations) - 1:
            self.selected_index += 1

    def action_cursor_up(self) -> None:
        """Move selection up."""
        if self.customizations and self.selected_index > 0:
            self.selected_index -= 1

    def action_cursor_top(self) -> None:
        """Move selection to top."""
        if self.customizations:
            self.selected_index = 0

    def action_cursor_bottom(self) -> None:
        """Move selection to bottom."""
        if self.customizations:
            self.selected_index = len(self.customizations) - 1

    def action_select(self) -> None:
        """Drill down into selected customization."""
        if self.selected_customization:
            self.post_message(self.DrillDown(self.selected_customization))

    def action_focus_next_panel(self) -> None:
        """Delegate to app's focus_next_panel action."""
        self.app.action_focus_next_panel()

    def action_focus_previous_panel(self) -> None:
        """Delegate to app's focus_previous_panel action."""
        self.app.action_focus_previous_panel()

    def set_customizations(self, customizations: list[Customization]) -> None:
        """Set the customizations for this panel (filtered by type)."""
        filtered = [c for c in customizations if c.type == self.customization_type]
        self.customizations = filtered
