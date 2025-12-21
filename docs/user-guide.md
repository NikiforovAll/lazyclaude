# LazyClaude User Guide

A keyboard-driven TUI for visualizing and managing Claude Code customizations.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Understanding the Interface](#understanding-the-interface)
  - [Customization Types](#customization-types)
  - [Configuration Levels](#configuration-levels)
  - [Panel Layout](#panel-layout)
- [Core Workflows](#core-workflows)
  - [1. Viewing and Filtering Configurations](#1-viewing-and-filtering-configurations)
  - [2. Editing Customizations](#2-editing-customizations)
  - [3. Managing Configurations Across Levels](#3-managing-configurations-across-levels)
  - [4. Working with Marketplace](#4-working-with-marketplace)
- [Keyboard Reference](#keyboard-reference)
- [Tips and Best Practices](#tips-and-best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

LazyClaude is a terminal user interface (TUI) for managing Claude Code customizations. It provides a visual way to explore, edit, and organize your slash commands, subagents, skills, memory files, MCPs, and hooks across different configuration levels.

**Key Features:**
- Visual exploration of all Claude Code customizations
- Multi-level configuration management (user, project, plugin)
- Copy and move configurations between levels
- Marketplace browser for discovering and installing plugins
- Preview plugin content before installation
- Keyboard-driven workflow inspired by lazygit

## Getting Started

```bash
uvx lazyclaude
```

### First Launch

When you first launch LazyClaude, you'll see:
- Left sidebar with panels for each customization type
- Right pane showing content of selected item
- Status bar showing current path and filter state
- Footer with keyboard shortcuts

![First Launch](./assets/first-launch.gif)

**Quick Start:**
1. Use `j`/`k` or arrow keys to navigate
2. Press `1-6` or `Tab` to switch between panels
3. Press `[` / `]` to toggle between content and metadata views
4. Press `?` for help, `q` to quit

## Understanding the Interface

### Customization Types

LazyClaude organizes Claude Code customizations into six types:

| Type | Panel | Description |
|------|-------|-------------|
| **Slash Commands** | `[1]` | Custom commands like `/commit`, `/review` |
| **Subagents** | `[2]` | Specialized agents for specific tasks |
| **Skills** | `[3]` | Reusable workflows and procedures |
| **Memory Files** | `[4]` | Context files referenced with `@` |
| **MCPs** | `[5]` | Model Context Protocol servers |
| **Hooks** | `[6]` | Event-driven automations |

### Configuration Levels

Customizations exist at different levels, allowing you to control scope and sharing:

| Level | Location | Purpose | Version Control |
|-------|----------|---------|-----------------|
| **User** | `~/.claude/` | Personal global configurations | No |
| **Project** | `./.claude/` | Project-specific, shared with team | Yes (git) |
| **Project Local** | `./.claude/local/` | Project-specific, machine-local | No |
| **Plugin** | `~/.claude/plugins/` | Installed marketplace extensions | No |

### Panel Layout

```
┌─────────────────────────────────────────────────────┐
│ Status: lazyclaude | All                            │
├──────────────────────┬──────────────────────────────┤
│ [1] Slash Commands   │                              │
│   handbook:commit    │    Content / Metadata        │
│   open-files         │    (toggle with [ / ])       │
│   reflect            │                              │
│                      │    Syntax highlighting       │
│ [2] Subagents        │    Markdown rendering        │
│   handbook:review    │    File trees for skills     │
│   git-diff-analyzer  │                              │
│                      │                              │
│ [3] Skills           │                              │
│   quality-gates      │                              │
│   uspp:uspp-monitor  │                              │
│                      │                              │
│ [4] Memory | [5] MCP │                              │
│     [6] Hooks        │                              │
└──────────────────────┴──────────────────────────────┘
│ Quit | Help | Edit | Copy | Move | Search | Market  │
└─────────────────────────────────────────────────────┘
```

## Core Workflows

### 1. Viewing and Filtering Configurations

**Use Case:** Understand what customizations are available and where they're defined.

**Steps:**
1. Launch LazyClaude: `uv run lazyclaude`
2. Press `1-6` to focus different customization types
3. Use filter keys to narrow view:
   - `a` - Show All levels
   - `u` - Show only User level
   - `p` - Show only Project level
   - `P` - Show only Plugin level
4. Press `D` to toggle visibility of disabled plugins
5. Navigate items with `j`/`k` or arrow keys
6. Press `[` / `]` to switch between content and metadata views

![Filter Workflow Demo](./assets/demo-filter-workflow.gif)

**Tips:**
- Status bar shows current filter (e.g., `lazyclaude | Project`)
- Combine filters with panel navigation for efficient browsing
- Use `/` to search within current view

### 2. Editing Customizations

**Use Case:** Modify a customization to change its behavior.

**Steps:**
1. Navigate to the customization you want to edit
2. Press `e` to open in your `$EDITOR`
3. Make your changes and save
4. Press `r` to refresh LazyClaude and see updates

<--- DEMO PLACEHOLDER -->

**Requirements:**
- `$EDITOR` environment variable must be set (e.g., `export EDITOR=vim`)
- Write permissions for the target file

**Tip:** Use `C` to copy the file path to clipboard for external editing

### 3. Managing Configurations Across Levels

**Use Case:** Copy customizations between levels to share with team, customize plugin content, or reorganize configurations.

This is one of LazyClaude's most powerful features, enabling several common scenarios:
- Install a plugin and customize it for personal use
- Share personal configurations with your team
- Promote local configs to version control
- Reorganize configuration hierarchy

#### Copy vs Move

| Operation | Key | Behavior | Use When |
|-----------|-----|----------|----------|
| **Copy** | `c` | Creates duplicate at target, keeps original | Customizing plugins, sharing configs |
| **Move** | `m` | Removes original, creates at target | Reorganizing, promoting configs |

#### Scenario A: Customize Plugin Content

**Goal:** Install a marketplace plugin and customize it for your personal workflow.

**Steps:**
1. Press `M` to open marketplace
2. Install the plugin (see [Working with Marketplace](#4-working-with-marketplace))
3. Press `Esc` to close marketplace
4. Press `P` to filter to Plugin level
5. Navigate to the plugin customization you want to customize
6. Press `c` to initiate copy operation
7. Select `User` as target level
8. Press `u` to filter to User level and verify the copy
9. Press `e` to edit your personal copy

**Example Flow:**
```
Plugin → Copy → User → Edit
```

**Why Copy Instead of Edit?**
- Preserves original plugin for updates
- Allows personal customization without conflicts
- Can revert by deleting user copy

#### Scenario B: Share Configuration with Team

**Goal:** Share a useful personal configuration with your team by adding it to version control.

**Steps:**
1. Press `u` to filter to User level
2. Navigate to the customization you want to share
3. Press `c` to initiate copy operation
4. Select `Project` as target level
5. The customization is now in `./.claude/`
6. Press `p` to filter to Project level and verify
7. Commit to git:
   ```bash
   git add .claude/
   git commit -m "Add custom slash command"
   git push
   ```


**Example Flow:**
```
User → Copy → Project → Git Commit
```

**Benefits:**
- Team gets access to your custom workflows
- Configuration is version controlled
- Changes can be reviewed via pull requests

#### Scenario C: Promote Local to Project

**Goal:** Move a project-local configuration to version-controlled project level.

**Steps:**
1. Navigate to a Project Local customization
2. Press `m` to initiate move operation
3. Select `Project` as target level
4. The configuration moves from `./.claude/local/` to `./.claude/`
5. Commit to git to share with team

**Example Flow:**
```
Project Local → Move → Project → Git Commit
```

#### Common Copy/Move Patterns

| From | To | Operation | Use Case |
|------|----|-----------|----- |
| Plugin | User | Copy | Customize plugin content |
| User | Project | Copy | Share personal config with team |
| Project | User | Copy | Personalize team config |
| Project Local | Project | Move | Promote to version control |
| Project | Project Local | Move | Make machine-specific |
| User | User | - | N/A (same level) |

**Level Selection:**
```
┌─────────────────────────────────┐
│ Select target level             │
├─────────────────────────────────┤
│ > User (~/.claude/)             │
│   Project (./.claude/)          │
│   Project Local (./.claude/local/) │
└─────────────────────────────────┘
```

### 4. Working with Marketplace

**Use Case:** Discover, preview, install, and manage marketplace plugins.

#### Browse and Install Plugins

**Steps:**
1. Press `M` (Shift+m) to open marketplace browser
2. Navigate with `j`/`k` to browse marketplaces and plugins
3. Press `l` or `Enter` to expand a marketplace tree
4. Press `h` to collapse a marketplace tree
5. Find a plugin you want to install
6. Press `i` to install (or enable if already installed)
7. Wait for installation to complete
8. Press `Esc` to close marketplace
9. Press `P` to filter to Plugin level and explore

<--- DEMO PLACEHOLDER -->

**Marketplace Status Icons:**
- `[I]` (green) - Installed and enabled
- `[D]` (yellow) - Installed but disabled
- `[ ]` - Not installed

**Marketplace Actions:**
- `i` - Install plugin (or enable if disabled)
- `d` - Uninstall plugin
- `e` - Open plugin folder in file manager
- `/` - Search within marketplace

#### Preview Plugin Content

**Use Case:** Explore plugin contents before installing to understand what it provides.

**Steps:**
1. Press `M` to open marketplace browser
2. Navigate to a plugin (e.g., `handbook-glab@cc-handbook`)
3. Press `p` to enter preview mode
4. Marketplace modal closes automatically
5. Main panels now show plugin content (read-only)
6. Use `1-6` to explore different customization types
7. Press `[` / `]` to view content and metadata
8. Press `Esc` to exit preview mode and return to normal view

<--- DEMO PLACEHOLDER -->

**Preview Mode Features:**
- View all customizations included in a plugin
- Read content and metadata without installing
- Understand plugin structure and capabilities
- Navigate as if plugin were installed (read-only)

**When to Preview:**
- Evaluating plugins before installation
- Checking if plugin meets your needs
- Understanding plugin structure
- Learning from plugin implementations

#### Manage Installed Plugins

**Steps:**
1. Press `M` to open marketplace
2. Navigate to an installed plugin (marked with `[I]` or `[D]`)
3. Use management actions:
   - `i` - Toggle enabled/disabled state
   - `d` - Uninstall plugin
   - `e` - Open plugin folder
4. Press `Esc` to close marketplace

<--- DEMO PLACEHOLDER -->

**Plugin States:**
- **Enabled** `[I]` - Active and available in Claude Code
- **Disabled** `[D]` - Installed but not loaded
- **Not Installed** `[ ]` - Available in marketplace

## Keyboard Reference

### Global Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit LazyClaude |
| `?` | Help | Show help screen |
| `r` | Refresh | Reload configurations |
| `/` | Search | Search/filter current view |
| `Esc` | Back | Return to previous context |

### Navigation

| Key | Action | Description |
|-----|--------|-------------|
| `j` / `↓` | Down | Move selection down |
| `k` / `↑` | Up | Move selection up |
| `g` | Top | Jump to first item |
| `G` | Bottom | Jump to last item |
| `d` | Page Down | Scroll detail pane down |
| `u` | Page Up | Scroll detail pane up |
| `Tab` | Next Panel | Switch to next panel |
| `0-6` | Focus Panel | Jump directly to panel |

### Panel Actions

| Key | Action | Description |
|-----|--------|-------------|
| `[` | Content View | Show content |
| `]` | Metadata View | Show metadata |
| `Enter` | Drill Down | Expand tree or open item |

### Configuration Management

| Key | Action | Description |
|-----|--------|-------------|
| `e` | Edit | Open in `$EDITOR` |
| `c` | Copy | Copy to another level |
| `m` | Move | Move to another level |
| `C` | Copy Path | Copy file path to clipboard |
| `Ctrl+u` | User Config | Open `~/.claude/` |

### Filtering

| Key | Action | Description |
|-----|--------|-------------|
| `a` | All | Show all levels |
| `u` | User | Show only user level |
| `p` | Project | Show only project level |
| `P` | Plugin | Show only plugin level |
| `D` | Toggle Disabled | Show/hide disabled plugins |

### Marketplace

| Key | Action | Description |
|-----|--------|-------------|
| `M` | Open Marketplace | Browse plugins |
| `i` | Install/Enable | Install or enable plugin |
| `d` | Uninstall | Remove plugin |
| `e` | Open Folder | Open plugin folder |
| `p` | Preview | Preview plugin content |
| `h` / `l` | Collapse/Expand | Tree navigation |

## Tips and Best Practices

### Configuration Strategy

**User Level** (`~/.claude/`)
- Personal preferences and workflows
- Custom commands for your coding style
- Private configurations and credentials
- Experiments and prototypes

**Project Level** (`./.claude/`)
- Team-shared commands and skills
- Project-specific conventions
- Standardized workflows
- Version-controlled configurations

**Project Local** (`./.claude/local/`)
- Machine-specific paths
- Local development overrides
- Temporary experiments
- Not version controlled

**Plugin Level** (`~/.claude/plugins/`)
- Install from marketplace
- Keep originals untouched
- Copy to user level to customize
- Check for updates periodically

### Efficient Workflows

**Quick Copy Pattern:**
```
[P]lugin → navigate → [c]opy → User
[u]ser → navigate → [e]dit
```

**Share with Team:**
```
[u]ser → navigate → [c]opy → Project
git add .claude/ && git commit
```

**Browse and Install:**
```
[M]arketplace → [l]expand → navigate → [i]nstall
[Esc] → [P]lugin → verify
```

**Preview Before Install:**
```
[M]arketplace → navigate → [p]review
Explore in panels
[Esc] → [M] → [i]nstall if satisfied
```

### Marketplace Best Practices

1. **Explore First** - Use `M` to browse available plugins
2. **Preview Before Install** - Use `p` to examine plugin content
3. **Install Selectively** - Only install plugins you'll actively use
4. **Customize via Copy** - Copy plugin configs to user level for modifications
5. **Keep Organized** - Periodically review installed plugins with `M`
6. **Check Updates** - Keep marketplace plugins updated

### Keyboard Shortcuts Memorization

**By Frequency:**
1. `j`/`k` - Navigation (most used)
2. `1-6` - Panel switching
3. `[`/`]` - View toggling
4. `e` - Edit (daily use)
5. `c` - Copy (common operation)
6. `M` - Marketplace (occasional)

**By Category:**
- **Navigation**: `j`, `k`, `g`, `G`, `Tab`, `0-6`
- **Viewing**: `[`, `]`, `a`, `u`, `p`, `P`, `D`
- **Actions**: `e`, `c`, `m`, `C`
- **Global**: `q`, `?`, `r`, `/`, `Esc`, `M`

## Troubleshooting

### Configuration Not Appearing

**Problem:** A configuration file exists but doesn't show in LazyClaude.

**Solutions:**
- Press `r` to refresh after external changes
- Check filter: Press `a` to show All levels
- Verify file location matches expected level
- Check file has correct frontmatter format

### Edit Command Not Working

**Problem:** Pressing `e` does nothing or shows error.

**Solutions:**
- Ensure `$EDITOR` environment variable is set:
  ```bash
  export EDITOR=vim        # or code, nano, emacs, etc.
  ```
- Check write permissions on the file
- Verify the file path exists

### Plugin Installation Issues

**Problem:** Plugin installation fails or hangs.

**Solutions:**
- Check network connectivity
- Verify marketplace URL in `~/.claude/plugins/known_marketplaces.json`
- Check terminal output for error messages
- Try uninstalling and reinstalling: `M` → `d` → `i`

### Copy/Move Operations Failing

**Problem:** Copy or move operation fails with error.

**Solutions:**
- Ensure target directory exists (e.g., `./.claude/` for project level)
- Check file permissions
- Verify you're not overwriting existing files with same name
- Create target directory if needed:
  ```bash
  mkdir -p .claude
  ```

### Marketplace Not Loading

**Problem:** Marketplace is empty or shows errors.

**Solutions:**
- Check `~/.claude/plugins/known_marketplaces.json` exists
- Verify marketplace registry format
- Check network access to marketplace repositories
- Refresh with `r` after fixing marketplace configuration

### Preview Mode Issues

**Problem:** Preview mode shows empty or incorrect content.

**Solutions:**
- Ensure you're in preview mode (check status bar)
- Press `Esc` to exit preview and try again
- Refresh marketplace data with `r`
- Check plugin has valid customizations

---

## Additional Resources

- [CLAUDE.md](../CLAUDE.md) - Project overview and development guide
- [docs/constitution.md](./constitution.md) - Design principles
- [Claude Code Documentation](https://docs.claude.ai) - Official Claude Code docs
- [GitHub Repository](https://github.com/NikiforovAll/lazyclaude) - Source code
- [GitHub Issues](https://github.com/NikiforovAll/lazyclaude/issues) - Report bugs or request features

---

**Version:** 0.11.0
**Last Updated:** 2025-12-20
