# Marketplace Browser Modal Implementation Plan

## Overview
Add a marketplace browser modal to LazyClaude that displays available plugins from configured marketplaces in a tree structure, allowing users to browse and toggle/install plugins.

## Requirements
- **Trigger**: `Ctrl+m` keyboard shortcut
- **Size**: 80% of screen (large overlay modal)
- **Tree Structure**: Marketplace → Plugins (flat) using Textual Tree widget
- **Toggle Action ('i')**: Combined behavior - install if not installed, toggle enabled state if installed
- **Uninstall Action ('d')**: Uninstall an installed plugin
- **Close**: `Escape` to close modal

## Data Sources
- Index: `~/.claude/plugins/known_marketplaces.json`
- Per-marketplace: `<installLocation>/.claude-plugin/marketplace.json`

## Implementation Steps

### Step 1: Create Marketplace Models
**File**: `src/lazyclaude/models/marketplace.py`

Create dataclasses:
- `MarketplaceSource` - source type (github/directory), repo, path
- `MarketplaceEntry` - name, source, install_location, last_updated
- `MarketplacePlugin` - name, description, source, marketplace_name, full_plugin_id, is_installed, is_enabled
- `Marketplace` - entry, plugins list, error string

### Step 2: Create MarketplaceLoader Service
**File**: `src/lazyclaude/services/marketplace_loader.py`

Service that:
- Reads `known_marketplaces.json` index file
- Loads `marketplace.json` from each marketplace's install location
- Checks installed state via PluginLoader registry
- Checks enabled state via settings.json enabledPlugins dict

### Step 3: Create MarketplaceModal Widget
**File**: `src/lazyclaude/widgets/marketplace_modal.py`

Widget using Textual Tree with:
- Header: "Marketplace Browser" title with keybinding hints
- Tree: Marketplaces as expandable roots, plugins as leaves
- Footer: Keybinding reference
- Bindings: `escape` (close), `i` (install/toggle), `d` (uninstall), `j/k` (navigation), `enter` (expand)
- Messages: `PluginToggled(plugin)`, `PluginUninstall(plugin)`, `ModalClosed()`
- Status icons in labels: `[green]I[/]` (installed+enabled), `[yellow]D[/]` (disabled), `[ ]` (not installed)

CSS positioning:
```css
MarketplaceModal {
    display: none;
    layer: overlay;
    width: 80%;
    height: 80%;
    border: double $accent;
    background: $surface;
}
MarketplaceModal.visible {
    display: block;
    align: center middle;
}
```

### Step 4: Update app.tcss
**File**: `src/lazyclaude/styles/app.tcss`

Add MarketplaceModal styles (can also use DEFAULT_CSS in widget).

### Step 5: Integrate with App
**File**: `src/lazyclaude/app.py`

1. Add import: `from lazyclaude.widgets.marketplace_modal import MarketplaceModal`
2. Add binding: `Binding("ctrl+m", "open_marketplace", "Marketplace", show=True)`
3. Add instance vars in `__init__`: `_marketplace_modal`, `_marketplace_loader`
4. Yield modal in `compose()` after `_delete_confirm`
5. Initialize loader in `on_mount()`
6. Add action: `action_open_marketplace()` - calls `_marketplace_modal.show()`
7. Add message handlers:
   - `on_marketplace_modal_plugin_toggled()` - handle toggle/install
   - `on_marketplace_modal_modal_closed()` - restore focus

### Step 6: Update Exports
- `src/lazyclaude/widgets/__init__.py` - add MarketplaceModal
- `src/lazyclaude/models/__init__.py` - add marketplace models

## Critical Files to Modify/Create
| File | Action |
|------|--------|
| `src/lazyclaude/models/marketplace.py` | Create |
| `src/lazyclaude/services/marketplace_loader.py` | Create |
| `src/lazyclaude/widgets/marketplace_modal.py` | Create |
| `src/lazyclaude/app.py` | Modify |
| `src/lazyclaude/widgets/__init__.py` | Modify |
| `src/lazyclaude/models/__init__.py` | Modify |

## Action Behavior Logic

Uses Claude CLI commands:
- `claude plugin install <plugin>` - Install a plugin from marketplace
- `claude plugin enable <plugin>` - Enable a disabled plugin
- `claude plugin disable <plugin>` - Disable an enabled plugin
- `claude plugin uninstall <plugin>` - Uninstall an installed plugin

```python
# 'i' key - Install/Toggle
def on_marketplace_modal_plugin_toggled(self, message):
    plugin = message.plugin

    if not plugin.is_installed:
        cmd = ["claude", "plugin", "install", plugin.full_plugin_id]
        subprocess.run(cmd, check=True)
        self.notify(f"Installed {plugin.name}")
    elif plugin.is_enabled:
        cmd = ["claude", "plugin", "disable", plugin.full_plugin_id]
        subprocess.run(cmd, check=True)
        self.notify(f"Disabled {plugin.name}")
    else:
        cmd = ["claude", "plugin", "enable", plugin.full_plugin_id]
        subprocess.run(cmd, check=True)
        self.notify(f"Enabled {plugin.name}")

    self._marketplace_modal.refresh_tree()
    self.action_refresh()

# 'd' key - Uninstall
def on_marketplace_modal_plugin_uninstall(self, message):
    plugin = message.plugin
    if not plugin.is_installed:
        self.notify("Plugin not installed", severity="warning")
        return

    cmd = ["claude", "plugin", "uninstall", plugin.full_plugin_id]
    subprocess.run(cmd, check=True)
    self.notify(f"Uninstalled {plugin.name}")

    self._marketplace_modal.refresh_tree()
    self.action_refresh()
```

## Future Enhancements (Out of Scope)
- Search/filter within marketplace
- Plugin details drill-down view
- Version comparison for updates

# This file is a copy of original plan ~/.claude/plans/jaunty-waddling-mango.md
