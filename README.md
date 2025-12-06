# LazyClaude

A lazygit-style TUI for visualizing Claude Code customizations.

## Features

- View all Claude Code customizations (Slash Commands, Subagents, Skills, Memory Files, MCPs)
- Navigate with keyboard-first vim-like keybindings
- Filter by configuration level (User, Project, Project-Local)
- Search across all customization types
- Drill down into customization details

## Installation

```bash
# Using uvx (recommended)
uvx lazyclaude

# Or install with uv
uv tool install lazyclaude
```

## Development

```bash
# Clone the repository
git clone https://github.com/nikiforovall/lazyclaude.git
cd lazyclaude

# Install dependencies
uv sync

# Run the application
uv run lazyclaude

# Run tests
uv run pytest

# Lint and format
uv run ruff check src tests
uv run ruff format src tests
```

## Keybindings

| Key | Action |
|-----|--------|
| `j`/`k` | Navigate up/down |
| `Enter` | Drill down into details |
| `Esc` | Go back |
| `Tab` | Switch panels |
| `1`/`2`/`3` | Filter by level (All/User/Project) |
| `/` | Search |
| `R` | Refresh |
| `?` | Help |
| `q` | Quit |

## License

MIT
