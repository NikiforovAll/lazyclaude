# Fix TypePanel Scrollbar and Highlighting

## Problem Summary
1. **No scrollbar**: TypePanel doesn't show scrollbar when items exceed visible area
2. **Wrong item highlighted**: Selected item can be outside visible viewport when navigating

## Root Cause
- `overflow-y: auto;` missing from TypePanel CSS (DetailPane has it and works)
- No scroll-into-view logic when `selected_index` changes
- Items rendered as single Static text block, panel doesn't scroll to keep selection visible

## Files to Modify

| File | Change |
|------|--------|
| `src/lazyclaude/styles/app.tcss` | Add `overflow-y: auto;` to TypePanel |
| `src/lazyclaude/widgets/type_panel.py` | Add scroll-into-view in `watch_selected_index()` |

## Implementation

### 1. Add scrollbar CSS (`app.tcss:21-28`)

```diff
 TypePanel {
     height: auto;
     min-height: 3;
     max-height: 10;
     border: solid $primary;
     padding: 0 1;
     margin-bottom: 1;
+    overflow-y: auto;
 }
```

### 2. Add scroll-into-view logic (`type_panel.py`)

In `watch_selected_index()` method (line 147), after refreshing display, scroll to keep selection visible:

```python
def watch_selected_index(self, index: int) -> None:
    """React to selected index changes."""
    self._refresh_display()
    self._scroll_to_selection()
    self.post_message(self.SelectionChanged(self.selected_customization))

def _scroll_to_selection(self) -> None:
    """Scroll to keep the selected item visible."""
    if not self.customizations:
        return
    # Each item is one line, header is ~2 lines (header + padding)
    header_offset = 2
    target_y = self.selected_index + header_offset
    # Scroll so selected item is visible
    self.scroll_to(y=max(0, target_y - 2), animate=False)
```

---
# This file is a copy of original plan ~/.claude/plans/lazy-growing-tide.md
