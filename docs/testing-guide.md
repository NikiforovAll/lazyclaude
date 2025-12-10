# LazyClaude Testing Guide

This comprehensive guide documents testing patterns, architecture, and best practices for the LazyClaude project.

For quick reference rules when writing tests, see `.claude/rules/testing.md`.

## Table of Contents


## Testing Philosophy

### When to Write Tests

Write tests for:

- **All service layer code** - Business logic in `src/lazyclaude/services/`
- **Data transformation logic** - Parsers, formatters, converters
- **File operations** - Reading, writing, discovery operations
- **State management** - Configuration handling, caching
- **Edge cases** - Error conditions, boundary cases, platform-specific behavior

### Test Scope

- **Unit tests** (`tests/unit/`) - Test individual services or components in isolation with mocked dependencies
- **Integration tests** (`tests/integration/`) - Test services working together with real implementations and fake filesystem
- **No UI tests yet** - Textual widget testing infrastructure exists but not actively used

### Test Quality Standards

- All tests MUST pass consistently
- Tests MUST be isolated (no shared state between tests)
- Tests MUST be fast (use fake filesystem, minimize I/O)
- Tests MUST be maintainable (clear names, good organization)
- Tests MUST cover edge cases (empty data, missing files, malformed input)

## Test Organization

### Directory Structure

```
tests/
├── conftest.py                      # Shared pytest fixtures
├── unit/                            # Unit tests for individual components
│   ├── test_config_path_resolver.py
│   ├── test_customization_writer.py
│   ├── test_plugin_source_path.py
│   └── test_level_selector.py
└── integration/
    ├── discovery/                   # Integration tests for discovery service
    │   ├── test_behavior.py         # Caching, refresh, path resolution
    │   ├── test_hooks.py
    │   ├── test_mcps.py
    │   ├── test_memory_files.py
    │   ├── test_plugins.py
    │   ├── test_skills.py
    │   ├── test_slash_commands.py
    │   └── test_subagents.py
    └── fixtures/                    # Test data fixtures
        ├── commands/
        ├── agents/
        ├── skills/
        ├── memory/
        ├── mcp/
        ├── plugins/
        ├── project/
        └── settings/
```

### Naming Conventions

#### Test Files

Pattern: `test_<module_name>.py`

Examples:
- `test_config_path_resolver.py` - Tests for `config_path_resolver.py` module
- `test_customization_writer.py` - Tests for `customization_writer.py` module
- `test_behavior.py` - Tests for service behavior (caching, refresh)

#### Test Classes

Pattern: `Test<ClassName>` or `Test<Behavior>`

Examples from `test_config_path_resolver.py`:
```python
class TestResolveFile:
    """Tests for resolve_file method."""
    pass

class TestResolvePath:
    """Tests for resolve_path method with arbitrary file paths."""
    pass
```

Examples from `test_behavior.py`:
```python
class TestMultiLevelDiscovery:
    """Tests for discover_all and discover_by_level."""
    pass

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    pass
```

#### Test Methods

Pattern: `test_<scenario>_<expected_outcome>`

Examples:
```python
def test_non_plugin_level_returns_path_as_is(self) -> None:
    """Non-plugin customizations return their path unchanged."""

def test_discovers_user_slash_commands(self, user_config_path: Path, fake_project_root: Path) -> None:
    """Discovery service finds user-level slash commands."""

def test_conflict_detection_returns_error(self, fs, fake_home: Path, fake_project_root: Path) -> None:
    """Writer detects existing files and returns error."""
```

### Class-Based Organization

Group related tests into classes. Each class tests one specific behavior or aspect of functionality.

Example from `test_config_path_resolver.py`:
```python
class TestResolveFile:
    """Tests for resolve_file method."""

    def test_non_plugin_level_returns_path_as_is(self) -> None:
        """Non-plugin customizations return their path unchanged."""
        mock_loader = Mock()
        resolver = ConfigPathResolver(mock_loader)

        customization = Customization(
            name="test",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.USER,
            path=Path("/home/user/.claude/commands/test.md"),
            content="test",
        )

        result = resolver.resolve_file(customization)

        assert result == Path("/home/user/.claude/commands/test.md")
        mock_loader.get_plugin_source_path.assert_not_called()

    def test_plugin_without_plugin_info_returns_path_as_is(self) -> None:
        """Plugin customization without plugin_info returns path unchanged."""
        # ... more tests for resolve_file behavior
```

## Fixture Architecture

### Shared Fixtures in conftest.py

The `tests/conftest.py` file contains shared fixtures used across all tests. These fixtures provide isolated filesystem environments and test configuration.

#### Core Fixtures

**fake_home** - Fake home directory:
```python
@pytest.fixture
def fake_home(fs: FakeFilesystem) -> Generator[Path, None, None]:
    """Create a fake home directory and patch Path.home() to return it."""
    fs.create_dir(FAKE_HOME)
    os.environ["HOME"] = str(FAKE_HOME)
    os.environ["USERPROFILE"] = str(FAKE_HOME)

    with patch.object(Path, "home", return_value=FAKE_HOME):
        yield FAKE_HOME
```

Where `FAKE_HOME = Path("/fake/home")` is a constant defined at module level.

**fake_project_root** - Fake project directory:
```python
@pytest.fixture
def fake_project_root(fs: FakeFilesystem) -> Path:
    """Create a fake project root directory."""
    project = Path("/fake/project")
    fs.create_dir(project)
    return project
```

#### Configuration Fixtures

These fixtures build on the core fixtures using the **composition pattern**:

**user_config_path** - User configuration with test data:
```python
@pytest.fixture
def user_config_path(fake_home: Path, fs: FakeFilesystem) -> Path:
    """Create user config directory (~/.claude) with fixtures."""
    user_claude = fake_home / ".claude"
    fs.create_dir(user_claude)

    # Add real fixture files from tests/integration/fixtures/
    fs.add_real_directory(
        FIXTURES_DIR / "commands",
        target_path=user_claude / "commands",
        read_only=False,
    )
    fs.add_real_directory(
        FIXTURES_DIR / "agents",
        target_path=user_claude / "agents",
        read_only=False,
    )
    # ... more fixtures

    return user_claude
```

**full_user_config** - Complete user configuration:
```python
@pytest.fixture
def full_user_config(
    user_config_path: Path,
    user_mcp_config: Path,  # noqa: ARG001
    plugins_config: Path,  # noqa: ARG001
) -> Path:
    """Complete user configuration with all customization types."""
    return user_config_path
```

This fixture depends on other fixtures but doesn't use their values directly (hence the `noqa: ARG001` comments). The dependencies ensure all components are set up before this fixture returns.

### Fixture Composition Pattern

Fixtures can depend on other fixtures, creating a hierarchy:

```
fake_home (base)
  └─> user_config_path (adds fixture data)
      └─> full_user_config (adds MCP + plugins)
```

Example usage in a test:
```python
def test_discovers_user_slash_commands(
    self, user_config_path: Path, fake_project_root: Path
) -> None:
    """Discovery service finds user-level slash commands."""
    service = ConfigDiscoveryService(
        user_config_path=user_config_path,
        project_config_path=fake_project_root / ".claude",
    )

    commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

    user_commands = [c for c in commands if c.level == ConfigLevel.USER]
    assert len(user_commands) == 2
```

### Fixture Scope

- **Function-scoped (default)** - Fixtures are created fresh for each test function
- Ensures test isolation
- No shared state between tests
- Tests can run in any order

### Using Fixtures in Tests

Fixtures are injected via function parameters:

```python
def test_example(self, fs: FakeFilesystem, fake_home: Path, user_config_path: Path) -> None:
    """Example showing fixture injection."""
    # fs, fake_home, and user_config_path are automatically provided by pytest
    # Each is isolated to this test
```

## Filesystem Testing with pyfakefs

### Why pyfakefs?

The project uses [pyfakefs](https://pytest-pyfakefs.readthedocs.io/) to:

- Isolate tests from the real filesystem
- Make tests fast (no actual disk I/O)
- Provide repeatable test environments
- Avoid cleanup issues

### Core Patterns

#### Creating Directories

```python
def test_example(self, fs: FakeFilesystem, fake_home: Path) -> None:
    user_config = fake_home / ".claude"
    fs.create_dir(user_config)
    fs.create_dir(user_config / "commands")
```

#### Creating Files

```python
def test_example(self, fs: FakeFilesystem, fake_home: Path) -> None:
    test_file = fake_home / ".claude" / "commands" / "test.md"
    fs.create_file(test_file, contents="# Test Command\nTest content")

    # File now exists in fake filesystem
    assert test_file.exists()
    assert test_file.read_text() == "# Test Command\nTest content"
```

#### Adding Real Fixture Files

Use `fs.add_real_file()` to add actual fixture files from `tests/integration/fixtures/`:

```python
@pytest.fixture
def user_mcp_config(fake_home: Path, fs: FakeFilesystem) -> Path:
    """Create user-level MCP config (~/.claude.json)."""
    mcp_path = fake_home / ".claude.json"
    fs.add_real_file(
        FIXTURES_DIR / "mcp" / "user.claude.json",
        target_path=mcp_path,
        read_only=False,
    )
    return mcp_path
```

#### Adding Real Fixture Directories

Use `fs.add_real_directory()` for directories:

```python
fs.add_real_directory(
    FIXTURES_DIR / "commands",
    target_path=user_claude / "commands",
    read_only=False,
)
```

### Filesystem Conventions

Use consistent paths across all tests:

```python
FAKE_HOME = Path("/fake/home")            # User home directory
fake_project_root = Path("/fake/project")  # Project root directory
```

This makes tests predictable and easier to understand.

### Example: Complete Filesystem Test

From `test_customization_writer.py`:

```python
def test_write_slash_command_to_user_level(
    self, fs, fake_home: Path, fake_project_root: Path
) -> None:
    """Writer copies slash command file to user level."""
    # Arrange: Set up fake filesystem
    user_config = fake_home / ".claude"
    fs.create_dir(user_config)

    test_file = fake_project_root / "test.md"
    fs.create_file(test_file, contents="# Test Command\nTest content")

    customization = Customization(
        name="test",
        type=CustomizationType.SLASH_COMMAND,
        level=ConfigLevel.PROJECT,
        path=test_file,
        content="# Test Command\nTest content",
    )

    # Act: Perform the operation
    writer = CustomizationWriter()
    success, msg = writer.write_customization(
        customization,
        ConfigLevel.USER,
        user_config,
        fake_project_root / ".claude",
    )

    # Assert: Verify the outcome
    assert success is True
    assert "Copied 'test' to User level" in msg
    target_path = user_config / "commands" / "test.md"
    assert target_path.exists()
    assert target_path.read_text() == "# Test Command\nTest content"
```

## Async Testing Patterns

### Configuration

Async testing is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

- `asyncio_mode = "auto"` - Automatically detect and run async tests
- Function-scoped event loop for isolation

### Decorator

Use `@pytest.mark.asyncio` for async test methods:

```python
@pytest.mark.asyncio
async def test_async_operation(self) -> None:
    """Test an async operation."""
    result = await some_async_function()
    assert result is not None
```

### Message Capture Pattern

For testing Textual widgets that post messages, replace async methods with synchronous mocks:

Example from `test_level_selector.py`:

```python
@pytest.mark.asyncio
async def test_select_user_posts_message_when_available(self) -> None:
    """action_select_user should post LevelSelected when USER is available."""
    selector = LevelSelector()
    selector._available_levels = [ConfigLevel.USER, ConfigLevel.PROJECT]

    # Capture messages in a list
    messages: list[LevelSelector.LevelSelected] = []

    def capture_message(msg: LevelSelector.LevelSelected) -> None:
        messages.append(msg)

    # Replace async method with sync mock
    selector.post_message = capture_message  # type: ignore

    # Trigger action
    selector.action_select_user()

    # Verify message was posted
    assert len(messages) == 1
    assert messages[0].level == ConfigLevel.USER
```

### Common Async Patterns

**Mocking async widget methods:**
```python
selector.hide = lambda: None  # type: ignore
selector.focus = lambda: None  # type: ignore
selector.post_message = capture_message  # type: ignore
```

**Testing async service methods:**
```python
@pytest.mark.asyncio
async def test_async_service_method(self) -> None:
    """Service method performs async operation."""
    service = MyService()
    result = await service.async_method()
    assert result is not None
```

## Mocking Strategies

### When to Mock

Mock when:

- Testing a component that depends on external services
- The real implementation would be slow or unreliable
- You need to verify method calls or interactions
- Testing error conditions that are hard to trigger

DON'T mock when:

- You can use the real implementation with fake filesystem
- The code is simple and fast
- Over-mocking would hide integration issues

### Mock Library

Use `unittest.mock.Mock`:

```python
from unittest.mock import Mock

mock_loader = Mock()
mock_loader.get_plugin_source_path.return_value = Path("/dev/my-plugin")
```

### Mocking Service Dependencies

Example from `test_config_path_resolver.py`:

```python
def test_non_plugin_level_returns_path_as_is(self) -> None:
    """Non-plugin customizations return their path unchanged."""
    # Create mock dependency
    mock_loader = Mock()
    resolver = ConfigPathResolver(mock_loader)

    customization = Customization(
        name="test",
        type=CustomizationType.SLASH_COMMAND,
        level=ConfigLevel.USER,
        path=Path("/home/user/.claude/commands/test.md"),
        content="test",
    )

    result = resolver.resolve_file(customization)

    # Verify the mock was not called (path returned as-is)
    assert result == Path("/home/user/.claude/commands/test.md")
    mock_loader.get_plugin_source_path.assert_not_called()
```

### Mock Return Values

Set return values for mock methods:

```python
mock_loader = Mock()
mock_loader.get_plugin_source_path.return_value = Path("/dev/my-plugin")

# Now calling the method returns the configured value
result = mock_loader.get_plugin_source_path("plugin-id")
assert result == Path("/dev/my-plugin")
```

### Verifying Mock Calls

Common assertion patterns:

```python
# Verify method was called
mock_loader.get_plugin_source_path.assert_called()

# Verify method was NOT called
mock_loader.get_plugin_source_path.assert_not_called()

# Verify method was called with specific arguments
mock_loader.get_plugin_source_path.assert_called_with("plugin-id")

# Verify method was called once
mock_loader.get_plugin_source_path.assert_called_once()
```

### Integration Tests - Minimal Mocking

Integration tests prefer real implementations. Example from `test_behavior.py`:

```python
def test_discovers_user_slash_commands(
    self, user_config_path: Path, fake_project_root: Path
) -> None:
    """Integration test uses real service with fake filesystem."""
    # Real service, real parsers, fake filesystem
    service = ConfigDiscoveryService(
        user_config_path=user_config_path,
        project_config_path=fake_project_root / ".claude",
    )

    # Real discovery operation
    commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

    # Verify real results
    user_commands = [c for c in commands if c.level == ConfigLevel.USER]
    assert len(user_commands) == 2
```

## Type Hints in Tests

### Requirements

All test functions MUST include type hints:

- Test methods: `-> None`
- Fixtures: Appropriate return type
- MyPy enforces `disallow_untyped_defs = true`

### Test Method Type Hints

```python
def test_example(self) -> None:
    """Test methods always return None."""
    assert True

def test_with_fixtures(self, fs: FakeFilesystem, fake_home: Path) -> None:
    """Fixture parameters include types."""
    assert fake_home.exists()
```

### Fixture Type Hints

Simple fixtures:
```python
@pytest.fixture
def fake_project_root(fs: FakeFilesystem) -> Path:
    """Create a fake project root directory."""
    project = Path("/fake/project")
    fs.create_dir(project)
    return project
```

Generator fixtures:
```python
@pytest.fixture
def fake_home(fs: FakeFilesystem) -> Generator[Path, None, None]:
    """Create a fake home directory and patch Path.home() to return it."""
    fs.create_dir(FAKE_HOME)
    os.environ["HOME"] = str(FAKE_HOME)
    os.environ["USERPROFILE"] = str(FAKE_HOME)

    with patch.object(Path, "home", return_value=FAKE_HOME):
        yield FAKE_HOME
```

The `Generator[Path, None, None]` type means:
- Yields `Path` value
- No send value (second `None`)
- No return value (third `None`)

### Type Ignoring Mocks

When mocking methods with incompatible signatures, use `# type: ignore`:

```python
selector.post_message = capture_message  # type: ignore
selector.hide = lambda: None  # type: ignore
```

This tells MyPy to skip type checking for these lines, which is acceptable in tests.

## Edge Case Coverage

### Required Edge Cases

Tests MUST cover these edge cases where applicable:

1. **Empty data** - Empty directories, empty files, empty lists
2. **Missing data** - Nonexistent files/directories
3. **Malformed data** - Invalid YAML, invalid JSON, corrupt files
4. **Permission errors** - Unreadable/unwritable files
5. **Boundary conditions** - Zero, negative, maximum values
6. **Platform-specific behavior** - Windows vs Unix differences

### Empty Directories

From `test_behavior.py`:

```python
def test_empty_directories_returns_empty(self, fs: FakeFilesystem) -> None:
    """Service handles empty config directories gracefully."""
    user_config = Path("/empty/user/.claude")
    project_config = Path("/empty/project/.claude")
    fs.create_dir(user_config)
    fs.create_dir(project_config)

    service = ConfigDiscoveryService(
        user_config_path=user_config,
        project_config_path=project_config,
    )

    all_items = service.discover_all()

    assert all_items == []
```

### Missing Directories

```python
def test_missing_directories_handled_gracefully(
    self,
    fs: FakeFilesystem,  # noqa: ARG002
) -> None:
    """Service handles nonexistent directories without crashing."""
    user_config = Path("/nonexistent/user/.claude")
    project_config = Path("/nonexistent/project/.claude")

    service = ConfigDiscoveryService(
        user_config_path=user_config,
        project_config_path=project_config,
    )

    all_items = service.discover_all()

    assert all_items == []
```

### Malformed Data

**Malformed JSON:**
```python
def test_malformed_json_sets_error(self, fs: FakeFilesystem) -> None:
    """Parser sets error flag for malformed JSON."""
    user_config = Path("/test/user/.claude")
    project_config = Path("/test/project/.claude")
    project_root = Path("/test/project")
    fs.create_dir(user_config)
    fs.create_dir(project_config)
    fs.create_file(
        project_root / ".mcp.json",
        contents="{ invalid json }",
    )

    service = ConfigDiscoveryService(
        user_config_path=user_config,
        project_config_path=project_config,
    )

    mcps = service.discover_by_type(CustomizationType.MCP)

    assert len(mcps) == 1
    assert mcps[0].has_error
    assert "parse" in mcps[0].error.lower()
```

**Malformed YAML:**
```python
def test_malformed_yaml_frontmatter_falls_back_gracefully(
    self, fs: FakeFilesystem
) -> None:
    """Parser is lenient: malformed YAML frontmatter treated as no frontmatter."""
    user_config = Path("/test/user/.claude")
    project_config = Path("/test/project/.claude")
    fs.create_dir(user_config)
    fs.create_dir(project_config / "commands")
    fs.create_file(
        project_config / "commands" / "bad.md",
        contents="---\n[unclosed bracket\n---\n# Bad",
    )

    service = ConfigDiscoveryService(
        user_config_path=user_config,
        project_config_path=project_config,
    )

    commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

    bad_cmd = next((c for c in commands if c.name == "bad"), None)
    assert bad_cmd is not None
    assert not bad_cmd.has_error
    assert bad_cmd.metadata.get("allowed_tools") == []
```

### Permission Errors

Platform-specific testing with `@pytest.mark.skipif`:

```python
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Permission testing unreliable on Windows with pyfakefs",
)
def test_handles_permission_error(
    self, fs, fake_home: Path, fake_project_root: Path
) -> None:
    """Writer handles permission denied gracefully."""
    user_config = fake_home / ".claude"
    fs.create_dir(user_config)

    test_file = fake_project_root / "test.md"
    fs.create_file(test_file, contents="# Test")

    customization = Customization(
        name="test",
        type=CustomizationType.SLASH_COMMAND,
        level=ConfigLevel.PROJECT,
        path=test_file,
        content="# Test",
    )

    target_dir = user_config / "commands"
    fs.create_dir(target_dir)

    import os
    os.chmod(str(target_dir), 0o444)  # Read-only

    writer = CustomizationWriter()
    success, msg = writer.write_customization(
        customization,
        ConfigLevel.USER,
        user_config,
        fake_project_root / ".claude",
    )

    assert success is False
    assert "Permission denied" in msg or "Failed to copy" in msg
```

### Conflict Detection

```python
def test_conflict_detection_returns_error(
    self, fs, fake_home: Path, fake_project_root: Path
) -> None:
    """Writer detects file already exists and returns error."""
    user_config = fake_home / ".claude"
    fs.create_dir(user_config / "commands")
    fs.create_file(user_config / "commands" / "test.md", contents="Existing")

    test_file = fake_project_root / "test.md"
    fs.create_file(test_file, contents="New content")

    customization = Customization(
        name="test",
        type=CustomizationType.SLASH_COMMAND,
        level=ConfigLevel.PROJECT,
        path=test_file,
        content="New content",
    )

    writer = CustomizationWriter()
    success, msg = writer.write_customization(
        customization,
        ConfigLevel.USER,
        user_config,
        fake_project_root / ".claude",
    )

    assert success is False
    assert "already exists at User level" in msg
```

## Commands and Execution

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test directory
uv run pytest tests/unit/
uv run pytest tests/integration/

# Run specific test file
uv run pytest tests/unit/test_config_path_resolver.py

# Run tests matching pattern
uv run pytest -k "test_resolve"
uv run pytest -k "plugin"

# Show short traceback for failures
uv run pytest --tb=short

# Show full traceback
uv run pytest --tb=long

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf

# Show test durations
uv run pytest --durations=10
```

## Summary

The LazyClaude testing architecture provides:

- **Comprehensive test coverage** for services and business logic
- **Isolated testing** using pyfakefs for filesystem operations
- **Clear patterns** for fixtures, mocking, and assertions
- **Type safety** enforced through MyPy
- **Edge case coverage** for robust error handling
- **Fast, reliable tests** that can run in any order

For quick reference when writing tests, see `.claude/rules/testing.md`.
