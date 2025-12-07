# Contributing to LazyClaude

## Development Setup

```bash
# Clone and install
git clone https://github.com/NikiforovAll/lazyclaude.git
cd lazyclaude
uv sync

# Install git hooks
uv run pre-commit install
```

## Code Quality

Pre-commit hooks run automatically on commit. To run manually:

```bash
uv run pre-commit run --all-files
```

Individual checks:

```bash
uv run ruff check src tests      # Lint
uv run ruff format src tests     # Format
uv run mypy src                  # Type check
uv run pytest                    # Test
```

## Commit Messages

Use conventional commits with emojis:

| Type | Emoji | Description |
|------|-------|-------------|
| feat | ✨ | New feature |
| fix | 🐛 | Bug fix |
| docs | 📝 | Documentation |
| refactor | ♻️ | Code restructuring |
| style | 🎨 | Formatting |
| test | ✅ | Tests |
| chore | 🧑‍💻 | Tooling, maintenance |

Example: `✨ feat(discovery): add hooks panel`