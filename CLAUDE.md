# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LazyClaude is a TUI application for visualizing Claude Code customizations (Slash Commands, Subagents, Skills, Memory Files, MCPs, Hooks). Built with the Textual framework following lazygit-style keyboard ergonomics.

## Active Technologies

- **Language**: Python 3.11+
- **Framework**: Textual (TUI), Rich (formatting), PyYAML (frontmatter parsing)
- **Testing**: pytest, pytest-asyncio, pytest-textual-snapshot
- **Package Manager**: uv

## Commands

### Setup & Running

```bash
uv sync                         # Install dependencies
uv run lazyclaude              # Run application
uv run pre-commit install      # Install git hooks for quality gates
```

### Pre-commit Hooks

```bash
uv run pre-commit run --all-files      # Run all hooks manually
```

Git hooks run automatically before commit and enforce: ruff format, ruff lint, mypy checks, and pytest.

## Code Style

- Type hints required for all public functions
- Linting via ruff, formatting via ruff format
- No emojis in code/comments
- Comments explain WHY not WHAT (add comments only when logic isn't self-evident)

## Constitution Principles

All code MUST comply with these principles (see `docs/constitution.md`):

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
| `r` | Refresh | Global |
| `/` | Search | Global |
| `e` | Open in $EDITOR | Global |
| `c` | Copy to level | Global |
| `m` | Move to level | Global |
| `C` | Copy path to clipboard | Global |
| `Ctrl+u` | Open user config (~/.claude, ~/.claude.json) | Global |
| `a`/`u`/`p`/`P` | Filter: All/User/Project/Plugin | Global |
| `D` | Toggle disabled plugins | Global |
| `[`/`]` | Switch content/metadata view | Global |
| `Tab` | Switch between panels | Global |
| `0`-`6` | Focus panel by number | Global |
| `j`/`k` | Navigate up/down | List |
| `d`/`u` | Page down/up | Detail pane |
| `g`/`G` | Go to top/bottom | List |
| `Enter` | Drill down | Context |
| `Esc` | Back | Context |

## Architecture

```
User Input → App (app.py) → TypePanel widgets → SelectionChanged message
                ↓                                        ↓
         ConfigDiscoveryService                   MainPane updates
                ↓
         Parsers (slash_command, subagent, skill, memory_file, mcp, hook)
                ↓
         Customization models
```

**Data Flow**:
1. `ConfigDiscoveryService` discovers files from multiple sources:
   - User: `~/.claude/` (commands, agents, skills, memory files)
   - Project: `./.claude/` and project root (CLAUDE.md, .mcp.json)
   - Plugins: `~/.claude/plugins/` (enabled plugins from installed_plugins.json)
2. Type-specific parsers in `services/parsers/` extract frontmatter metadata and content
3. `Customization` objects are created with `ConfigLevel` (USER, PROJECT, PROJECT_LOCAL, PLUGIN)
4. Selection changes emit `TypePanel.SelectionChanged` messages handled by `App` to update `MainPane`

**CustomizationTypes**: SLASH_COMMAND, SUBAGENT, SKILL, MEMORY_FILE, MCP, HOOK

**ConfigLevels**: USER, PROJECT, PROJECT_LOCAL, PLUGIN
- USER: `~/.claude/` - User's global configuration
- PROJECT: `./.claude/` - Project-specific files checked into version control
- PROJECT_LOCAL: `./.claude/local/` - Project-local files (not version controlled, .gitignored)
- PLUGIN: `~/.claude/plugins/` - Installed third-party plugin extensions

## Implementation Principles

**Simplicity over Generality**
- Don't add features, refactoring, or improvements beyond what's requested
- One-time operations don't need helpers or abstractions
- Don't add docstrings or comments to code you didn't change
- Trust internal code and framework guarantees; validate only at system boundaries (user input, external APIs)
