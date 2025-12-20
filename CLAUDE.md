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
| `M` | Open marketplace browser | Global |
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

### Data Flow

```
User Input → App (app.py) → TypePanel widgets → SelectionChanged message
                ↓                                        ↓
         ConfigDiscoveryService                   MainPane updates
                ↓
         Parsers (slash_command, subagent, skill, memory_file, mcp, hook)
                ↓
         Customization models
```

1. `ConfigDiscoveryService` discovers files from multiple sources (User, Project, Plugin)
2. Type-specific parsers in `services/parsers/` extract frontmatter metadata and content
3. `Customization` objects are created with `ConfigLevel` (USER, PROJECT, PROJECT_LOCAL, PLUGIN)
4. Selection changes emit `TypePanel.SelectionChanged` messages handled by `App` to update `MainPane`

### Widget Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LazyClaude App                                                          │
├────────────────────────┬────────────────────────────────────────────────┤
│ #sidebar (Container)   │ MainPane                                       │
│ ┌────────────────────┐ │ ┌────────────────────────────────────────────┐ │
│ │ StatusPanel        │ │ │ Content/Metadata view for selected item    │ │
│ │ Path | Filter      │ │ │ Switchable with [ / ]                      │ │
│ └────────────────────┘ │ │                                            │ │
│ ┌────────────────────┐ │ │ Supports:                                  │ │
│ │ TypePanel [1]      │ │ │ - Syntax highlighting                      │ │
│ │ Slash Commands     │ │ │ - Markdown rendering                       │ │
│ └────────────────────┘ │ │ - File tree for skills                     │ │
│ ┌────────────────────┐ │ │ - Memory file refs (@path)                 │ │
│ │ TypePanel [2]      │ │ │                                            │ │
│ │ Subagents          │ │ │                                            │ │
│ └────────────────────┘ │ │                                            │ │
│ ┌────────────────────┐ │ │                                            │ │
│ │ TypePanel [3]      │ │ │                                            │ │
│ │ Skills             │ │ │                                            │ │
│ └────────────────────┘ │ │                                            │ │
│ ┌────────────────────┐ │ │                                            │ │
│ │ CombinedPanel      │ │ │                                            │ │
│ │ [4]Mem [5]MCP [6]H │ │ │                                            │ │
│ └────────────────────┘ │ └────────────────────────────────────────────┘ │
├────────────────────────┴────────────────────────────────────────────────┤
│ Footer                                                                  │
└─────────────────────────────────────────────────────────────────────────┘

Modal overlays (hidden by default, dock: bottom):
- FilterInput: Search/filter (activated with /)
- LevelSelector: Copy/move target selection (activated with c/m)
- DeleteConfirm: Delete confirmation (activated with d)
- PluginConfirm: Plugin enable/disable confirmation (activated with t)
```

### Widget Responsibilities

| Widget | File | Purpose |
|--------|------|---------|
| `TypePanel` | `widgets/type_panel.py` | Single-type list panel (Commands, Subagents, Skills) with expandable trees |
| `CombinedPanel` | `widgets/combined_panel.py` | Multi-type tabbed panel (Memory, MCPs, Hooks) |
| `MainPane` | `widgets/detail_pane.py` | Content/metadata detail view with syntax highlighting |
| `StatusPanel` | `widgets/status_panel.py` | Shows current path and filter status |
| `FilterInput` | `widgets/filter_input.py` | Search input modal |
| `LevelSelector` | `widgets/level_selector.py` | Target level selector for copy/move |
| `DeleteConfirm` | `widgets/delete_confirm.py` | Delete confirmation modal |
| `PluginConfirm` | `widgets/plugin_confirm.py` | Plugin toggle confirmation modal |
| `MarketplaceModal` | `widgets/marketplace_modal.py` | Marketplace browser overlay |

### Shared Helpers

`widgets/helpers/rendering.py` contains shared rendering utilities:
- `render_memory_item()` - Renders memory file tree items
- `build_memory_flat_items()` - Builds flat list from nested memory refs

### CustomizationTypes

SLASH_COMMAND, SUBAGENT, SKILL, MEMORY_FILE, MCP, HOOK

### ConfigLevels

- USER: `~/.claude/` - User's global configuration
- PROJECT: `./.claude/` - Project-specific files checked into version control
- PROJECT_LOCAL: `./.claude/local/` - Project-local files (not version controlled)
- PLUGIN: `~/.claude/plugins/` - Installed third-party plugin extensions

### Plugin & Marketplace System

**Data Sources:**
- `~/.claude/plugins/known_marketplaces.json` - Index of registered marketplaces
- `<marketplace_install_location>/.claude-plugin/marketplace.json` - Per-marketplace plugin catalog
- `~/.claude/plugins/installed_plugins.json` - Registry of installed plugins with paths and versions

**Key Models (`models/marketplace.py`):**
- `MarketplaceSource` - Source type (github/directory), repo, path
- `MarketplaceEntry` - Marketplace name, source, install_location
- `MarketplacePlugin` - Plugin metadata including full_plugin_id (`name@marketplace`), install state, install_path
- `Marketplace` - Entry + list of plugins

**Services:**
- `MarketplaceLoader` (`services/marketplace_loader.py`) - Loads marketplaces and determines plugin install/enabled state from PluginLoader registry
- `PluginLoader` (`services/plugin_loader.py`) - Manages installed_plugins.json registry, resolves install paths

**Marketplace Modal (`widgets/marketplace_modal.py`):**
- Opens with `M` (Shift+m) as full-screen overlay using `layer: overlay`
- Uses Textual Tree widget: marketplaces as expandable roots, plugins as leaves
- Status icons: `[green]I[/]` (installed+enabled), `[yellow]D[/]` (disabled), `[ ]` (not installed)
- Bindings: `i` (install/toggle), `d` (uninstall), `e` (open folder), `j/k` (nav), `h/l` (collapse/expand)
- Emits messages: `PluginToggled`, `PluginUninstall`, `OpenPluginFolder`, `ModalClosed`

**Plugin Actions (via Claude CLI):**
```bash
claude plugin install <plugin_id>   # Install from marketplace
claude plugin enable <plugin_id>    # Enable disabled plugin
claude plugin disable <plugin_id>   # Disable enabled plugin
claude plugin uninstall <plugin_id> # Remove installed plugin
```

Commands run in background workers (`@work(thread=True)`) to keep UI responsive.

## Implementation Principles

**Simplicity over Generality**
- Don't add features, refactoring, or improvements beyond what's requested
- One-time operations don't need helpers or abstractions
- Don't add docstrings or comments to code you didn't change
- Trust internal code and framework guarantees; validate only at system boundaries (user input, external APIs)
