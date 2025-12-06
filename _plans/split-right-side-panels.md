# Split Right Side into Two Panels

## Goal
Split the detail pane into two panels: metadata (top) and content preview (bottom).

## Target Layout

```
┌─Status──────────────────┐┌─Metadata────────────────┐
│ lazyclaude | All        ││ Name: commit            │
└─────────────────────────┘│ Type: Slash Command     │
┌─[1]-Slash Commands (10)─┐│ Level: Project          │
│ > commit                ││ Path: .claude/commands  │
│   review                │└─────────────────────────┘
└─────────────────────────┘┌─Content─────────────────┐
┌─[2]-Subagents (3)───────┐│ # Commit Command        │
│ ...                     ││                         │
└─────────────────────────┘│ Creates a git commit... │
┌─[3]-Skills (2)──────────┐│                         │
│ ...                     ││                         │
└─────────────────────────┘└─────────────────────────┘
```

## Files to Modify

| File | Changes |
|------|---------|
| `src/lazyclaude/widgets/detail_pane.py` | Refactor into MetadataPane + ContentPane |
| `src/lazyclaude/widgets/__init__.py` | Export new widgets |
| `src/lazyclaude/styles/app.tcss` | Add right-side container, adjust heights |
| `src/lazyclaude/app.py` | Compose with new layout structure |

## Implementation

### 1. MetadataPane (`detail_pane.py`)

New widget showing compact metadata:
```python
class MetadataPane(Widget):
    """Pane displaying metadata of selected customization."""

    customization: reactive[Customization | None] = reactive(None)

    def compose(self):
        yield Static(self._render_content(), classes="metadata-content")

    def _render_content(self) -> str:
        if not self.customization:
            return "[dim italic]Select a customization[/]"
        c = self.customization
        lines = [
            f"[bold]{c.name}[/]",
            f"[dim]Type:[/] {c.type_label}",
            f"[dim]Level:[/] {c.level_label}",
            f"[dim]Path:[/] {c.path}",
        ]
        if c.description:
            lines.append(f"[dim]Description:[/] {c.description}")
        if c.has_error:
            lines.append(f"[red]Error:[/] {c.error}")
        return "\n".join(lines)

    def on_mount(self):
        self.border_title = "Metadata"
```

### 2. ContentPane (`detail_pane.py`)

New widget showing full content with scrolling:
```python
class ContentPane(Widget):
    """Pane displaying content of selected customization."""

    BINDINGS = [
        Binding("j", "scroll_down", ...),
        Binding("k", "scroll_up", ...),
        # ... other scroll bindings
    ]

    customization: reactive[Customization | None] = reactive(None)

    def compose(self):
        yield Static(self._render_content(), classes="content-text")

    def _render_content(self) -> str:
        if not self.customization:
            return "[dim italic]No content to display[/]"
        if self.customization.has_error:
            return ""  # Error shown in metadata pane
        return self.customization.content or "[dim]Empty[/]"

    def on_mount(self):
        self.border_title = "Content"
```

### 3. App Layout Changes (`app.py`)

Add Container for right side:
```python
def compose(self) -> ComposeResult:
    with Container(id="sidebar"):
        # ... status + type panels

    with Container(id="main-content"):
        self._metadata_pane = MetadataPane(id="metadata-pane")
        yield self._metadata_pane

        self._content_pane = ContentPane(id="content-pane")
        yield self._content_pane

    yield FilterInput(...)
    yield Footer()
```

Update event handlers to set customization on both panes.

### 4. CSS (`app.tcss`)

```css
Screen {
    layout: grid;
    grid-size: 2;
    grid-columns: 1fr 2fr;
}

#main-content {
    layout: vertical;
    height: 100%;
}

#metadata-pane {
    height: auto;
    min-height: 5;
    max-height: 10;
    border: solid $primary;
    padding: 0 1;
}

#content-pane {
    height: 1fr;
    border: solid $primary;
    padding: 1;
    overflow-y: auto;
}

MetadataPane:focus, ContentPane:focus {
    border: double $accent;
}
```

## Removed

- `DetailPane` class (replaced by MetadataPane + ContentPane)
- `#detail-pane` CSS rules

---
# This file is a copy of original plan ~/.claude/plans/lazy-growing-tide.md
