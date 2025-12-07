# Plan: Refactor ConfigDiscoveryService (task-04)

## Goal
Reduce `ConfigDiscoveryService` from 447 lines to ~150 lines by extracting concerns into dedicated modules.

**Constraint**: Safe refactoring - keep `IConfigDiscoveryService` interface unchanged, rely on existing integration tests.

## Target Architecture
```
src/lazyclaude/services/
├── discovery.py           # Coordinator only (~130-150 lines)
├── plugin_loader.py       # Plugin registry management (~80-100 lines)
├── filesystem_scanner.py  # Generic file discovery (~60-80 lines)
└── parsers/               # Unchanged
```

## Key Design Decisions

### 1. FilesystemScanner (`filesystem_scanner.py`)
Eliminates duplication in `_discover_slash_commands`, `_discover_subagents`, `_discover_skills` and their plugin variants.

```python
class GlobStrategy(Enum):
    RGLOB = "rglob"   # commands/**/*.md (nested)
    GLOB = "glob"     # agents/*.md (flat)
    SUBDIR = "subdir" # skills/*/SKILL.md

@dataclass
class ScanConfig:
    subdir: str                           # e.g., "commands"
    pattern: str                          # e.g., "*.md"
    strategy: GlobStrategy
    parser_factory: Callable[[Path], IParser]

class FilesystemScanner:
    def scan_directory(self, base_path, config, level, plugin_info=None) -> list[Customization]
```

### 2. PluginLoader (`plugin_loader.py`)
Extracts plugin loading from discovery.py. Moves `_load_installed_plugins`, `_load_enabled_plugins`, `_create_plugin_info`.

```python
@dataclass
class PluginRegistry:
    installed: dict[str, dict[str, Any]]
    enabled: dict[str, bool]

class PluginLoader:
    def __init__(self, user_config_path: Path)
    def load_registry(self) -> PluginRegistry
    def get_enabled_plugins(self) -> list[PluginInfo]
    def refresh(self) -> None
```

### 3. ConfigDiscoveryService (refactored)
- **NO interface changes** - constructor signature stays the same
- Creates `FilesystemScanner` and `PluginLoader` internally
- `discover_all()` uses scanner for slash_commands, subagents, skills
- Keep special methods: `_discover_memory_files`, `_discover_mcps`, `_discover_hooks` (unique patterns)
- Plugin discovery delegates to scanner + loader

## Implementation Steps

### Phase 1: Extract FilesystemScanner
1. Create `src/lazyclaude/services/filesystem_scanner.py`
   - `GlobStrategy` enum
   - `ScanConfig` dataclass
   - `FilesystemScanner` class
2. Run integration tests to ensure no regressions

### Phase 2: Extract PluginLoader
1. Create `src/lazyclaude/services/plugin_loader.py`
   - `PluginRegistry` dataclass
   - `PluginLoader` class (move `_load_installed_plugins`, `_load_enabled_plugins`, `_create_plugin_info`)
2. Run integration tests

### Phase 3: Refactor ConfigDiscoveryService
1. Import and instantiate `FilesystemScanner` and `PluginLoader` in `__init__`
2. Define `SCAN_CONFIGS` dict for slash_commands, subagents, skills
3. Replace 6 `_discover_*` methods with scanner calls
4. Replace 5 `_discover_plugin_*` methods with scanner + loader
5. Keep `_discover_memory_files`, `_discover_mcps`, `_discover_hooks` (unique patterns)
6. Run full test suite

### Phase 4: Cleanup
1. Remove dead code from discovery.py
2. Verify line count target met

## Critical Files

| File | Action |
|------|--------|
| `src/lazyclaude/services/discovery.py` | Refactor (447 → ~150 lines) |
| `src/lazyclaude/services/filesystem_scanner.py` | Create (~70 lines) |
| `src/lazyclaude/services/plugin_loader.py` | Create (~90 lines) |

## Test Strategy
Rely on existing integration tests in `tests/integration/discovery/`:
- `test_behavior.py` - caching, refresh, edge cases
- `test_slash_commands.py`, `test_subagents.py`, `test_skills.py`
- `test_memory_files.py`, `test_mcps.py`, `test_hooks.py`
- `test_plugins.py` - plugin discovery

Run `uv run pytest tests/integration/discovery/` after each phase.

## Acceptance Criteria
- [ ] ConfigDiscoveryService < 150 lines
- [ ] PluginLoader extracted to separate module
- [ ] Generic discovery pattern eliminates code duplication
- [ ] All existing integration tests pass
- [ ] IConfigDiscoveryService interface unchanged

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Glob strategy mismatch | Integration tests catch any regressions |
| Plugin path resolution breaks | Keep original logic as reference |
| Integration tests fail | Run tests after each incremental change |

---

# This file is a copy of original plan ~/.claude/plans/enchanted-toasting-goose.md
