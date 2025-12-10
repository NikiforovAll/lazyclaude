---
paths: tests/**/*.py
---

# Testing Rules for LazyClaude

These rules apply when working with test files in the `tests/` directory. For detailed patterns and examples, see `docs/testing-guide.md`.

## Naming Conventions

- Test files: MUST use `test_` prefix (e.g., `test_config_path_resolver.py`)
- Test classes: MUST use `Test` prefix (e.g., `TestConfigPathResolver`)
- Test methods: MUST use pattern `test_<scenario>_<expected_outcome>` (e.g., `test_non_plugin_level_returns_path_as_is`)
- Test methods: SHOULD be descriptive and explain what is being tested

## File Organization

- Unit tests: Place in `tests/unit/` directory
- Integration tests: Place in `tests/integration/` directory
- Test fixtures (data): Place in `tests/integration/fixtures/` directory
- Shared fixtures (code): Define in `tests/conftest.py`

## Required Patterns

### Type Hints
- MUST include type hints on all test functions
- Test functions: Use `-> None` return type
- Fixtures: Use appropriate return type (`-> Path`, `-> Generator[Path, None, None]`, etc.)
- MyPy enforces `disallow_untyped_defs = true`

### Docstrings
- MUST include docstrings for test classes describing what is being tested
- MUST include docstrings for test methods describing the test scenario
- Format: Brief one-line description ending with period

### Class-Based Organization
- Group related tests into classes with `Test` prefix
- One class per behavior or functionality being tested
- Classes SHOULD have descriptive names indicating what they test

## Fixture Usage

- MUST use fixtures from `conftest.py` for shared test setup
- Function-scoped fixtures by default for test isolation
- Use composition pattern: fixtures can depend on other fixtures
- Common fixtures:
  - `fs` (FakeFilesystem) - pyfakefs filesystem
  - `fake_home` (Path) - Fake home directory at `/fake/home`
  - `fake_project_root` (Path) - Fake project root at `/fake/project`
  - `user_config_path` (Path) - User config with test fixtures
  - `project_config_path` (Path) - Project config with test fixtures

## Filesystem Testing

- MUST use pyfakefs for all filesystem operations
- DO NOT use real filesystem paths in tests
- Use `fs.create_dir()` to create directories
- Use `fs.create_file()` to create files
- Use `fs.add_real_file()` to add fixture files from `tests/integration/fixtures/`
- Use `fs.add_real_directory()` to add fixture directories
- Conventions:
  - Fake home: `Path("/fake/home")`
  - Fake project root: `Path("/fake/project")`

## Async Testing

- Use `@pytest.mark.asyncio` decorator for async test methods
- pytest.ini configured with `asyncio_mode = "auto"`
- For message capture in async tests: Replace async methods with synchronous mocks
- Example: `widget.post_message = capture_message  # type: ignore`

## Mocking

- Use `unittest.mock.Mock` for service dependencies
- Prefer minimal mocking - use real implementations with fake filesystem when possible
- For widget testing: Mock methods like `post_message`, `focus`, `hide`
- For service testing: Mock external dependencies only
- Use `assert_called()`, `assert_not_called()`, `assert_called_with()` for verification

## Test Structure

Typical test method structure:
1. **Arrange**: Set up test data and dependencies
2. **Act**: Execute the operation being tested
3. **Assert**: Verify the outcome

Example:
```python
def test_copies_file_successfully(self, fs, fake_home: Path) -> None:
    """Copying a file to user level creates the file."""
    # Arrange
    fs.create_dir(fake_home / ".claude")
    source_file = Path("/source/test.md")
    fs.create_file(source_file, contents="Test content")

    # Act
    result = writer.copy_file(source_file, fake_home / ".claude")

    # Assert
    assert result is True
    assert (fake_home / ".claude" / "test.md").exists()
```

## Commands Reference

```bash
uv run pytest                          # Run all tests
uv run pytest tests/unit/              # Run unit tests only
uv run pytest tests/integration/       # Run integration tests only
uv run pytest tests/unit/test_X.py     # Run specific test file
uv run pytest -k "test_name"           # Run tests matching pattern
uv run pytest -v                       # Verbose output
uv run pytest --tb=short               # Short traceback format
```

## See Also

- `docs/testing-guide.md` - Comprehensive guide with examples
- `docs/constitution.md` - Project principles and constraints
- `tests/conftest.py` - Shared fixture definitions
- `pyproject.toml` - pytest configuration
