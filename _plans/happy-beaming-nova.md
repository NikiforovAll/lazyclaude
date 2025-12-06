# Plugin Support for LazyClaude

## Summary

Add plugin support to display Claude Code plugin components (slash commands, subagents, skills, MCPs) with plugin name prefix and filter functionality.

## User Requirements

- **Display**: `handbook:commit` - prefix with plugin short name (no level indicator for plugins)
- **Disabled plugins**: Hide entirely (not shown in UI)
- **Filtering**: Add `g` key to filter plugin-level components

## Files to Modify

| File | Changes |
|------|---------|
| `src/lazyclaude/models/customization.py` | Add `PLUGIN` ConfigLevel, `PluginInfo` dataclass, update `display_name` |
| `src/lazyclaude/services/discovery.py` | Add `_discover_plugins()` and JSON loading methods |
| `src/lazyclaude/app.py` | Add `g` keybinding, `action_filter_plugin()`, update help text |

## Implementation Steps

### 1. Model Layer (`src/lazyclaude/models/customization.py`)

Add `PluginInfo` dataclass:
```python
@dataclass
class PluginInfo:
    plugin_id: str       # "handbook@cc-handbook"
    short_name: str      # "handbook"
    version: str         # "1.3.1"
    install_path: Path
    is_local: bool = False
```

Add to `ConfigLevel`:
```python
PLUGIN = auto()  # ~/.claude/plugins/{plugin}/
```

Add field to `Customization`:
```python
plugin_info: PluginInfo | None = None
```

Update `display_name` property:
```python
# For plugins: just prefix with plugin name, no level indicator
if self.plugin_info:
    return f"{self.plugin_info.short_name}:{self.name}"
# For other levels: use existing indicator pattern
return f"{self.name} {level_indicator[self.level]}"
```

Update `level_label`:
```python
ConfigLevel.PLUGIN: "Plugin"
```

### 2. Discovery Service (`src/lazyclaude/services/discovery.py`)

Add import:
```python
import json
```

Add new methods:

1. `_load_installed_plugins()` - Read `~/.claude/plugins/installed_plugins.json`
2. `_load_enabled_plugins()` - Read `enabledPlugins` from `~/.claude/settings.json`
3. `_create_plugin_info(plugin_id, plugin_data)` - Create PluginInfo, extract short_name from ID
4. `_discover_plugin_slash_commands(install_path, plugin_info)` - Scan `commands/` dir
5. `_discover_plugin_subagents(install_path, plugin_info)` - Scan `agents/` dir
6. `_discover_plugin_skills(install_path, plugin_info)` - Scan `skills/` dir
7. `_discover_plugin_mcps(install_path, plugin_info)` - Parse `.mcp.json` if exists
8. `_discover_plugins()` - Orchestrate plugin discovery

Call `_discover_plugins()` from `discover_all()`.

Key logic:
- Skip plugins where `enabledPlugins[plugin_id] == false`
- Reuse existing parsers with `ConfigLevel.PLUGIN`
- Set `plugin_info` on returned customizations

### 3. App Layer (`src/lazyclaude/app.py`)

Add binding:
```python
Binding("g", "filter_plugin", "Plugin"),
```

Add action:
```python
def action_filter_plugin(self) -> None:
    """Show only plugin-level customizations."""
    self._level_filter = ConfigLevel.PLUGIN
    self._update_panels()
    self._update_subtitle()
    self._update_status_filter("Plugin")
```

Update `_update_subtitle()`:
```python
elif self._level_filter == ConfigLevel.PLUGIN:
    parts.append("Plugin Level")
```

Update `_update_status_filter()`:
```python
elif level == "Plugin":
    self._status_panel.config_path = "~/.claude/plugins"
```

Update help text (line 349):
```
  g              Show plugin-level only
```

## Data Sources

- `~/.claude/plugins/installed_plugins.json` - All installed plugins with `installPath`
- `~/.claude/settings.json` → `enabledPlugins` - Which plugins are enabled

## Plugin Structure (same as user folder)

```
{installPath}/
├── commands/*.md     → Slash commands
├── agents/*.md       → Subagents
├── skills/*/SKILL.md → Skills
└── .mcp.json         → MCP servers (optional)
```

## Error Handling

- Missing JSON files → Return empty dict, skip plugin discovery
- Invalid JSON → Catch `JSONDecodeError`, return defaults
- Missing `installPath` → Skip that plugin
- Non-existent install directory → Skip that plugin

---
# This file is a copy of original plan ~/.claude/plans/happy-beaming-nova.md
