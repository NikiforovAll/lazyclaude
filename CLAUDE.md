# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LazyClaude is a TUI application for visualizing Claude Code customizations (Slash Commands, Subagents, Skills, Memory Files, MCPs). Built with the Textual framework following lazygit-style keyboard ergonomics.

## Active Technologies

- **Language**: Python 3.11+
- **Framework**: Textual (TUI), Rich (formatting), PyYAML (frontmatter parsing)
- **Testing**: pytest, pytest-asyncio, pytest-textual-snapshot
- **Package Manager**: uv

## Project Structure

```text
src/lazyclaude/
├── app.py               # Main Textual App
├── models/              # Data models (Customization, ConfigLevel, etc.)
├── services/            # Business logic (discovery, parsing, filtering)
├── widgets/             # UI components (TypePanel, DetailPane, etc.)
├── keybindings/         # Keyboard handlers
└── styles/              # Textual CSS (.tcss files)

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
└── snapshots/           # Visual regression tests
```

## Commands

```bash
uv sync                              # Install dependencies
uv run lazyclaude                    # Run application
uv run pytest                        # Run all tests
uv run pytest tests/unit/test_X.py  # Run single test file
uv run pytest -k "test_name"         # Run tests matching pattern
uv run ruff check src                # Lint code
uv run ruff format src               # Format code
```

## Code Style

- Type hints required for all public functions
- Linting via ruff
- Formatting via ruff format
- No emojis in code/comments
- Comments explain WHY not WHAT

## Constitution Principles

All code MUST comply with these principles (see `.specify/memory/constitution.md`):

1. **Keyboard-First**: Every action has a keyboard shortcut, vim-like navigation
2. **Panel Layout**: Multi-panel structure with clear focus indicators
3. **Contextual Navigation**: Enter drills down, Esc goes back
4. **Modal Minimalism**: No modals for simple operations
5. **Textual Framework**: All widgets extend Textual base classes
6. **UV Packaging**: uv for package management, uvx for distribution

## Keybinding Conventions

| Key | Action | Scope |
|-----|--------|-------|
| `q` | Quit | Global |
| `?` | Help | Global |
| `R` | Refresh | Global |
| `/` | Filter | Global |
| `j`/`k` | Navigate | List |
| `Enter` | Drill down | Context |
| `Esc` | Back | Context |

## Architecture

```
User Input → App (app.py) → TypePanel widgets → SelectionChanged message
                ↓                                        ↓
         ConfigDiscoveryService                   MainPane updates
                ↓
         Parsers (slash_command, subagent, skill, memory_file, mcp)
                ↓
         Customization models
```

**Data Flow**:
1. `ConfigDiscoveryService` discovers files from `~/.claude` (user) and `./.claude` (project)
2. Type-specific parsers extract frontmatter metadata and content
3. `Customization` objects are created and passed to `TypePanel` widgets
4. Selection changes emit messages handled by `App` to update `MainPane`

**Theme Sync**: App theme (Textual) maps to syntax highlighting theme (Pygments) via `TEXTUAL_TO_PYGMENTS_THEME` in `detail_pane.py`.
