# Research: Claude Code Customization Viewer

**Feature**: 001-customization-viewer
**Date**: 2025-12-06
**Status**: Complete

## 1. Textual Framework

### Decision
Use Textual 0.89+ as the TUI framework.

### Rationale
- Native Python async support with proper event handling
- CSS-based styling matches constitution requirement (V. Textual Framework Integration)
- Built-in widget system with ListView, containers, Footer for our exact needs
- First-class testing support via `pytest-textual-snapshot` and Pilot class
- Active development and mature ecosystem

### Alternatives Considered
- **Rich**: Library only, no application framework - rejected
- **urwid**: Older API, no CSS styling - rejected
- **blessed/curses**: Too low-level - rejected

### Key Findings

**Application Structure**:
```python
from textual.app import App
from textual.binding import Binding

class LazyClaude(App):
    CSS_PATH = "styles/app.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "show_help", "Help"),
        # ...
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(...)
        yield Footer()
```

**Widget Recommendations**:
- `ListView` / `ListItem` - for customization lists in type panels
- `Container` - for panel layout with CSS grid/flexbox
- `Static` / `MarkdownViewer` - for detail pane content display
- `Footer` - for keybinding hints (built-in support)
- `Input` - for filter/search input

**Testing Approach**:
```python
async def test_navigation():
    app = LazyClaude()
    async with app.run_test() as pilot:
        await pilot.press("j")  # Move down
        await pilot.press("enter")  # Drill into detail
        # assertions...
```

---

## 2. Claude Code Configuration Structure

### Decision
Support all three configuration levels with the following paths:

| Level | Path | Scope |
|-------|------|-------|
| User | `~/.claude/` | All projects |
| Project | `./.claude/` | Current project (shared) |
| Project-Local | `~/.claude.json` | Current project (personal) |

### Rationale
Official Claude Code documentation defines these as the standard configuration locations. The viewer must accurately reflect where users configure their customizations.

### Configuration Details by Type

#### Slash Commands
- **User**: `~/.claude/commands/*.md`
- **Project**: `./.claude/commands/*.md`
- **Format**: Markdown with optional YAML frontmatter
- **Namespace**: Directory structure creates namespaces (e.g., `frontend/component.md` → `/frontend:component`)

```yaml
---
description: Brief explanation
allowed-tools: "Bash(fd:*), Read"
argument-hint: "<file-pattern>"
---
Command instructions here. Use $ARGUMENTS or $1, $2 for args.
```

#### Subagents
- **User**: `~/.claude/agents/*.md`
- **Project**: `./.claude/agents/*.md`
- **Format**: Markdown with required YAML frontmatter

```yaml
---
name: agent-name
description: When to use this agent
tools: tool1, tool2  # Optional, omit for all
model: opus  # Optional
---
System prompt for the agent.
```

#### Skills
- **User**: `~/.claude/skills/<skill-name>/SKILL.md`
- **Project**: `./.claude/skills/<skill-name>/SKILL.md`
- **Format**: Directory with SKILL.md file

```yaml
---
name: skill-name
description: What this skill does
tags: category, use-case
---
Skill documentation and instructions.
```

#### Memory Files
- **User**: `~/.claude/CLAUDE.md`
- **Project**: `./.claude/CLAUDE.md` or `./CLAUDE.md`
- **Local**: `./CLAUDE.local.md`
- **Format**: Markdown with optional frontmatter, supports `@path/to/import` syntax

#### MCP Servers
- **User**: `~/.claude.json` → `mcpServers` key
- **Project**: `./.mcp.json` → `mcpServers` key
- **Format**: JSON

```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio|http|sse",
      "command": "/path/to/server",
      "args": ["--flag", "value"],
      "env": { "KEY": "value" }
    }
  }
}
```

---

## 3. UV Package Manager

### Decision
Use uv for all package management with PyPI distribution for uvx execution.

### Rationale
Constitution principle VI mandates uv usage. UV provides:
- Fast, reliable dependency resolution
- Built-in virtual environment handling
- Lock file support for reproducibility
- Direct integration with PyPI for uvx distribution

### Configuration

**pyproject.toml**:
```toml
[project]
name = "lazyclaude"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "textual>=0.89.0",
    "rich>=13.0.0",
    "pyyaml>=6.0",
]

[project.scripts]
lazyclaude = "lazyclaude.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/lazyclaude"]
```

**Development Commands**:
- `uv sync` - Install dependencies
- `uv run pytest` - Run tests
- `uv run lazyclaude` - Run application
- `uvx lazyclaude` - Run from PyPI (after publish)

---

## 4. YAML Frontmatter Parsing

### Decision
Use `pyyaml` with a simple frontmatter extraction utility.

### Rationale
- Standard library yaml parsing
- Minimal dependency footprint
- Sufficient for our needs (no complex YAML features)

### Implementation Pattern

```python
import yaml
import re

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown content."""
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        frontmatter = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
        return frontmatter, body
    return {}, content
```

---

## 5. Keybinding Design

### Decision
Follow lazygit conventions exactly as specified in the constitution.

### Mapping

| Key | Action | Scope | Constitution Reference |
|-----|--------|-------|----------------------|
| `q` | Quit | Global | I. Keyboard-First |
| `?` | Show help | Global | I. Keyboard-First |
| `R` | Refresh | Global | I. Keyboard-First |
| `/` | Filter/Search | Global | I. Keyboard-First |
| `Enter` | Drill down | Context | III. Contextual Navigation |
| `Esc` | Back/Cancel | Context | III. Contextual Navigation |
| `j`/`↓` | Move down | List | I. Keyboard-First |
| `k`/`↑` | Move up | List | I. Keyboard-First |
| `g` | Go to top | List | I. Keyboard-First |
| `G` | Go to bottom | List | I. Keyboard-First |
| `1` | All levels | Global | New (level switching) |
| `2` | User only | Global | New (level switching) |
| `3` | Project only | Global | New (level switching) |
| `Tab` | Next panel | Global | II. Panel Layout |

---

## 6. Panel Layout Design

### Decision
Left sidebar with 5 stacked type panels, right detail pane (lazygit-style).

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ LazyClaude - Customization Viewer              [All] q:quit │
├──────────────────────┬──────────────────────────────────────┤
│ Slash Commands (3)   │                                      │
│ ├─ /commit           │  /commit                             │
│ └─ /review           │  ──────────────────────────────────  │
├──────────────────────┤  Level: Project                      │
│ Subagents (2)        │  Path: .claude/commands/commit.md    │
│ ├─ code-reviewer     │                                      │
│ └─ planner           │  Description:                        │
├──────────────────────┤  Create a git commit following       │
│ Skills (1)           │  conventional commit standards.      │
│ └─ skill-creator     │                                      │
├──────────────────────┤  Content Preview:                    │
│ Memory Files (2)     │  ---                                 │
│ ├─ CLAUDE.md [P]     │  description: Create git commit      │
│ └─ AGENTS.md [U]     │  allowed-tools: "Bash(git:*)"        │
├──────────────────────┤  ---                                 │
│ MCPs (3)             │  ## Instructions                     │
│ ├─ filesystem        │  ...                                 │
│ ├─ github            │                                      │
│ └─ postgres          │                                      │
├──────────────────────┴──────────────────────────────────────┤
│ j/k:navigate  Enter:view  /:filter  1/2/3:level  ?:help     │
└─────────────────────────────────────────────────────────────┘
```

### CSS Layout

```css
Screen {
    layout: grid;
    grid-size: 2;
    grid-columns: 1fr 2fr;
}

#sidebar {
    layout: vertical;
}

.type-panel {
    height: auto;
    border: solid green;
}

.type-panel:focus {
    border: double green;
}

#detail-pane {
    border: solid blue;
}
```

---

## 7. Error Handling Strategy

### Decision
Graceful degradation with visual error indicators.

### Approach
- Missing directories: Show empty panel with "No items" message
- Malformed files: Show item with error indicator, details show error
- Permission errors: Show item with lock icon, details show permission message
- Missing config: Auto-detect and show appropriate default level

### Implementation

```python
@dataclass
class Customization:
    name: str
    type: CustomizationType
    level: ConfigLevel
    path: Path
    content: str | None = None
    error: str | None = None  # Non-None indicates parse/read error
```

---

## Summary

All technical decisions have been made and documented. No NEEDS CLARIFICATION items remain. The design fully complies with the constitution's 6 principles and is ready for Phase 1 detailed design.
