# Data Model: Claude Code Customization Viewer

**Feature**: 001-customization-viewer
**Date**: 2025-12-06
**Status**: Complete

## Core Entities

### ConfigLevel

Enumeration representing where a customization is defined.

```python
from enum import Enum, auto

class ConfigLevel(Enum):
    """Configuration level where a customization is defined."""
    USER = auto()          # ~/.claude/
    PROJECT = auto()       # ./.claude/
    PROJECT_LOCAL = auto() # ~/.claude.json (for MCPs only)
```

**Constraints**:
- PROJECT_LOCAL only valid for MCP customizations
- Higher specificity overrides: PROJECT > USER

---

### CustomizationType

Enumeration of customization categories.

```python
class CustomizationType(Enum):
    """Type of Claude Code customization."""
    SLASH_COMMAND = auto()
    SUBAGENT = auto()
    SKILL = auto()
    MEMORY_FILE = auto()
    MCP = auto()
```

**Display Order** (per spec FR-001):
1. SLASH_COMMAND
2. SUBAGENT
3. SKILL
4. MEMORY_FILE
5. MCP

---

### Customization

Core entity representing a single Claude Code configuration item.

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class Customization:
    """A Claude Code customization item."""
    name: str
    type: CustomizationType
    level: ConfigLevel
    path: Path

    # Parsed content (None if error during read/parse)
    description: str | None = None
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Error state (non-None indicates failure)
    error: str | None = None

    @property
    def has_error(self) -> bool:
        """Check if this customization failed to load."""
        return self.error is not None

    @property
    def display_name(self) -> str:
        """Name for display in UI, with level indicator."""
        level_indicator = {
            ConfigLevel.USER: "[U]",
            ConfigLevel.PROJECT: "[P]",
            ConfigLevel.PROJECT_LOCAL: "[L]",
        }
        return f"{self.name} {level_indicator[self.level]}"

    @property
    def level_label(self) -> str:
        """Human-readable level label."""
        return {
            ConfigLevel.USER: "User",
            ConfigLevel.PROJECT: "Project",
            ConfigLevel.PROJECT_LOCAL: "Project-Local",
        }[self.level]
```

**Field Descriptions**:

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `name` | str | Identifier (e.g., "commit", "code-reviewer") | Yes |
| `type` | CustomizationType | Category of customization | Yes |
| `level` | ConfigLevel | Where defined (User/Project/ProjectLocal) | Yes |
| `path` | Path | Absolute path to source file | Yes |
| `description` | str \| None | Brief description from frontmatter | No |
| `content` | str \| None | Full file content for detail view | No |
| `metadata` | dict | Parsed frontmatter/JSON fields | No |
| `error` | str \| None | Error message if load failed | No |

**Validation Rules**:
- `name` must be non-empty
- `path` must be absolute
- If `error` is set, `content` should be None

---

### SlashCommandMetadata

Specialized metadata for slash commands.

```python
@dataclass
class SlashCommandMetadata:
    """Metadata specific to slash commands."""
    allowed_tools: list[str] = field(default_factory=list)
    argument_hint: str | None = None
    model: str | None = None
    disable_model_invocation: bool = False
```

---

### SubagentMetadata

Specialized metadata for subagents.

```python
@dataclass
class SubagentMetadata:
    """Metadata specific to subagents."""
    tools: list[str] = field(default_factory=list)
    model: str | None = None
    permission_mode: str | None = None
    skills: list[str] = field(default_factory=list)
```

---

### SkillMetadata

Specialized metadata for skills.

```python
@dataclass
class SkillMetadata:
    """Metadata specific to skills."""
    tags: list[str] = field(default_factory=list)
    has_reference: bool = False
    has_examples: bool = False
    has_scripts: bool = False
    has_templates: bool = False
```

---

### MCPServerMetadata

Specialized metadata for MCP servers.

```python
@dataclass
class MCPServerMetadata:
    """Metadata specific to MCP servers."""
    transport_type: str  # "stdio" | "http" | "sse"
    command: str | None = None
    url: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
```

---

## State Entities

### AppState

Application-level state management.

```python
@dataclass
class AppState:
    """Global application state."""
    customizations: list[Customization] = field(default_factory=list)
    active_filter: str = ""
    level_filter: ConfigLevel | None = None  # None = show all
    selected_type: CustomizationType = CustomizationType.SLASH_COMMAND
    selected_index: int = 0
    filter_mode: bool = False

    @property
    def filtered_customizations(self) -> list[Customization]:
        """Get customizations matching current filters."""
        result = self.customizations

        if self.level_filter:
            result = [c for c in result if c.level == self.level_filter]

        if self.active_filter:
            query = self.active_filter.lower()
            result = [
                c for c in result
                if query in c.name.lower()
                or (c.description and query in c.description.lower())
            ]

        return result

    def by_type(self, ctype: CustomizationType) -> list[Customization]:
        """Get filtered customizations of a specific type."""
        return [c for c in self.filtered_customizations if c.type == ctype]
```

---

### TypePanelState

State for individual type panels.

```python
@dataclass
class TypePanelState:
    """State for a customization type panel."""
    type: CustomizationType
    expanded: bool = True
    selected_index: int = 0
    scroll_offset: int = 0
```

---

## Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                        AppState                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ customizations: list[Customization]                 │    │
│  │ level_filter: ConfigLevel | None                    │    │
│  │ active_filter: str                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Customization                          │    │
│  │  ├─ type: CustomizationType ────────────────────────┼────┤
│  │  ├─ level: ConfigLevel                              │    │
│  │  ├─ metadata: dict ─────┬───────────────────────────┼────┤
│  │  │                      │                           │    │
│  │  │    ┌─────────────────┴─────────────────────┐    │    │
│  │  │    │ SlashCommandMetadata                  │    │    │
│  │  │    │ SubagentMetadata                      │    │    │
│  │  │    │ SkillMetadata                         │    │    │
│  │  │    │ MCPServerMetadata                     │    │    │
│  │  │    └───────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘

CustomizationType (enum)          ConfigLevel (enum)
├─ SLASH_COMMAND                  ├─ USER
├─ SUBAGENT                       ├─ PROJECT
├─ SKILL                          └─ PROJECT_LOCAL
├─ MEMORY_FILE
└─ MCP
```

---

## State Transitions

### Level Filter Transitions

```
         ┌──────────────────────────────────────┐
         │                                      │
    ┌────▼────┐    ┌─────────┐    ┌───────────┐│
    │   ALL   │◄───│  USER   │◄───│  PROJECT  ││
    │  (1)    │    │   (2)   │    │    (3)    ││
    └────┬────┘    └────┬────┘    └─────┬─────┘│
         │              │               │      │
         └──────────────┴───────────────┴──────┘
                   Key press cycles
```

### Navigation State

```
  BROWSING                    FILTERING
  ┌─────────────┐            ┌─────────────┐
  │ filter_mode │────"/"────►│ filter_mode │
  │   = false   │            │   = true    │
  └─────────────┘◄───Esc─────└─────────────┘
        │
        │ Enter
        ▼
  DETAIL VIEW (focus on detail pane)
        │
        │ Esc
        ▼
  BROWSING (focus returns to list)
```

---

## File Locations Summary

| Type | User Path | Project Path | Local Path |
|------|-----------|--------------|------------|
| Slash Commands | `~/.claude/commands/*.md` | `.claude/commands/*.md` | — |
| Subagents | `~/.claude/agents/*.md` | `.claude/agents/*.md` | — |
| Skills | `~/.claude/skills/*/SKILL.md` | `.claude/skills/*/SKILL.md` | — |
| Memory Files | `~/.claude/CLAUDE.md` | `.claude/CLAUDE.md`, `CLAUDE.md` | `CLAUDE.local.md` |
| MCPs | `~/.claude.json` | `.mcp.json` | — |

Note: Memory files at `CLAUDE.local.md` use ConfigLevel.PROJECT (local override of project config).
