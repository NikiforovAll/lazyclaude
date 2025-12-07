<p align="center">
  <img src="assets/logo.png" alt="LazyClaude" width="150">
</p>

# LazyClaude

A lazygit-style TUI for visualizing Claude Code customizations.

![Demo](assets/demo.png)

## Install

```bash
uvx lazyclaude
```

## Key Features

### Unified View

All six customization types displayed in organized panels. Select any item to see its full content with syntax highlighting in the detail pane.

### Configuration Level Awareness

Claude Code resolves customizations from multiple levels:

| Level | Location | Description |
|-------|----------|-------------|
| User | `~/.claude/` | Global configuration |
| Project | `./.claude/` | Project-specific overrides |
| Plugin | `~/.claude/plugins/` | Third-party extensions |

LazyClaude shows each item's origin, helping you understand override behavior and avoid conflicts.

### Quick Filtering

Press a single key to filter by configuration level:

- `a` — Show all levels
- `u` — User-level only
- `p` — Project-level only
- `P` — Plugin-level only

Press `/` to search by name or plugin prefix.

### Vim-Style Navigation

| Key | Action |
|-----|--------|
| `j` / `k` | Navigate up/down |
| `g` / `G` | Jump to top/bottom |
| `1`-`6` | Jump to specific panel |
| `Tab` | Switch between panels |
| `Enter` | View item details |
| `Esc` | Go back |
| `e` | Open in $EDITOR |
| `R` | Refresh from disk |
| `?` | Show help |
| `q` | Quit |


`j/k` navigate | `Enter` drill down | `Esc` back | `/` search | `?` help | `q` quit


![Demo](assets/demo.gif)



## Development

```bash
uv sync              # Install dependencies
uv run lazyclaude    # Run app
```

Publish:

```bash
export UV_PUBLISH_TOKEN=<your_token>
uv build
uv publish
```

See: <https://docs.astral.sh/uv/guides/package/>

## License

MIT
