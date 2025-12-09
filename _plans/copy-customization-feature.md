# Copy and Move Customization Feature - Implementation Plan

## Overview

Add ability to copy and move slash commands, subagents, and skills between configuration levels (User ↔ Project). User presses `c` key for copy or `m` key for move, modal popup shows available target levels, keyboard navigation (j/k/Enter/Esc), file copied/moved to target with conflict detection.

**User Decisions:**
- Key bindings: `c` (copy), `m` (move)
- Scope: Slash commands, subagents, skills only
- Copy direction: FROM any level (user/project/plugin) TO user/project only
- Move direction: FROM user/project TO user/project only (NO moving from plugin)
- Conflict handling: Show error, no overwrite
- UI: Separate modals for copy and move operations

---

## Architecture

### Current State (Read-Only)
- **Discovery**: `ConfigDiscoveryService` scans filesystem for customizations
- **No Write Operations**: App only displays, never creates/modifies files
- **Modal Pattern**: `FilterInput` widget uses `display: none` + `.visible` class

### New Components
1. **CustomizationWriter** service - writes and deletes files on disk
2. **LevelSelector** modal widget - keyboard-driven level picker (reused for both copy and move)
3. **Copy action handler** - coordinates copy operation
4. **Move action handler** - coordinates move operation (copy + delete source)

---

## Implementation Steps

### 1. Create File Writing Service

**File:** `src/lazyclaude/services/writer.py` (NEW)

```python
class CustomizationWriter:
    """Writes and deletes customizations on disk (inverse of parsers)."""

    def write_customization(
        self,
        customization: Customization,
        target_level: ConfigLevel,
        user_config_path: Path,
        project_config_path: Path,
    ) -> tuple[bool, str]:
        """Copy customization to target level. Returns (success, message)."""

    def delete_customization(
        self,
        customization: Customization,
    ) -> tuple[bool, str]:
        """Delete customization from disk. Returns (success, message)."""
```

**Key Methods:**
- `_get_target_base_path(level)` → Returns `~/.claude` or `./.claude`
- `_build_target_path(customization, base)` → Constructs target file path
  - Slash commands: Preserve nested structure (`nested:cmd` → `commands/nested/cmd.md`)
  - Subagents: Flat structure (`agent` → `agents/agent.md`)
  - Skills: Directory copy (`skill` → `skills/skill/` entire tree)
- `_check_conflict(path)` → Returns True if target exists
- `_ensure_parent_dirs(path)` → Creates parent directories (e.g., `./.claude/commands/nested/`)
- `_copy_skill_directory(source, target)` → Recursively copies skill tree using `shutil.copytree()`
- `_delete_file(path)` → Deletes a file
- `_delete_skill_directory(path)` → Recursively deletes skill directory using `shutil.rmtree()`

**Path Resolution Logic:**

Reverse the parser's `_derive_name()` logic:
- `nested:deep-cmd` → split on `:` → `commands/nested/deep-cmd.md`
- `my-agent` → `agents/my-agent.md`
- `my-skill` → `skills/my-skill/` (directory)

**Error Handling:**
- Catch `OSError`, `PermissionError`, `FileExistsError`
- Return `(False, "Error message")` on failure
- Return `(True, "Copied 'name' to Level")` on success

---

### 2. Create Level Selector Modal

**File:** `src/lazyclaude/widgets/level_selector.py` (NEW)

```python
class LevelSelector(Widget):
    """Modal dialog for selecting target configuration level."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("enter", "select", "Select", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]
```

**UI Layout:**
```
┌─────────────────────────────────┐
│  Copy to Configuration Level    │
│                                 │
│  > User (~/.claude)             │  ← Selected
│    Project (./.claude)          │
│                                 │
│  [Enter] Select  [Esc] Cancel   │
└─────────────────────────────────┘
```

**CSS Styling:**
```css
LevelSelector {
    display: none;
    align: center middle;
    width: 45;
    height: auto;
}

LevelSelector.visible {
    display: block;
}
```

**Key Methods:**
- `show(source: Customization, available: list[ConfigLevel], operation: str = "copy")` → Display modal
- `hide()` → Remove `.visible` class
- `action_cursor_down/up()` → Navigate options (j/k)
- `action_select()` → Emit `LevelSelected(level, operation)` message, hide modal
- `action_cancel()` → Emit `SelectionCancelled()` message, hide modal

**Messages:**
```python
class LevelSelected(Message):
    level: ConfigLevel
    operation: str  # "copy" or "move"

class SelectionCancelled(Message):
    pass
```

**Available Levels Logic:**
- Always show USER and PROJECT
- Exclude source level (can't copy to same level)
- Do NOT show PLUGIN (copying to plugins not supported)

---

### 3. Integrate Copy and Move Actions

**File:** `src/lazyclaude/app.py` (MODIFY)

#### a) Add Keybindings (line ~43)
```python
Binding("c", "copy_customization", "Copy"),
Binding("m", "move_customization", "Move"),
```

#### b) Mount Modal Widget (line ~99)
```python
def compose(self) -> ComposeResult:
    # ... existing widgets ...

    self._level_selector = LevelSelector(id="level-selector")
    yield self._level_selector
```

#### c) Add Action Handler (after `action_open_in_editor`, line ~206)
```python
def action_copy_customization(self) -> None:
    """Copy selected customization to another level."""

    # 1. Validate: Get current customization
    if not self._main_pane or not self._main_pane.customization:
        return

    customization = self._main_pane.customization

    # 2. Validate: Only slash commands, subagents, skills
    if customization.type not in [
        CustomizationType.SLASH_COMMAND,
        CustomizationType.SUBAGENT,
        CustomizationType.SKILL,
    ]:
        self._show_status_error(
            f"Cannot copy {customization.type_label} customizations"
        )
        return

    # 3. Calculate available target levels (exclude source, exclude PLUGIN)
    available = [
        level for level in [ConfigLevel.USER, ConfigLevel.PROJECT]
        if level != customization.level
    ]

    if not available:
        self._show_status_error("No available target levels")
        return

    # 4. Show level selector modal
    if self._level_selector:
        self._level_selector.show(customization, available)
```

#### d) Add Move Action Handler (after copy action handler)
```python
def action_move_customization(self) -> None:
    """Move selected customization to another level."""

    # 1. Validate: Get current customization
    if not self._main_pane or not self._main_pane.customization:
        return

    customization = self._main_pane.customization

    # 2. Validate: Only slash commands, subagents, skills
    if customization.type not in [
        CustomizationType.SLASH_COMMAND,
        CustomizationType.SUBAGENT,
        CustomizationType.SKILL,
    ]:
        self._show_status_error(
            f"Cannot move {customization.type_label} customizations"
        )
        return

    # 3. Validate: Cannot move FROM plugin level
    if customization.level == ConfigLevel.PLUGIN:
        self._show_status_error(
            "Cannot move from plugin-level customizations"
        )
        return

    # 4. Calculate available target levels (exclude source, exclude PLUGIN)
    available = [
        level for level in [ConfigLevel.USER, ConfigLevel.PROJECT]
        if level != customization.level
    ]

    if not available:
        self._show_status_error("No available target levels")
        return

    # 5. Show level selector modal (reuse same modal, track operation type)
    if self._level_selector:
        self._level_selector.show(customization, available, operation="move")
```

#### e) Add Message Handlers (after action handlers)
```python
def on_level_selector_level_selected(
    self, message: LevelSelector.LevelSelected
) -> None:
    """Perform copy or move operation after level selection."""
    if not self._main_pane or not self._main_pane.customization:
        return

    customization = self._main_pane.customization
    writer = CustomizationWriter()

    # First, copy to target
    success, msg = writer.write_customization(
        customization,
        message.level,
        self._user_config_path or Path.home() / ".claude",
        self._project_config_path or Path.cwd() / ".claude",
    )

    if not success:
        self._show_status_error(msg)
        return

    # If move operation, delete source after successful copy
    if message.operation == "move":
        delete_success, delete_msg = writer.delete_customization(customization)
        if not delete_success:
            self._show_status_error(f"Copied but failed to delete source: {delete_msg}")
            return
        # Update success message for move
        level_label = message.level.name.title()
        msg = f"Moved '{customization.name}' to {level_label} level"

    self._show_status_success(msg)
    self.action_refresh()  # Reload to show changes

def on_level_selector_selection_cancelled(
    self, message: LevelSelector.SelectionCancelled
) -> None:
    """Handle modal cancellation."""
    pass  # Modal already hidden
```

#### e) Add Status Feedback Methods
```python
def _show_status_success(self, message: str) -> None:
    """Show success message in subtitle temporarily."""
    original = self.sub_title
    self.sub_title = f"[green]✓[/green] {message}"
    self.set_timer(2.0, lambda: setattr(self, "sub_title", original))

def _show_status_error(self, message: str) -> None:
    """Show error message in subtitle temporarily."""
    original = self.sub_title
    self.sub_title = f"[red]✗[/red] {message}"
    self.set_timer(2.0, lambda: setattr(self, "sub_title", original))
```

#### f) Update Help Text (line ~420)
```diff
[bold]Actions[/]
  e              Open in $EDITOR
+ c              Copy to level
+ m              Move to level
  r              Refresh from disk
```

---

### 4. Skill Special Case Handling

Skills require copying entire directory tree (not just SKILL.md):

```python
# In CustomizationWriter._copy_skill_directory()
import shutil

shutil.copytree(
    source_skill_dir,  # ~/.claude/skills/my-skill/
    target_skill_dir,  # ./.claude/skills/my-skill/
    dirs_exist_ok=False,  # Fail on conflict
)
```

**Preserves:**
- `SKILL.md` (main file)
- `reference.md`, `examples.md` (optional)
- `scripts/`, `templates/` subdirectories
- All other files in skill directory

---

## Edge Cases & Error Handling

### 1. Nested Slash Command Paths
**Problem:** Copying `nested:deep-cmd` must preserve structure

**Solution:**
```python
# Split name on ':' and reconstruct path
parts = name.split(':')
target_path = base / 'commands' / '/'.join(parts[:-1]) / f"{parts[-1]}.md"
# Ensure parent dirs exist
target_path.parent.mkdir(parents=True, exist_ok=True)
```

### 2. Conflict Detection
**Problem:** File/directory already exists at target

**Solution:**
- Check existence before copy
- Return error: `"Slash Command 'name' already exists at User level"`
- Do NOT overwrite (no auto-rename, no --force)

### 3. Permission Errors
**Problem:** User lacks write permissions

**Solution:**
- Catch `PermissionError`
- Return: `"Permission denied writing to {path}"`

### 4. Plugin Level Restrictions
**Problem:** Copying TO plugin level is ambiguous (which plugin?)

**Solution:**
- Do NOT offer PLUGIN as target option in modal
- Only USER and PROJECT available as targets
- Copying FROM plugin TO user/project is allowed

### 5. Directory Creation
**Problem:** Target directories may not exist (`./.claude/commands/` etc.)

**Solution:**
- Use `Path.mkdir(parents=True, exist_ok=True)`
- Create full path before writing file

---

## Success & Error Messages

### Success Messages
```
"Copied 'command-name' to User level"
"Moved 'my-agent' to Project level"
```

### Error Messages
```
"Slash Command 'name' already exists at User level"
"Cannot copy/move MCP Server customizations"
"Cannot move from plugin-level customizations"
"Permission denied writing to ~/.claude/commands/"
"No available target levels"
"Copied but failed to delete source: {error}"  # For move operation failures
```

---

## Testing Strategy

### Unit Tests

**`tests/unit/test_customization_writer.py`:**
- `test_write_slash_command_to_user_level`
- `test_write_slash_command_preserves_nested_path`
- `test_write_subagent_to_project_level`
- `test_write_skill_copies_entire_directory`
- `test_delete_customization_removes_file`
- `test_delete_skill_removes_directory`
- `test_conflict_detection_returns_error`
- `test_creates_parent_directories`
- `test_handles_permission_error`

**`tests/unit/test_level_selector.py`:**
- `test_keyboard_navigation_jk`
- `test_enter_emits_level_selected`
- `test_escape_emits_selection_cancelled`
- `test_filters_source_level_from_options`

### Integration Tests

**`tests/integration/test_copy_feature.py`:**
- `test_copy_slash_command_user_to_project`
- `test_copy_subagent_project_to_user`
- `test_copy_skill_with_subdirectories`
- `test_copy_shows_error_on_conflict`
- `test_refresh_after_copy_shows_new_item`
- `test_cannot_copy_mcp_customization`

### Manual Testing Checklist
- [ ] Press `c` with slash command selected → modal appears with "Copy" title
- [ ] Press `m` with slash command selected → modal appears with "Move" title
- [ ] Navigate modal with j/k → visual selection updates
- [ ] Press Enter → file copied/moved, success message, refresh shows changes
- [ ] Press Esc → modal closes, no changes
- [ ] Copy nested slash command → preserves directory structure
- [ ] Copy skill → entire directory tree copied
- [ ] Move slash command → source deleted, appears at target
- [ ] Try to move from plugin level → error message
- [ ] Copy to existing name → error message
- [ ] Try to copy/move MCP/Hook → error message

---

## Implementation Order

1. **CustomizationWriter service** (`services/writer.py`)
   - Core file writing logic
   - Path resolution and conflict detection
   - Unit tests

2. **LevelSelector modal widget** (`widgets/level_selector.py`)
   - Modal UI and keyboard navigation
   - Message definitions
   - CSS styling
   - Unit tests

3. **App integration** (`app.py`)
   - Add keybinding
   - Mount modal widget
   - Action handler and message handlers
   - Status feedback methods

4. **Skill special case** (in `writer.py`)
   - Directory copy logic
   - Integration tests

5. **Polish & testing**
   - Edge case handling
   - Error messages refinement
   - Manual testing

---

## Critical Files

### New Files
- `src/lazyclaude/services/writer.py` - File writing service
- `src/lazyclaude/widgets/level_selector.py` - Modal widget
- `tests/unit/test_customization_writer.py` - Writer tests
- `tests/unit/test_level_selector.py` - Modal tests
- `tests/integration/test_copy_feature.py` - Integration tests

### Modified Files
- `src/lazyclaude/app.py` - Add keybinding, modal, action handler, message handlers

### Reference Files (read-only)
- `src/lazyclaude/services/parsers/slash_command.py` - Name derivation logic to reverse
- `src/lazyclaude/widgets/filter_input.py` - Modal pattern example
- `src/lazyclaude/models/customization.py` - Data structures

---

## Future Enhancements (Out of Scope)

- Rename during copy to avoid conflicts
- Copy TO plugin level (requires plugin selection)
- Batch copy multiple items
- Move operation (delete source after copy)
- Edit frontmatter during copy

---

# This file is a copy of original plan ~/.claude/plans/stateless-spinning-moonbeam.md
