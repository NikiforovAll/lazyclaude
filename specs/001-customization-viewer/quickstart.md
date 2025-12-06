# Quickstart: LazyClaude Development

**Feature**: 001-customization-viewer
**Date**: 2025-12-06

## Prerequisites

- Python 3.11+
- uv package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))

## Setup

```bash
# Clone and enter project
cd lazyclaude

# Install dependencies
uv sync

# Verify installation
uv run lazyclaude --version
```

## Development Commands

```bash
# Run the application
uv run lazyclaude

# Run with specific directory
uv run lazyclaude /path/to/project

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=lazyclaude

# Run snapshot tests (update on first run)
uv run pytest tests/snapshots --snapshot-update

# Lint code
uv run ruff check src tests

# Format code
uv run ruff format src tests

# Type check
uv run mypy src
```

## Project Structure

```
lazyclaude/
├── src/lazyclaude/       # Main package
│   ├── app.py            # Textual App class
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── widgets/          # UI components
│   └── styles/           # TCSS styles
├── tests/                # Test suite
├── specs/                # Feature specifications
└── pyproject.toml        # Project config
```

## Running Tests

### Unit Tests

```bash
# All unit tests
uv run pytest tests/unit

# Specific test file
uv run pytest tests/unit/test_parsers.py

# With verbose output
uv run pytest tests/unit -v
```

### Integration Tests

```bash
# All integration tests
uv run pytest tests/integration

# Run app tests
uv run pytest tests/integration/test_app.py
```

### Snapshot Tests

```bash
# Run snapshot tests
uv run pytest tests/snapshots

# Update snapshots after visual changes
uv run pytest tests/snapshots --snapshot-update
```

## Writing Tests

### Testing Widgets

```python
import pytest
from textual.testing import Pilot

from lazyclaude.app import LazyClaude

@pytest.mark.asyncio
async def test_navigation():
    app = LazyClaude()
    async with app.run_test() as pilot:
        # Simulate keypresses
        await pilot.press("j")  # Move down
        await pilot.press("enter")  # Drill into detail

        # Assert state
        assert app.detail_pane.customization is not None
```

### Testing Services

```python
from pathlib import Path
from lazyclaude.services.discovery import ConfigDiscoveryService

def test_discover_slash_commands(tmp_path: Path):
    # Setup test fixtures
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "test.md").write_text("# Test command")

    # Test service
    service = ConfigDiscoveryService(project_config_path=tmp_path)
    results = service.discover_by_type(CustomizationType.SLASH_COMMAND)

    assert len(results) == 1
    assert results[0].name == "test"
```

## Adding New Features

1. **Update spec** if requirements change
2. **Update data model** if new entities needed
3. **Update contracts** if new services needed
4. **Write tests first** (TDD recommended)
5. **Implement feature**
6. **Run constitution check** - verify keyboard-first, panel layout compliance

## Constitution Compliance Checklist

Before submitting changes, verify:

- [ ] Every action has a keyboard shortcut
- [ ] Vim-like navigation (j/k/h/l) works
- [ ] Enter drills down, Esc goes back
- [ ] No modals for simple operations
- [ ] All widgets are Textual-native
- [ ] CSS-based styling only

## Common Issues

### "Module not found" errors

```bash
# Ensure you're using uv's environment
uv run python -c "import lazyclaude; print(lazyclaude.__file__)"
```

### Test fixtures not found

```bash
# Run tests from project root
cd /path/to/lazyclaude
uv run pytest
```

### Snapshot test failures after legitimate changes

```bash
# Review and update snapshots
uv run pytest tests/snapshots --snapshot-update
# Then review the generated SVG files
```

## Publishing

```bash
# Build package
uv build

# Publish to PyPI (requires credentials)
uv publish

# After publishing, users can run:
uvx lazyclaude
```
