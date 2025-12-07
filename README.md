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

## Keybindings

`j/k` navigate | `Enter` drill down | `Esc` back | `/` search | `?` help | `q` quit

## License

MIT
