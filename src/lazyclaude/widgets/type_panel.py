"""TypePanel widget for displaying customizations of a single type."""

from pathlib import Path
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
    SkillFile,
)
from lazyclaude.widgets.helpers import build_memory_flat_items, render_memory_item


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
        Binding("right", "expand", "Expand", show=False),
        Binding("left", "collapse", "Collapse", show=False),
        Binding("l", "expand", "Expand", show=False),
        Binding("h", "collapse", "Collapse", show=False),
        Binding("escape", "back", "Back", show=False),
    ]

    DEFAULT_CSS = """
    TypePanel {
        height: 1fr;
        min-height: 3;
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

    class SkillFileSelected(Message):
        """Emitted when a file within a skill is selected."""

        def __init__(
            self, customization: Customization, file_path: Path | None
        ) -> None:
            self.customization = customization
            self.file_path = file_path
            super().__init__()

    class MemoryFileRefSelected(Message):
        """Emitted when a referenced file within a memory file is selected."""

        def __init__(
            self, customization: Customization, ref: MemoryFileRef | None
        ) -> None:
            self.customization = customization
            self.ref = ref
            super().__init__()

    expanded_skills: reactive[set[str]] = reactive(set, always_update=True)
    expanded_memory_files: reactive[set[str]] = reactive(set, always_update=True)

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
        self._flat_items: list[tuple[Customization, Path | None]] = []
        self._memory_flat_items: list[
            tuple[Customization, MemoryFileRef | None, int]
        ] = []

    @property
    def _is_skills_panel(self) -> bool:
        """Check if this panel is for skills."""
        return self.customization_type == CustomizationType.SKILL

    @property
    def _is_memory_panel(self) -> bool:
        """Check if this panel is for memory files."""
        return self.customization_type == CustomizationType.MEMORY_FILE

    @property
    def type_label(self) -> str:
        """Get human-readable type label."""
        return {
            CustomizationType.SLASH_COMMAND: "Slash Commands",
            CustomizationType.SUBAGENT: "Subagents",
            CustomizationType.SKILL: "Skills",
            CustomizationType.MEMORY_FILE: "Memory Files",
            CustomizationType.MCP: "MCPs",
            CustomizationType.HOOK: "Hooks",
        }[self.customization_type]

    @property
    def selected_customization(self) -> Customization | None:
        """Get the currently selected customization."""
        if self.customizations and 0 <= self.selected_index < len(self.customizations):
            return self.customizations[self.selected_index]
        return None

    def compose(self) -> ComposeResult:
        """Compose the panel content."""
        with VerticalScroll(classes="items-container"):
            if self._is_skills_panel:
                if not self._flat_items:
                    yield Static("[dim italic]No items[/]", classes="empty-message")
                else:
                    for i, (skill, file_path) in enumerate(self._flat_items):
                        yield Static(
                            self._render_skill_item(i, skill, file_path),
                            classes="item",
                            id=f"item-{i}",
                        )
            elif self._is_memory_panel:
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
            elif not self.customizations:
                yield Static("[dim italic]No items[/]", classes="empty-message")
            else:
                for i, item in enumerate(self.customizations):
                    yield Static(
                        self._render_item(i, item), classes="item", id=f"item-{i}"
                    )

    def _render_header(self) -> str:
        """Render the panel header with type label."""
        return f"[{self.panel_number}]-{self.type_label}-"

    def _render_footer(self) -> str:
        """Render the panel footer with selection position."""
        if self._is_skills_panel:
            count = len(self._flat_items)
        elif self._is_memory_panel:
            count = len(self._memory_flat_items)
        else:
            count = len(self.customizations)
        if count == 0:
            return "0 of 0"
        return f"{self.selected_index + 1} of {count}"

    def _render_item(self, index: int, item: Customization) -> str:
        """Render a single item."""
        is_selected = index == self.selected_index and self.is_active
        prefix = ">" if is_selected else " "
        error_marker = " [red]![/]" if item.has_error else ""
        return f"{prefix} {item.display_name}{error_marker}"

    def _render_skill_item(
        self, index: int, skill: Customization, file_path: Path | None
    ) -> str:
        """Render a skill item (skill root or file)."""
        is_selected = index == self.selected_index and self.is_active
        prefix = ">" if is_selected else " "

        if file_path is None:
            is_expanded = skill.name in self.expanded_skills
            has_files = bool(skill.metadata.get("files", []))
            expand_char = ("▼" if is_expanded else "▶") if has_files else " "
            error_marker = " [red]![/]" if skill.has_error else ""
            return f"{prefix} {expand_char} {skill.display_name}{error_marker}"
        else:
            indent = self._get_item_indent(file_path, skill)
            indent_str = "  " * indent
            name = file_path.name
            if file_path.is_dir():
                name = f"{name}/"
            return f"{prefix} {indent_str}{name}"

    def watch_customizations(self, customizations: list[Customization]) -> None:
        """React to customizations list changes."""
        if self._is_skills_panel:
            self._rebuild_flat_items()
            if self.selected_index >= len(self._flat_items):
                self.selected_index = max(0, len(self._flat_items) - 1)
        elif self._is_memory_panel:
            self._rebuild_memory_flat_items()
            if self.selected_index >= len(self._memory_flat_items):
                self.selected_index = max(0, len(self._memory_flat_items) - 1)
        elif self.selected_index >= len(customizations):
            self.selected_index = max(0, len(customizations) - 1)

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

        if self._is_skills_panel:
            if not self._flat_items:
                await container.mount(
                    Static("[dim italic]No items[/]", classes="empty-message")
                )
            else:
                for i, (skill, file_path) in enumerate(self._flat_items):
                    is_selected = i == self.selected_index and self.is_active
                    classes = "item item-selected" if is_selected else "item"
                    await container.mount(
                        Static(
                            self._render_skill_item(i, skill, file_path),
                            classes=classes,
                            id=f"item-{i}",
                        )
                    )
        elif self._is_memory_panel:
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
            if not self.customizations:
                await container.mount(
                    Static("[dim italic]No items[/]", classes="empty-message")
                )
            else:
                for i, item in enumerate(self.customizations):
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

    def on_mount(self) -> None:
        """Handle mount event - rebuild items if customizations were set before mount."""
        self.border_title = self._render_header()
        self.border_subtitle = self._render_footer()
        if self.customizations:
            self.call_later(self._rebuild_items)

    def _refresh_display(self) -> None:
        """Refresh the panel display (updates existing widgets)."""
        try:
            items = list(self.query("Static.item"))
            if self._is_skills_panel:
                for i, (item_widget, (skill, file_path)) in enumerate(
                    zip(items, self._flat_items, strict=False)
                ):
                    if isinstance(item_widget, Static):
                        item_widget.update(self._render_skill_item(i, skill, file_path))
                    is_selected = i == self.selected_index and self.is_active
                    item_widget.set_class(is_selected, "item-selected")
            elif self._is_memory_panel:
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
                for i, (item_widget, item) in enumerate(
                    zip(items, self.customizations, strict=False)
                ):
                    if isinstance(item_widget, Static):
                        item_widget.update(self._render_item(i, item))
                    is_selected = i == self.selected_index and self.is_active
                    item_widget.set_class(is_selected, "item-selected")
        except Exception:
            pass

    def _scroll_to_selection(self) -> None:
        """Scroll to keep the selected item visible."""
        item_count = self._item_count()
        if item_count == 0:
            return
        try:
            items = list(self.query(".item"))
            if 0 <= self.selected_index < len(items):
                items[self.selected_index].scroll_visible(animate=False)
        except Exception:
            pass

    def _scroll_selection_to_top(self) -> None:
        """Scroll so the selected item is at the top of the container."""
        try:
            container = self.query_one(".items-container", VerticalScroll)
            container.scroll_to(y=self.selected_index, animate=False)
        except Exception:
            pass

    def on_click(self, event: Click) -> None:
        """Handle click - select clicked item and focus panel."""
        self.focus()

        # Find which item was clicked using screen coordinates
        try:
            clicked_widget, _ = self.screen.get_widget_at(
                event.screen_x, event.screen_y
            )
        except Exception:
            return

        # Walk up widget tree to find item widget (Static with id "item-{i}")
        current: DOMNode | None = clicked_widget
        while current is not None and current is not self:
            if current.id and current.id.startswith("item-"):
                try:
                    index = int(current.id.split("-")[1])
                    item_count = self._item_count()
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

    def _item_count(self) -> int:
        """Get the number of items in the panel."""
        if self._is_skills_panel:
            return len(self._flat_items)
        if self._is_memory_panel:
            return len(self._memory_flat_items)
        return len(self.customizations)

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
        if self._is_skills_panel:
            if not self._flat_items or not (
                0 <= self.selected_index < len(self._flat_items)
            ):
                return
            skill, file_path = self._flat_items[self.selected_index]
            if file_path is not None and file_path.is_dir():
                return
            self.post_message(self.DrillDown(skill))
        elif self._is_memory_panel:
            if not self._memory_flat_items or not (
                0 <= self.selected_index < len(self._memory_flat_items)
            ):
                return
            memory, ref, _ = self._memory_flat_items[self.selected_index]
            self.post_message(self.DrillDown(memory))
        elif self.selected_customization:
            self.post_message(self.DrillDown(self.selected_customization))

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
        """Set the customizations for this panel (filtered by type)."""
        filtered = [c for c in customizations if c.type == self.customization_type]
        self.customizations = filtered
        if self._is_skills_panel:
            self._rebuild_flat_items()
        elif self._is_memory_panel:
            self._rebuild_memory_flat_items()
        self._update_empty_state()

    def _update_empty_state(self) -> None:
        """Toggle empty class based on item count."""
        if len(self.customizations) == 0:
            self.add_class("empty")
        else:
            self.remove_class("empty")

    def _rebuild_flat_items(self) -> None:
        """Build flat list of items for skills panel (with expanded files)."""
        self._flat_items = []
        for skill in self.customizations:
            self._flat_items.append((skill, None))
            if skill.name in self.expanded_skills:
                files: list[SkillFile] = skill.metadata.get("files", [])
                self._add_files_to_flat_list(skill, files, indent=1)

    def _add_files_to_flat_list(
        self, skill: Customization, files: list[SkillFile], indent: int
    ) -> None:
        """Add files to flat list with indentation tracking."""
        for file in files:
            self._flat_items.append((skill, file.path))
            if file.is_directory and file.children:
                self._add_files_to_flat_list(skill, file.children, indent + 1)

    def _rebuild_memory_flat_items(self) -> None:
        """Build flat list of items for memory panel (with expanded refs)."""
        self._memory_flat_items = build_memory_flat_items(
            self.customizations, self.expanded_memory_files
        )

    def _emit_selection_message(self) -> None:
        """Emit selection message based on current selection."""
        if self._is_skills_panel and self._flat_items:
            if 0 <= self.selected_index < len(self._flat_items):
                skill, file_path = self._flat_items[self.selected_index]
                self.post_message(self.SelectionChanged(skill))
                self.post_message(self.SkillFileSelected(skill, file_path))
        elif self._is_memory_panel and self._memory_flat_items:
            if 0 <= self.selected_index < len(self._memory_flat_items):
                memory, ref, _ = self._memory_flat_items[self.selected_index]
                self.post_message(self.SelectionChanged(memory))
                self.post_message(self.MemoryFileRefSelected(memory, ref))
        else:
            self.post_message(self.SelectionChanged(self.selected_customization))

    def _get_item_indent(self, file_path: Path | None, skill: Customization) -> int:
        """Get indentation level for a file path within a skill."""
        if not file_path:
            return 0
        skill_dir = skill.path.parent
        try:
            rel = file_path.relative_to(skill_dir)
            return len(rel.parts)
        except ValueError:
            return 1

    async def _rebuild_items_and_scroll(self) -> None:
        """Rebuild items and scroll selection to top."""
        await self._rebuild_items(scroll_to_selection=True)

    def action_expand(self) -> None:
        """Expand the currently selected item."""
        if self._is_skills_panel and self._flat_items:
            if 0 <= self.selected_index < len(self._flat_items):
                skill, file_path = self._flat_items[self.selected_index]
                if file_path is None and skill.name not in self.expanded_skills:
                    new_expanded = self.expanded_skills.copy()
                    new_expanded.add(skill.name)
                    self.expanded_skills = new_expanded
                    self._rebuild_flat_items()
                    self.call_later(self._rebuild_items_and_scroll)
        elif (
            self._is_memory_panel
            and self._memory_flat_items
            and 0 <= self.selected_index < len(self._memory_flat_items)
        ):
            memory, ref, _ = self._memory_flat_items[self.selected_index]
            memory_key = str(memory.path)
            if ref is None and memory_key not in self.expanded_memory_files:
                new_expanded = self.expanded_memory_files.copy()
                new_expanded.add(memory_key)
                self.expanded_memory_files = new_expanded
                self._rebuild_memory_flat_items()
                self.call_later(self._rebuild_items_and_scroll)

    def action_collapse(self) -> None:
        """Collapse the currently selected item."""
        if self._is_skills_panel and self._flat_items:
            if 0 <= self.selected_index < len(self._flat_items):
                skill, _ = self._flat_items[self.selected_index]
                if skill.name in self.expanded_skills:
                    new_expanded = self.expanded_skills.copy()
                    new_expanded.discard(skill.name)
                    self.expanded_skills = new_expanded
                    self._rebuild_flat_items()
                    self._adjust_selection_after_collapse(skill)
                    self.call_later(self._rebuild_items)
        elif (
            self._is_memory_panel
            and self._memory_flat_items
            and 0 <= self.selected_index < len(self._memory_flat_items)
        ):
            memory, _, __ = self._memory_flat_items[self.selected_index]
            memory_key = str(memory.path)
            if memory_key in self.expanded_memory_files:
                new_expanded = self.expanded_memory_files.copy()
                new_expanded.discard(memory_key)
                self.expanded_memory_files = new_expanded
                self._rebuild_memory_flat_items()
                self._adjust_memory_selection_after_collapse(memory)
                self.call_later(self._rebuild_items)

    def _adjust_selection_after_collapse(self, collapsed_skill: Customization) -> None:
        """Adjust selection after collapsing a skill."""
        for i, (skill, file_path) in enumerate(self._flat_items):
            if skill == collapsed_skill and file_path is None:
                self.selected_index = i
                break

    def _adjust_memory_selection_after_collapse(
        self, collapsed_memory: Customization
    ) -> None:
        """Adjust selection after collapsing a memory file."""
        for i, (memory, ref, _) in enumerate(self._memory_flat_items):
            if memory == collapsed_memory and ref is None:
                self.selected_index = i
                break
