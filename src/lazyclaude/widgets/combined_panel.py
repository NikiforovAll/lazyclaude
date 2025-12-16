"""CombinedPanel widget for displaying multiple types in a tabbed view."""

from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.dom import DOMNode
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

if TYPE_CHECKING:
    from lazyclaude.app import LazyClaude

from lazyclaude.models.customization import Customization, CustomizationType


class CombinedPanel(Widget):
    """Panel displaying multiple customization types with tab switching."""

    COMBINED_TYPES = [
        CustomizationType.MEMORY_FILE,
        CustomizationType.MCP,
        CustomizationType.HOOK,
    ]

    TYPE_LABELS = {
        CustomizationType.MEMORY_FILE: ("[4]", "Memory"),
        CustomizationType.MCP: ("[5]", "MCPs"),
        CustomizationType.HOOK: ("[6]", "Hooks"),
    }

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
        Binding("escape", "back", "Back", show=False),
        Binding("[", "prev_tab", "Prev Tab", show=False),
        Binding("]", "next_tab", "Next Tab", show=False),
    ]

    DEFAULT_CSS = """
    CombinedPanel {
        height: 1fr;
        min-height: 3;
        border: solid $primary;
        padding: 0 1;
        border-title-align: left;
    }

    CombinedPanel:focus {
        border: double $accent;
    }

    CombinedPanel .items-container {
        height: auto;
    }

    CombinedPanel .item {
        height: 1;
        width: 100%;
    }

    CombinedPanel .item-selected {
        background: $accent;
        text-style: bold;
    }

    CombinedPanel .item-error {
        color: $error;
    }

    CombinedPanel .empty-message {
        color: $text-muted;
        text-style: italic;
    }
    """

    active_type: reactive[CustomizationType] = reactive(CustomizationType.MEMORY_FILE)
    customizations: reactive[list[Customization]] = reactive(list, always_update=True)
    selected_index: reactive[int] = reactive(0)
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
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize CombinedPanel."""
        super().__init__(name=name, id=id, classes=classes)
        self.can_focus = True
        self._selected_indices: dict[CustomizationType, int] = dict.fromkeys(
            self.COMBINED_TYPES, 0
        )

    @property
    def _filtered_customizations(self) -> list[Customization]:
        """Get customizations filtered by active type."""
        return [c for c in self.customizations if c.type == self.active_type]

    @property
    def selected_customization(self) -> Customization | None:
        """Get the currently selected customization."""
        filtered = self._filtered_customizations
        if filtered and 0 <= self.selected_index < len(filtered):
            return filtered[self.selected_index]
        return None

    def compose(self) -> ComposeResult:
        """Compose the panel content."""
        with VerticalScroll(classes="items-container"):
            filtered = self._filtered_customizations
            if not filtered:
                yield Static("[dim italic]No items[/]", classes="empty-message")
            else:
                for i, item in enumerate(filtered):
                    yield Static(
                        self._render_item(i, item), classes="item", id=f"item-{i}"
                    )

    def _render_header(self) -> str:
        """Render the tab-style header."""
        parts = []
        for ctype in self.COMBINED_TYPES:
            num, label = self.TYPE_LABELS[ctype]
            if ctype == self.active_type:
                parts.append(f"{num}-{label}")
            else:
                parts.append(f"[dim]{num}-{label}[/]")
        return " | ".join(parts)

    def _render_footer(self) -> str:
        """Render the panel footer with selection position."""
        count = len(self._filtered_customizations)
        if count == 0:
            return "0 of 0"
        return f"{self.selected_index + 1} of {count}"

    def _render_item(self, index: int, item: Customization) -> str:
        """Render a single item."""
        is_selected = index == self.selected_index and self.is_active
        prefix = ">" if is_selected else " "
        error_marker = " [red]![/]" if item.has_error else ""
        return f"{prefix} {item.display_name}{error_marker}"

    def watch_active_type(
        self, old_type: CustomizationType, new_type: CustomizationType
    ) -> None:
        """React to active type changes."""
        self._selected_indices[old_type] = self.selected_index
        restored_index = self._selected_indices.get(new_type, 0)
        filtered = [c for c in self.customizations if c.type == new_type]
        if filtered and restored_index >= len(filtered):
            restored_index = len(filtered) - 1
        elif not filtered:
            restored_index = 0
        self.selected_index = restored_index
        if self.is_mounted:
            self.border_title = self._render_header()
            self.border_subtitle = self._render_footer()
            self.call_later(self._rebuild_items)
            if self.is_active:
                self._emit_selection_message()

    def watch_customizations(self, customizations: list[Customization]) -> None:  # noqa: ARG002
        """React to customizations list changes."""
        filtered = self._filtered_customizations
        if self.selected_index >= len(filtered):
            self.selected_index = max(0, len(filtered) - 1)

        if self.is_mounted:
            self.border_title = self._render_header()
            self.border_subtitle = self._render_footer()
            self.call_later(self._rebuild_items)
            if self.is_active:
                self._emit_selection_message()

    def watch_selected_index(self, index: int) -> None:  # noqa: ARG002
        """React to selected index changes."""
        if self.is_mounted:
            self.border_subtitle = self._render_footer()
        self._refresh_display()
        self._scroll_to_selection()
        self._emit_selection_message()

    async def _rebuild_items(self) -> None:
        """Rebuild item widgets when customizations change."""
        if not self.is_mounted:
            return
        container = self.query_one(".items-container", VerticalScroll)
        await container.remove_children()

        filtered = self._filtered_customizations
        if not filtered:
            await container.mount(
                Static("[dim italic]No items[/]", classes="empty-message")
            )
        else:
            for i, item in enumerate(filtered):
                is_selected = i == self.selected_index and self.is_active
                classes = "item item-selected" if is_selected else "item"
                await container.mount(
                    Static(self._render_item(i, item), classes=classes, id=f"item-{i}")
                )

        container.scroll_home(animate=False)
        self._update_empty_state()

    def on_mount(self) -> None:
        """Handle mount event."""
        self.border_title = self._render_header()
        self.border_subtitle = self._render_footer()
        if self.customizations:
            self.call_later(self._rebuild_items)

    def _refresh_display(self) -> None:
        """Refresh the panel display (updates existing widgets)."""
        try:
            items = list(self.query("Static.item"))
            filtered = self._filtered_customizations
            for i, (item_widget, item) in enumerate(zip(items, filtered, strict=False)):
                if isinstance(item_widget, Static):
                    item_widget.update(self._render_item(i, item))
                is_selected = i == self.selected_index and self.is_active
                item_widget.set_class(is_selected, "item-selected")
        except Exception:
            pass

    def _scroll_to_selection(self) -> None:
        """Scroll to keep the selected item visible."""
        filtered = self._filtered_customizations
        if not filtered:
            return
        try:
            items = list(self.query(".item"))
            if 0 <= self.selected_index < len(items):
                items[self.selected_index].scroll_visible(animate=False)
        except Exception:
            pass

    def on_click(self, event: Click) -> None:
        """Handle click - select clicked item and focus panel."""
        self.focus()

        try:
            clicked_widget, _ = self.screen.get_widget_at(
                event.screen_x, event.screen_y
            )
        except Exception:
            return

        current: DOMNode | None = clicked_widget
        while current is not None and current is not self:
            if current.id and current.id.startswith("item-"):
                try:
                    index = int(current.id.split("-")[1])
                    item_count = len(self._filtered_customizations)
                    if 0 <= index < item_count:
                        self.selected_index = index
                except ValueError:
                    pass
                break
            current = current.parent

    def on_focus(self) -> None:
        """Handle focus event."""
        self.is_active = True
        self._refresh_display()
        self._emit_selection_message()

    def on_blur(self) -> None:
        """Handle blur event."""
        self.is_active = False
        self._refresh_display()

    def action_cursor_down(self) -> None:
        """Move selection down."""
        count = len(self._filtered_customizations)
        if count > 0 and self.selected_index < count - 1:
            self.selected_index += 1

    def action_cursor_up(self) -> None:
        """Move selection up."""
        count = len(self._filtered_customizations)
        if count > 0 and self.selected_index > 0:
            self.selected_index -= 1

    def action_cursor_top(self) -> None:
        """Move selection to top."""
        if self._filtered_customizations:
            self.selected_index = 0

    def action_cursor_bottom(self) -> None:
        """Move selection to bottom."""
        count = len(self._filtered_customizations)
        if count > 0:
            self.selected_index = count - 1

    def action_select(self) -> None:
        """Drill down into selected customization."""
        if self.selected_customization:
            self.post_message(self.DrillDown(self.selected_customization))

    def action_prev_tab(self) -> None:
        """Switch to previous tab."""
        current_idx = self.COMBINED_TYPES.index(self.active_type)
        new_idx = (current_idx - 1) % len(self.COMBINED_TYPES)
        self.active_type = self.COMBINED_TYPES[new_idx]

    def action_next_tab(self) -> None:
        """Switch to next tab."""
        current_idx = self.COMBINED_TYPES.index(self.active_type)
        new_idx = (current_idx + 1) % len(self.COMBINED_TYPES)
        self.active_type = self.COMBINED_TYPES[new_idx]

    def switch_to_type(self, ctype: CustomizationType) -> None:
        """Switch to a specific type."""
        if ctype in self.COMBINED_TYPES:
            self.active_type = ctype

    def action_focus_next_panel(self) -> None:
        """Delegate to app's focus_next_panel action."""
        cast("LazyClaude", self.app).action_focus_next_panel()

    def action_focus_previous_panel(self) -> None:
        """Delegate to app's focus_previous_panel action."""
        cast("LazyClaude", self.app).action_focus_previous_panel()

    async def action_back(self) -> None:
        """Delegate to app's back action."""
        await cast("LazyClaude", self.app).action_back()

    def set_customizations(self, customizations: list[Customization]) -> None:
        """Set the customizations for this panel (all types, filtering done internally)."""
        filtered = [c for c in customizations if c.type in self.COMBINED_TYPES]
        self.customizations = filtered
        self._update_empty_state()

    def _update_empty_state(self) -> None:
        """Toggle empty class based on item count."""
        if len(self._filtered_customizations) == 0:
            self.add_class("empty")
        else:
            self.remove_class("empty")

    def _emit_selection_message(self) -> None:
        """Emit selection message based on current selection."""
        self.post_message(self.SelectionChanged(self.selected_customization))
