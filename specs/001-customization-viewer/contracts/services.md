# Service Contracts: Claude Code Customization Viewer

**Feature**: 001-customization-viewer
**Date**: 2025-12-06
**Status**: Complete

## Overview

This document defines the internal service layer contracts for the LazyClaude application. These are not external APIs but internal interfaces that ensure clean separation between UI and business logic.

---

## ConfigDiscoveryService

Discovers and loads all Claude Code customizations from the filesystem.

### Interface

```python
from abc import ABC, abstractmethod
from pathlib import Path

class IConfigDiscoveryService(ABC):
    """Service for discovering Claude Code customizations."""

    @abstractmethod
    def discover_all(self) -> list[Customization]:
        """
        Discover all customizations from all configuration levels.

        Returns:
            List of all discovered customizations, ordered by type then name.
            Includes customizations with errors (error field set).
        """
        ...

    @abstractmethod
    def discover_by_level(self, level: ConfigLevel) -> list[Customization]:
        """
        Discover customizations from a specific configuration level.

        Args:
            level: The configuration level to scan.

        Returns:
            List of customizations from the specified level.
        """
        ...

    @abstractmethod
    def discover_by_type(self, ctype: CustomizationType) -> list[Customization]:
        """
        Discover customizations of a specific type from all levels.

        Args:
            ctype: The type of customization to find.

        Returns:
            List of customizations of the specified type.
        """
        ...

    @abstractmethod
    def refresh(self) -> list[Customization]:
        """
        Re-scan all configuration directories and return fresh results.

        Returns:
            Updated list of all customizations.
        """
        ...
```

### Implementation Contract

```python
class ConfigDiscoveryService(IConfigDiscoveryService):
    """
    Implementation requirements:

    1. Path Resolution:
       - User level: Expand ~ to actual home directory
       - Project level: Use current working directory
       - Handle both Unix and Windows paths

    2. Error Handling:
       - Missing directories: Return empty list (not an error)
       - Unreadable files: Create Customization with error field set
       - Malformed content: Create Customization with error field set

    3. Ordering:
       - Primary: CustomizationType enum order
       - Secondary: Alphabetical by name within type

    4. Performance:
       - Cache results until refresh() called
       - Lazy-load content (only populate on demand)
    """

    def __init__(
        self,
        user_config_path: Path | None = None,
        project_config_path: Path | None = None,
    ):
        """
        Args:
            user_config_path: Override for ~/.claude (testing)
            project_config_path: Override for ./.claude (testing)
        """
        ...
```

---

## Parser Services

Individual parsers for each customization type.

### Base Parser Interface

```python
class ICustomizationParser(ABC):
    """Base interface for customization parsers."""

    @abstractmethod
    def parse(self, path: Path, level: ConfigLevel) -> Customization:
        """
        Parse a single customization file.

        Args:
            path: Absolute path to the configuration file.
            level: Configuration level this file belongs to.

        Returns:
            Customization object with parsed content.
            On parse failure, error field is set instead of content.
        """
        ...

    @abstractmethod
    def can_parse(self, path: Path) -> bool:
        """
        Check if this parser can handle the given path.

        Args:
            path: Path to check.

        Returns:
            True if this parser handles this file type.
        """
        ...
```

### Slash Command Parser

```python
class SlashCommandParser(ICustomizationParser):
    """
    Parser for slash command markdown files.

    File pattern: commands/**/*.md

    Expected format:
    ---
    description: Optional description
    allowed-tools: "Tool1, Tool2"  # Optional
    argument-hint: "<args>"  # Optional
    model: opus  # Optional
    ---
    Command body content

    Output:
    - name: Derived from filename (without .md)
          For nested: dir/file.md -> dir:file
    - metadata: SlashCommandMetadata dataclass
    - content: Full file content
    - description: From frontmatter or first paragraph
    """
    ...
```

### Subagent Parser

```python
class SubagentParser(ICustomizationParser):
    """
    Parser for subagent markdown files.

    File pattern: agents/*.md

    Expected format:
    ---
    name: agent-name  # Required
    description: When to use  # Required
    tools: tool1, tool2  # Optional
    model: opus  # Optional
    ---
    System prompt content

    Output:
    - name: From frontmatter 'name' field
    - metadata: SubagentMetadata dataclass
    - content: Full file content
    - description: From frontmatter
    """
    ...
```

### Skill Parser

```python
class SkillParser(ICustomizationParser):
    """
    Parser for skill directories.

    File pattern: skills/*/SKILL.md

    Expected format (SKILL.md):
    ---
    name: skill-name
    description: What this does
    tags: tag1, tag2
    ---
    Skill documentation

    Directory structure detected:
    - reference.md -> has_reference = True
    - examples.md -> has_examples = True
    - scripts/ -> has_scripts = True
    - templates/ -> has_templates = True

    Output:
    - name: From directory name or frontmatter
    - metadata: SkillMetadata with directory contents
    - content: SKILL.md content
    - description: From frontmatter
    """
    ...
```

### Memory File Parser

```python
class MemoryFileParser(ICustomizationParser):
    """
    Parser for memory files (CLAUDE.md, AGENTS.md).

    File patterns:
    - ~/.claude/CLAUDE.md (User)
    - .claude/CLAUDE.md or ./CLAUDE.md (Project)
    - ./CLAUDE.local.md (Project, local override)
    - Same patterns for AGENTS.md

    Expected format:
    ---
    tags: optional, tags  # Optional frontmatter
    ---
    Memory content
    @./path/to/import.md  # Import references

    Output:
    - name: "CLAUDE.md" or "AGENTS.md"
    - metadata: List of @import references
    - content: Full file content
    - description: First non-empty line or "Memory file"
    """
    ...
```

### MCP Parser

```python
class MCPParser(ICustomizationParser):
    """
    Parser for MCP server configurations.

    File patterns:
    - ~/.claude.json -> mcpServers (User)
    - ./.mcp.json -> mcpServers (Project)

    Expected format (JSON):
    {
      "mcpServers": {
        "server-name": {
          "type": "stdio|http|sse",
          "command": "/path/to/cmd",
          "args": ["--flag"],
          "env": {"KEY": "value"},
          "url": "https://..." (for http/sse)
        }
      }
    }

    Output:
    - One Customization per server in mcpServers
    - name: Server key name
    - metadata: MCPServerMetadata
    - content: JSON representation of server config
    - description: Generated from type + command/url
    """
    ...
```

---

## FilterService

Provides filtering and search functionality.

### Interface

```python
class IFilterService(ABC):
    """Service for filtering customizations."""

    @abstractmethod
    def filter(
        self,
        customizations: list[Customization],
        query: str,
        level: ConfigLevel | None = None,
    ) -> list[Customization]:
        """
        Filter customizations by search query and/or level.

        Args:
            customizations: Source list to filter.
            query: Search string (matches name and description).
            level: Optional level filter (None = all levels).

        Returns:
            Filtered list maintaining original order.
        """
        ...

    @abstractmethod
    def by_type(
        self,
        customizations: list[Customization],
        ctype: CustomizationType,
    ) -> list[Customization]:
        """
        Get customizations of a specific type.

        Args:
            customizations: Source list.
            ctype: Type to filter by.

        Returns:
            Customizations of the specified type.
        """
        ...
```

### Implementation Contract

```python
class FilterService(IFilterService):
    """
    Implementation requirements:

    1. Search Matching:
       - Case-insensitive substring match
       - Match against: name, description
       - Future: Consider fuzzy matching

    2. Performance:
       - O(n) filtering, no caching needed for <100 items
       - Return new list, don't mutate input

    3. Empty Handling:
       - Empty query: Return all items
       - No matches: Return empty list
    """
    ...
```

---

## Widget Contracts

### TypePanel Widget

```python
class TypePanel(Widget):
    """
    Panel displaying customizations of a single type.

    Responsibilities:
    - Display list of customizations with level indicators
    - Handle j/k navigation within list
    - Emit selection changed events
    - Show count in header
    - Support expand/collapse

    Bindings:
    - j/down: Move selection down
    - k/up: Move selection up
    - g: Go to first item
    - G: Go to last item
    - Enter: Emit drill-down event

    Events emitted:
    - SelectionChanged(customization: Customization)
    - DrillDown(customization: Customization)

    Reactive attributes:
    - customizations: list[Customization]
    - selected_index: int
    - expanded: bool
    """
    ...
```

### DetailPane Widget

```python
class DetailPane(Widget):
    """
    Pane displaying full details of selected customization.

    Responsibilities:
    - Show customization name as header
    - Display metadata (level, path, description)
    - Show full content with syntax highlighting
    - Handle scrolling for long content
    - Show error details if customization has error

    Bindings:
    - Esc: Return focus to list
    - j/down: Scroll content down
    - k/up: Scroll content up
    - g: Scroll to top
    - G: Scroll to bottom

    Reactive attributes:
    - customization: Customization | None
    """
    ...
```

### FilterInput Widget

```python
class FilterInput(Widget):
    """
    Search/filter input field.

    Responsibilities:
    - Capture search query
    - Emit filter events on input change
    - Show/hide based on filter mode

    Bindings:
    - Esc: Clear and hide
    - Enter: Apply filter and return to list

    Events emitted:
    - FilterChanged(query: str)
    - FilterCancelled()
    - FilterApplied(query: str)

    Reactive attributes:
    - visible: bool
    - query: str
    """
    ...
```

---

## Event Contracts

### Application Events

```python
from textual.message import Message

class SelectionChanged(Message):
    """Emitted when selected customization changes."""
    def __init__(self, customization: Customization) -> None:
        self.customization = customization
        super().__init__()

class DrillDown(Message):
    """Emitted when user drills into a customization."""
    def __init__(self, customization: Customization) -> None:
        self.customization = customization
        super().__init__()

class LevelFilterChanged(Message):
    """Emitted when level filter changes."""
    def __init__(self, level: ConfigLevel | None) -> None:
        self.level = level
        super().__init__()

class SearchFilterChanged(Message):
    """Emitted when search filter changes."""
    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__()

class RefreshRequested(Message):
    """Emitted when user requests configuration refresh."""
    pass
```

---

## Dependency Injection

```python
# Application composition root

def create_app(
    user_config_path: Path | None = None,
    project_config_path: Path | None = None,
) -> LazyClaude:
    """
    Create application with all dependencies wired.

    Args:
        user_config_path: Override for testing
        project_config_path: Override for testing

    Returns:
        Configured LazyClaude application instance.
    """
    discovery_service = ConfigDiscoveryService(
        user_config_path=user_config_path,
        project_config_path=project_config_path,
    )
    filter_service = FilterService()

    return LazyClaude(
        discovery_service=discovery_service,
        filter_service=filter_service,
    )
```

This enables easy testing with mock paths:

```python
# In tests
app = create_app(
    user_config_path=tmp_path / "user_config",
    project_config_path=tmp_path / "project_config",
)
```
