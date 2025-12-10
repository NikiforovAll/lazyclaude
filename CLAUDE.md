# CLAUDE.md

## Project Overview

LazyClaude is a TUI application for visualizing Claude Code customizations (Slash Commands, Subagents, Skills, Memory Files, MCPs, Hooks). Built with the Textual framework following lazygit-style keyboard ergonomics.

## Active Technologies

- **Language**: Python 3.11+
- **Framework**: Textual (TUI), Rich (formatting), PyYAML (frontmatter parsing)
- **Testing**: pytest, pytest-asyncio, pytest-textual-snapshot
- **Package Manager**: uv

## Commands

```bash
uv sync                                # Install dependencies
uv run lazyclaude                      # Run application
uv run pytest                          # Run all tests
uv run pytest tests/unit/test_X.py    # Run single test file
uv run pytest -k "test_name"           # Run tests matching pattern
uv run ruff check src tests            # Lint code
uv run ruff format src tests           # Format code
uv run mypy src                        # Type check
```

## Code Style

- Type hints required for all public functions
- Linting via ruff, formatting via ruff format
- No emojis in code/comments
- Comments explain WHY not WHAT

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
| `R` | Refresh | Global |
| `/` | Search | Global |
| `e` | Open in $EDITOR | Global |
| `a`/`u`/`p`/`P` | Filter: All/User/Project/Plugin | Global |
| `1`-`6` | Focus panel by number | Global |
| `j`/`k` | Navigate up/down | List |
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

<!-- BACKLOG.MD MCP GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_workflow_overview()` tool to load the tool-oriented overview (it lists the matching guide tools).

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:
- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and completion
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->
