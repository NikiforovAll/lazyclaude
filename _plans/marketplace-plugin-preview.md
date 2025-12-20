# Marketplace Plugin Preview - Implementation Plan

## Goal
When viewing a marketplace plugin, replicate the existing [1]-[6] panel layout to show:
- **Same panels**: Slash Commands, Subagents, Skills, Memory, MCPs, Hooks
- **Plugin's content**: Show what customizations the plugin provides
- **MainPane**: Show selected item content (same as normal mode)
- Works for **both installed and uninstalled** plugins

This gives users a full preview of plugin contents before installing.

## UX Flow
1. Press `M` to open marketplace (current modal or new view)
2. Navigate to a plugin, press `Enter` or `p` to preview
3. Sidebar shows plugin's [1]-[6] panels with its customizations
4. Browse like normal mode, MainPane shows content
5. Press `Esc` to return to marketplace browser

## Complexity Assessment: **Medium-High**

Key challenge: Loading customizations from plugin source directory (not installed path).

## Implementation Steps

### Step 1: Add plugin discovery to ConfigDiscoveryService
**File:** `src/lazyclaude/services/discovery.py`

Add method to discover customizations from a specific plugin directory (reuses existing `_discover_plugins` pattern):
```python
def discover_from_directory(
    self, plugin_dir: Path, plugin_info: PluginInfo | None = None
) -> list[Customization]:
    """Discover customizations from a specific directory (for plugin preview)."""
    customizations: list[Customization] = []
    level = ConfigLevel.PLUGIN

    # Scan for commands, agents, skills using existing SCAN_CONFIGS
    for config in SCAN_CONFIGS.values():
        customizations.extend(
            self._scanner.scan_directory(plugin_dir, config, level, plugin_info)
        )

    # Scan for MCPs and hooks using existing methods
    customizations.extend(self._discover_plugin_mcps(plugin_dir, plugin_info))
    customizations.extend(self._discover_plugin_hooks(plugin_dir, plugin_info))

    return self._sort_customizations(customizations)
```

### Step 2: Add plugin path resolution to MarketplaceLoader
**File:** `src/lazyclaude/services/marketplace_loader.py`

Add method to get plugin source directory:
```python
def get_plugin_source_dir(self, plugin: MarketplacePlugin) -> Path | None:
    """Get the source directory for a plugin (installed or from marketplace)."""
    # For installed: use install_path
    if plugin.install_path and plugin.install_path.exists():
        return plugin.install_path

    # For uninstalled: look in marketplace install_location/plugins/<name>/
    marketplace = self._find_marketplace(plugin.marketplace_name)
    if marketplace:
        return marketplace.entry.install_location / "plugins" / plugin.name
    return None
```

### Step 3: Add plugin preview mode to App
**File:** `src/lazyclaude/app.py`

Add state:
```python
self._plugin_preview_mode: bool = False
self._previewing_plugin: MarketplacePlugin | None = None
self._plugin_customizations: list[Customization] = []
```

Add preview action:
```python
def _enter_plugin_preview(self, plugin: MarketplacePlugin) -> None:
    """Enter plugin preview mode - show plugin's customizations in panels."""
    plugin_dir = self._marketplace_loader.get_plugin_source_dir(plugin)
    if not plugin_dir or not plugin_dir.exists():
        self.notify("Plugin source not found", severity="warning")
        return

    # Discover plugin's customizations
    self._plugin_customizations = self._discovery.discover_plugin_customizations(plugin_dir)
    self._previewing_plugin = plugin
    self._plugin_preview_mode = True

    # Hide marketplace modal/panel
    if self._marketplace_modal:
        self._marketplace_modal.hide()

    # Update panels with plugin customizations
    self._update_panels()  # Modified to use _plugin_customizations when in preview mode

    self._update_subtitle()  # Show "Preview: <plugin_name>"
```

Modify `_update_panels()`:
```python
def _update_panels(self) -> None:
    if self._plugin_preview_mode:
        # Use plugin customizations instead of global
        customizations = self._plugin_customizations
    else:
        customizations = self._filter_service.filter(...)
    # ... rest of panel update logic
```

Exit preview:
```python
def _exit_plugin_preview(self) -> None:
    self._plugin_preview_mode = False
    self._previewing_plugin = None
    self._plugin_customizations = []
    self._update_panels()
    self._update_subtitle()
    # Re-show marketplace
    if self._marketplace_modal:
        self._marketplace_modal.show()
```

### Step 4: Add preview binding to MarketplaceModal
**File:** `src/lazyclaude/widgets/marketplace_modal.py`

Add binding and message:
```python
Binding("enter", "preview_plugin", "Preview", show=False),
# or
Binding("p", "preview_plugin", "Preview", show=False),

class PluginPreview(Message):
    def __init__(self, plugin: MarketplacePlugin) -> None:
        self.plugin = plugin
        super().__init__()

def action_preview_plugin(self) -> None:
    node = self._tree.cursor_node
    if node and isinstance(node.data, MarketplacePlugin):
        self.post_message(self.PluginPreview(node.data))
```

Update footer for plugins:
```python
"[bold]Enter[/] Preview  [bold]i[/] Install  ..."
```

### Step 5: Handle Esc in preview mode
**File:** `src/lazyclaude/app.py`

Modify escape handling:
```python
def action_escape(self) -> None:
    if self._plugin_preview_mode:
        self._exit_plugin_preview()
    elif self._marketplace_modal and self._marketplace_modal.is_visible:
        # ... existing modal close logic
```

### Step 6: Update StatusPanel/subtitle
Show current mode in status:
- Normal: `~/.claude | All`
- Preview: `Preview: handbook | Plugin`

## Files Summary

| File | Action | Changes |
|------|--------|---------|
| `src/lazyclaude/services/discovery.py` | Modify | Add `discover_from_directory()` method |
| `src/lazyclaude/services/marketplace_loader.py` | Modify | Add `get_plugin_source_dir()` method |
| `src/lazyclaude/app.py` | Modify | Add preview mode state, handlers, modify `_update_panels()` |
| `src/lazyclaude/widgets/marketplace_modal.py` | Modify | Add `Enter` preview binding, `PluginPreview` message |

## Key Advantages

1. **Full reuse**: All existing panels, MainPane, navigation work as-is
2. **Accurate preview**: Users see exactly what they'll get
3. **No new widgets**: Just mode switching and customization source change
4. **Works for uninstalled**: Load from marketplace source directory

---
# This file is a copy of original plan ~/.claude/plans/abundant-baking-rose.md
