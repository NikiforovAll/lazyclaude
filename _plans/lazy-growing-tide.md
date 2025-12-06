# Lazygit-Style Panel Enhancements

## Goal
Match lazygit panel aesthetics with numbered border titles and status section.

## Changes Overview

| Change | Description |
|--------|-------------|
| Border titles | Move titles into border with `[N]-Title (count)-` format |
| Panel navigation | 1-5 keys jump to specific panels |
| Status section | New panel showing current config folder |
| Rebind filters | a/u/p instead of 1/2/3 for All/User/Project |

## Files to Modify

| File | Changes |
|------|---------|
| `src/lazyclaude/widgets/type_panel.py` | Add `panel_number` prop, use `border_title` |
| `src/lazyclaude/widgets/status_panel.py` | **NEW** - Status panel widget |
| `src/lazyclaude/styles/app.tcss` | Border-title CSS, status panel styles |
| `src/lazyclaude/app.py` | Add StatusPanel, rebind keys, add panel jump actions |

## Implementation

### 1. TypePanel (`type_panel.py`)

**Add panel_number property:**
```python
panel_number: reactive[int] = reactive(1)

def _render_header(self) -> str:
    count = len(self.customizations)
    return f"[{self.panel_number}]-{self.type_label} ({count})-"
```

**Use border_title instead of Static header:**
- Remove `yield Static(self._render_header(), ...)` from compose()
- Set `self.border_title = self._render_header()` in on_mount() and watch_customizations()

### 2. StatusPanel (`widgets/status_panel.py`) - NEW

Simple widget showing current config folder:
```python
class StatusPanel(Widget):
    config_path: reactive[str] = reactive("")

    def compose(self):
        yield Static(self.config_path)

    def on_mount(self):
        self.border_title = "[0]-Status-"
```

### 3. App Changes (`app.py`)

**Rebind filter keys:**
```python
# OLD:
Binding("1", "filter_all", "All"),
Binding("2", "filter_user", "User"),
Binding("3", "filter_project", "Project"),

# NEW:
Binding("a", "filter_all", "All"),
Binding("u", "filter_user", "User"),
Binding("p", "filter_project", "Project"),
```

**Add panel jump bindings:**
```python
Binding("1", "focus_panel_1", "Slash Cmds", show=False),
Binding("2", "focus_panel_2", "Subagents", show=False),
Binding("3", "focus_panel_3", "Skills", show=False),
Binding("4", "focus_panel_4", "Memory", show=False),
Binding("5", "focus_panel_5", "MCPs", show=False),
```

**Add StatusPanel to layout:**
- Add StatusPanel above TypePanels in sidebar
- Pass config_path from discovery service

### 4. CSS (`app.tcss`)

```css
TypePanel {
    border-title-align: left;
    border-title-color: $text;
}

TypePanel:focus {
    border-title-color: $accent;
}

StatusPanel {
    height: 3;
    border: solid $primary;
    border-title-align: left;
}
```

## Panel Layout

```
┌─[0]-Status──────────────┐┌─────────────────────────┐
│ ~/.claude               ││                         │
└─────────────────────────┘│                         │
┌─[1]-Slash Commands (10)─┐│                         │
│ > commit                ││      Detail Pane        │
│   review                ││                         │
└─────────────────────────┘│                         │
┌─[2]-Subagents (3)───────┐│                         │
│ ...                     ││                         │
└─────────────────────────┘└─────────────────────────┘
```

## Keybinding Summary

| Key | Action |
|-----|--------|
| 1-5 | Jump to panel |
| a | Filter: All levels |
| u | Filter: User level |
| p | Filter: Project level |

---
# This file is a copy of original plan ~/.claude/plans/lazy-growing-tide.md
