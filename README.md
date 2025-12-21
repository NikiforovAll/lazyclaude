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

## Quick Tour

### First Launch
Launch LazyClaude to explore all your Claude Code customizations in one place. Navigate with `j`/`k`, switch panels with `1-6`, and toggle views with `[`/`]`.

![First Launch](docs/assets/first-launch.gif)

### Filter by Level
Press `a`/`u`/`p`/`P` to filter customizations by configuration level (All/User/Project/Plugin).

![Filter Workflow](docs/assets/demo-filter-workflow.gif)

### Browse Marketplace
Press `M` to open the marketplace browser. Install plugins with `i`, preview content with `p`, and manage installations.

![Marketplace Install](docs/assets/demo-marketplace-install.gif)

### Preview Before Installing
Press `p` in the marketplace to preview plugin content before installation. Explore what the plugin provides without committing.

![Preview Plugin](docs/assets/demo-preview-plugin.gif)

📖 **[Full User Guide](docs/user-guide.md)** for detailed workflows and keyboard shortcuts.


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
