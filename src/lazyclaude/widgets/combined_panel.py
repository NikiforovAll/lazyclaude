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

from lazyclaude.models.customization import (
    Customization,
    CustomizationType,
    MemoryFileRef,
)
from lazyclaude.widgets.helpers import build_memory_flat_items, render_memory_item


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
        Binding("right", "expand", "Expand", show=False),
        Binding("left", "collapse", "Collapse", show=False),
        Binding("l", "expand", "Expand", show=False),
        Binding("h", "collapse", "Collapse", show=False),
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

    class MemoryFileRefSelected(Message):
        """Emitted when a referenced file within a memory file is selected."""

        def __init__(
            self, customization: Customization, ref: MemoryFileRef | None
        ) -> None:
            self.customization = customization
            self.ref = ref
            super().__init__()

    expanded_memory_files: reactive[set[str]] = reactive(set, always_update=True)

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
        self._memory_flat_items: list[
            tuple[Customization, MemoryFileRef | None, int]
        ] = []

    @property
    def _is_memory_mode(self) -> bool:
        """Check if currently showing memory files."""
        return self.active_type == CustomizationType.MEMORY_FILE

    @property
    def _filtered_customizations(self) -> list[Customization]:
        """Get customizations filtered by active type."""
        return [c for c in self.customizations if c.type == self.active_type]

    def _item_count(self) -> int:
        """Get the number of items in the current view."""
        if self._is_memory_mode:
            return len(self._memory_flat_items)
        return len(self._filtered_customizations)

    @property
    def selected_customization(self) -> Customization | None:
        """Get the currently selected customization."""
        if self._is_memory_mode and self._memory_flat_items:
            if 0 <= self.selected_index < len(self._memory_flat_items):
                memory, _, _ = self._memory_flat_items[self.selected_index]
                return memory
            return None
        filtered = self._filtered_customizations
        if filtered and 0 <= self.selected_index < len(filtered):
            return filtered[self.selected_index]
        return None

    def compose(self) -> ComposeResult:
        """Compose the panel content."""
        with VerticalScroll(classes="items-container"):
            if self._is_memory_mode:
                if not self._memory_flat_items:
                    yield Static("[dim italic]No items[/]", classes="empty-message")
                else:
                    for i, (memory, ref, depth) in enumerate(self._memory_flat_items):
                        yield Static(
                            render_memory_item(
                                i,
                                memory,
                                ref,
                                depth,
                                selected_index=self.selected_index,
                                is_active=self.is_active,
                                expanded_keys=self.expanded_memory_files,
                            ),
                            classes="item",
                            id=f"item-{i}",
                        )
            else:
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
        count = self._item_count()
        if count == 0:
            return "0 of 0"
        return f"{self.selected_index + 1} of {count}"

    def _render_item(self, index: int, item: Customization) -> str:
        """Render a single item."""
        is_selected = index == self.selected_index and self.is_active
        prefix = ">" if is_selected else " "
        error_marker = " [red]![/]" if item.has_error else ""
        return f"{prefix} {item.display_name}{error_marker}"

    def _rebuild_memory_flat_items(self) -> None:
        """Build flat list of items for memory mode (with expanded refs)."""
        memory_customizations = [
            c for c in self.customizations if c.type == CustomizationType.MEMORY_FILE
        ]
        self._memory_flat_items = build_memory_flat_items(
            memory_customizations, self.expanded_memory_files
        )

    def watch_active_type(
        self, old_type: CustomizationType, new_type: CustomizationType
    ) -> None:
        """React to active type changes."""
        self._selected_indices[old_type] = self.selected_index
        restored_index = self._selected_indices.get(new_type, 0)

        if new_type == CustomizationType.MEMORY_FILE:
            self._rebuild_memory_flat_items()
            count = len(self._memory_flat_items)
        else:
            filtered = [c for c in self.customizations if c.type == new_type]
            count = len(filtered)

        if count > 0 and restored_index >= count:
            restored_index = count - 1
        elif count == 0:
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
        if self._is_memory_mode:
            self._rebuild_memory_flat_items()
            count = len(self._memory_flat_items)
        else:
            count = len(self._filtered_customizations)

        if self.selected_index >= count:
            self.selected_index = max(0, count - 1)

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

    async def _rebuild_items(self, *, scroll_to_selection: bool = False) -> None:
        """Rebuild item widgets when customizations change."""
        if not self.is_mounted:
            return
        container = self.query_one(".items-container", VerticalScroll)
        await container.remove_children()

        if self._is_memory_mode:
            if not self._memory_flat_items:
                await container.mount(
                    Static("[dim italic]No items[/]", classes="empty-message")
                )
            else:
                for i, (memory, ref, depth) in enumerate(self._memory_flat_items):
                    is_selected = i == self.selected_index and self.is_active
                    classes = "item item-selected" if is_selected else "item"
                    await container.mount(
                        Static(
                            render_memory_item(
                                i,
                                memory,
                                ref,
                                depth,
                                selected_index=self.selected_index,
                                is_active=self.is_active,
                                expanded_keys=self.expanded_memory_files,
                            ),
                            classes=classes,
                            id=f"item-{i}",
                        )
                    )
        else:
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
                        Static(
                            self._render_item(i, item), classes=classes, id=f"item-{i}"
                        )
                    )

        if scroll_to_selection:
            self._scroll_selection_to_top()
        else:
            container.scroll_home(animate=False)
        self._update_empty_state()

    def _scroll_selection_to_top(self) -> None:
        """Scroll so the selected item is at the top of the container."""
        try:
            container = self.query_one(".items-container", VerticalScroll)
            container.scroll_to(y=self.selected_index, animate=False)
        except Exception:
            pass

    async def _rebuild_items_and_scroll(self) -> None:
        """Rebuild items and scroll selection to top."""
        await self._rebuild_items(scroll_to_selection=True)

    def on_mount(self) -> None:
        """Handle mount event."""
        self.border_title = self._render_header()
        self.border_subtitle = self._render_footer()
        if self.customizations:
            if self._is_memory_mode:
                self._rebuild_memory_flat_items()
            self.call_later(self._rebuild_items)

    def _refresh_display(self) -> None:
        """Refresh the panel display (updates existing widgets)."""
        try:
            items = list(self.query("Static.item"))
            if self._is_memory_mode:
                for i, (item_widget, (memory, ref, depth)) in enumerate(
                    zip(items, self._memory_flat_items, strict=False)
                ):
                    if isinstance(item_widget, Static):
                        item_widget.update(
                            render_memory_item(
                                i,
                                memory,
                                ref,
                                depth,
                                selected_index=self.selected_index,
                                is_active=self.is_active,
                                expanded_keys=self.expanded_memory_files,
                            )
                        )
                    is_selected = i == self.selected_index and self.is_active
                    item_widget.set_class(is_selected, "item-selected")
            else:
                filtered = self._filtered_customizations
                for i, (item_widget, item) in enumerate(
                    zip(items, filtered, strict=False)
                ):
                    if isinstance(item_widget, Static):
                        item_widget.update(self._render_item(i, item))
                    is_selected = i == self.selected_index and self.is_active
                    item_widget.set_class(is_selected, "item-selected")
        except Exception:
            pass

    def _scroll_to_selection(self) -> None:
        """Scroll to keep the selected item visible."""
        if self._item_count() == 0:
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
                    if 0 <= index < self._item_count():
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
        count = self._item_count()
        if count > 0 and self.selected_index < count - 1:
            self.selected_index += 1

    def action_cursor_up(self) -> None:
        """Move selection up."""
        count = self._item_count()
        if count > 0 and self.selected_index > 0:
            self.selected_index -= 1

    def action_cursor_top(self) -> None:
        """Move selection to top."""
        if self._item_count() > 0:
            self.selected_index = 0

    def action_cursor_bottom(self) -> None:
        """Move selection to bottom."""
        count = self._item_count()
        if count > 0:
            self.selected_index = count - 1

    def action_select(self) -> None:
        """Drill down into selected customization."""
        if self._is_memory_mode and self._memory_flat_items:
            if 0 <= self.selected_index < len(self._memory_flat_items):
                memory, ref, _ = self._memory_flat_items[self.selected_index]
                if ref is not None and ref.path and ref.path.is_dir():
                    return
                self.post_message(self.DrillDown(memory))
        elif self.selected_customization:
            self.post_message(self.DrillDown(self.selected_customization))

    def action_expand(self) -> None:
        """Expand the currently selected memory file."""
        if not self._is_memory_mode or not self._memory_flat_items:
            return
        if 0 <= self.selected_index < len(self._memory_flat_items):
            memory, ref, _ = self._memory_flat_items[self.selected_index]
            memory_key = str(memory.path)
            if ref is None and memory_key not in self.expanded_memory_files:
                new_expanded = self.expanded_memory_files.copy()
                new_expanded.add(memory_key)
                self.expanded_memory_files = new_expanded
                self._rebuild_memory_flat_items()
                self.call_later(self._rebuild_items_and_scroll)

    def action_collapse(self) -> None:
        """Collapse the currently selected memory file."""
        if not self._is_memory_mode or not self._memory_flat_items:
            return
        if 0 <= self.selected_index < len(self._memory_flat_items):
            memory, _, _ = self._memory_flat_items[self.selected_index]
            memory_key = str(memory.path)
            if memory_key in self.expanded_memory_files:
                new_expanded = self.expanded_memory_files.copy()
                new_expanded.discard(memory_key)
                self.expanded_memory_files = new_expanded
                self._rebuild_memory_flat_items()
                self._adjust_memory_selection_after_collapse(memory)
                self.call_later(self._rebuild_items)

    def _adjust_memory_selection_after_collapse(
        self, collapsed_memory: Customization
    ) -> None:
        """Adjust selection after collapsing a memory file."""
        for i, (memory, ref, _) in enumerate(self._memory_flat_items):
            if memory == collapsed_memory and ref is None:
                self.selected_index = i
                break

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
        """Cycle through tabs, then delegate to app when on last tab."""
        current_idx = self.COMBINED_TYPES.index(self.active_type)
        if current_idx < len(self.COMBINED_TYPES) - 1:
            self.active_type = self.COMBINED_TYPES[current_idx + 1]
        else:
            cast("LazyClaude", self.app).action_focus_next_panel()

    def action_focus_previous_panel(self) -> None:
        """Cycle through tabs backward, then delegate to app when on first tab."""
        current_idx = self.COMBINED_TYPES.index(self.active_type)
        if current_idx > 0:
            self.active_type = self.COMBINED_TYPES[current_idx - 1]
        else:
            cast("LazyClaude", self.app).action_focus_previous_panel()

    async def action_back(self) -> None:
        """Delegate to app's back action."""
        await cast("LazyClaude", self.app).action_back()

    def set_customizations(self, customizations: list[Customization]) -> None:
        """Set the customizations for this panel (all types, filtering done internally)."""
        filtered = [c for c in customizations if c.type in self.COMBINED_TYPES]
        self.customizations = filtered
        if self._is_memory_mode:
            self._rebuild_memory_flat_items()
        self._update_empty_state()

    def _update_empty_state(self) -> None:
        """Toggle empty class based on item count."""
        if self._item_count() == 0:
            self.add_class("empty")
        else:
            self.remove_class("empty")

    def _emit_selection_message(self) -> None:
        """Emit selection message based on current selection."""
        if self._is_memory_mode and self._memory_flat_items:
            if 0 <= self.selected_index < len(self._memory_flat_items):
                memory, ref, _ = self._memory_flat_items[self.selected_index]
                self.post_message(self.SelectionChanged(memory))
                self.post_message(self.MemoryFileRefSelected(memory, ref))
        else:
            self.post_message(self.SelectionChanged(self.selected_customization))
