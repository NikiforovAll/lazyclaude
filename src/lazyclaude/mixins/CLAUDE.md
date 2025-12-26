# Mixins Module

This module contains mixin classes that extend `LazyClaude` app functionality through multiple inheritance.

## Architecture

```python
class LazyClaude(
    NavigationMixin,      # Panel focus & navigation
    FilterMixin,          # Level/search filtering
    MarketplaceMixin,     # Plugin marketplace browser
    CustomizationActionsMixin,  # Copy/move/delete operations
    HelpMixin,            # Help overlay
    App,                  # Textual base class (must be last)
):
```

## Mixin Overview

| Mixin | Purpose | Key Methods |
|-------|---------|-------------|
| `NavigationMixin` | Panel focus, view switching | `action_focus_panel_*`, `action_prev/next_view`, `action_back` |
| `FilterMixin` | Level filters, search | `action_filter_*`, `action_search`, `_update_status_filter` |
| `MarketplaceMixin` | Plugin browser, preview mode | `action_toggle_marketplace`, `on_marketplace_modal_*` |
| `CustomizationActionsMixin` | CRUD operations | `action_copy/move/delete_customization`, `on_*_confirm_*` |
| `HelpMixin` | Help overlay toggle | `action_toggle_help`, `_show_help`, `_hide_help` |

## How Mixins Work

1. **Method Resolution Order (MRO)**: Python resolves methods left-to-right, then up. Textual's `action_*` and `on_*` method discovery works via MRO.

2. **Shared State**: Mixins access app state through `self._*` attributes defined in `LazyClaude.__init__`.

3. **Type Hints**: Use `TYPE_CHECKING` guard to avoid circular imports:
   ```python
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from lazyclaude.widgets.type_panel import TypePanel

   class NavigationMixin:
       _panels: list["TypePanel"]  # Type stub for IDE support
   ```

4. **Cross-Mixin Calls**: Use `# type: ignore[attr-defined]` for methods defined in other mixins or App:
   ```python
   self._update_panels()  # type: ignore[attr-defined]
   self.notify("message")  # type: ignore[attr-defined]
   ```

## Adding New Functionality

1. Identify if functionality belongs in existing mixin or needs new one
2. For new mixin:
   - Create `mixins/<name>.py`
   - Define class with type stubs for accessed attributes
   - Export from `mixins/__init__.py`
   - Add to `LazyClaude` inheritance (before `App`)
3. For existing mixin: add methods directly

## File Responsibilities

- `navigation.py`: Focus management, panel switching, view toggling
- `filtering.py`: ConfigLevel filters, search query, status updates
- `marketplace.py`: Plugin browser, preview mode, plugin commands
- `customization_actions.py`: Copy/move/delete, level selector, confirmations
- `help.py`: Help overlay display
