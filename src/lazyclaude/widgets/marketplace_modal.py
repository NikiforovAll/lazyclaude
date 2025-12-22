"""Marketplace browser modal widget."""

from dataclasses import replace

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Tree

from lazyclaude.models.marketplace import Marketplace, MarketplacePlugin
from lazyclaude.services.marketplace_loader import MarketplaceLoader
from lazyclaude.widgets.filter_input import FilterInput


class MarketplaceModal(Widget):
    """Modal for browsing marketplaces and their plugins."""

    BINDINGS = [
        Binding("escape", "close_or_cancel", "Close", show=False),
        Binding("/", "search", "Search", show=False),
        Binding("i", "toggle_plugin", "Install/Toggle", show=False),
        Binding("d", "uninstall_plugin", "Uninstall", show=False),
        Binding("e", "open_plugin_folder", "Open Folder", show=False),
        Binding("u", "update_marketplace", "Update", show=False),
        Binding("p", "preview_plugin", "Preview", show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("space", "toggle_node", "Toggle", show=False),
        Binding("right", "expand_node", "Expand", show=False),
        Binding("l", "expand_node", "Expand", show=False),
        Binding("left", "collapse_node", "Collapse", show=False),
        Binding("h", "collapse_node", "Collapse", show=False),
    ]

    DEFAULT_CSS = """
    MarketplaceModal {
        display: none;
        layer: overlay;
        dock: top;
        width: 100%;
        height: 100%;
        border: double $accent;
        background: $surface;
        padding: 1 2;
    }

    MarketplaceModal.visible {
        display: block;
    }

    MarketplaceModal:focus-within {
        border: double $accent;
    }

    MarketplaceModal #marketplace-tree {
        height: 1fr;
        padding: 0 1;
        scrollbar-gutter: stable;
    }

    MarketplaceModal #marketplace-footer {
        dock: bottom;
        height: 2;
        width: 100%;
        padding: 0 1;
        border-top: solid $primary;
        text-align: center;
        background: $surface;
    }

    MarketplaceModal FilterInput {
        dock: bottom;
        height: 3;
        offset-y: -2;
        background: $surface;
        border-top: solid $primary;
    }
    """

    can_focus = True

    class PluginToggled(Message):
        """Emitted when a plugin toggle/install is requested."""

        def __init__(self, plugin: MarketplacePlugin) -> None:
            self.plugin = plugin
            super().__init__()

    class PluginUninstall(Message):
        """Emitted when a plugin uninstall is requested."""

        def __init__(self, plugin: MarketplacePlugin) -> None:
            self.plugin = plugin
            super().__init__()

    class ModalClosed(Message):
        """Emitted when modal is closed."""

        pass

    class OpenPluginFolder(Message):
        """Emitted when user requests to open plugin folder."""

        def __init__(self, plugin: MarketplacePlugin) -> None:
            self.plugin = plugin
            super().__init__()

    class MarketplaceUpdate(Message):
        """Emitted when user requests to update a marketplace."""

        def __init__(self, marketplace: Marketplace) -> None:
            self.marketplace = marketplace
            super().__init__()

    class PluginPreview(Message):
        """Emitted when user requests to preview a plugin."""

        def __init__(self, plugin: MarketplacePlugin) -> None:
            self.plugin = plugin
            super().__init__()

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._loader: MarketplaceLoader | None = None
        self._marketplaces: list[Marketplace] = []
        self._tree: Tree[MarketplacePlugin | Marketplace | None] | None = None
        self._filter_query: str = ""
        self._filter_input: FilterInput | None = None

    def compose(self) -> ComposeResult:
        tree: Tree[MarketplacePlugin | Marketplace | None] = Tree(
            "Marketplace Browser", id="marketplace-tree"
        )
        tree.show_root = False
        self._tree = tree
        yield tree
        self._filter_input = FilterInput(id="marketplace-filter")
        yield self._filter_input
        yield Static("", id="marketplace-footer")

    def on_tree_node_highlighted(
        self, event: Tree.NodeHighlighted[MarketplacePlugin | Marketplace | None]
    ) -> None:
        """Update footer when tree selection changes."""
        self._update_footer(event.node.data)

    def _update_footer(self, data: MarketplacePlugin | Marketplace | None) -> None:
        """Update footer based on selected item."""
        footer = self.query_one("#marketplace-footer", Static)

        if isinstance(data, MarketplacePlugin):
            if data.is_installed:
                action = "Enable" if not data.is_enabled else "Disable"
                footer.update(
                    f"[bold]p[/] Preview  [bold]i[/] {action}  [bold]d[/] Uninstall  "
                    "[bold]e[/] Open  [bold]/[/] Search  [bold]Esc[/] Close"
                )
            else:
                footer.update(
                    "[bold]p[/] Preview  [bold]i[/] Install  "
                    "[bold]/[/] Search  [bold]Esc[/] Close"
                )
        elif isinstance(data, Marketplace):
            footer.update(
                "[bold]Space[/] Toggle  [bold]u[/] Update  "
                "[bold]/[/] Search  [bold]Esc[/] Close"
            )
        else:
            footer.update("[bold]/[/] Search  [bold]Esc[/] Close")

    def set_loader(self, loader: MarketplaceLoader) -> None:
        """Set the marketplace loader."""
        self._loader = loader

    def show(self, preserve_state: bool = False) -> None:
        """Show the modal and load marketplace data."""
        if not preserve_state:
            self._load_data()
            self._build_tree()
        self.add_class("visible")
        if self._tree:
            self._tree.focus()

    def hide(self, preserve_state: bool = False) -> None:
        """Hide the modal."""
        self.remove_class("visible")
        if not preserve_state:
            self._filter_query = ""
            if self._filter_input:
                self._filter_input.clear()
                self._filter_input.hide()

    def _load_data(self) -> None:
        """Load marketplace data from the loader."""
        if self._loader:
            self._marketplaces = self._loader.load_marketplaces()
        else:
            self._marketplaces = []

    def _build_tree(self) -> None:
        """Build the tree widget with marketplace data."""
        if not self._tree:
            return

        self._tree.clear()

        filtered = self._get_filtered_marketplaces()

        if not filtered:
            if self._filter_query:
                self._tree.root.add_leaf("[dim italic]No matches found[/]")
            else:
                self._tree.root.add_leaf("[dim italic]No marketplaces found[/]")
            return

        for marketplace in filtered:
            mp_label = self._render_marketplace_label(marketplace)
            mp_node = self._tree.root.add(mp_label, data=marketplace)

            if marketplace.error:
                mp_node.add_leaf(f"[red]Error: {marketplace.error}[/]")
            else:
                for plugin in marketplace.plugins:
                    plugin_label = self._render_plugin_label(plugin)
                    mp_node.add_leaf(plugin_label, data=plugin)

            mp_node.expand()

    def _get_filtered_marketplaces(self) -> list[Marketplace]:
        """Get marketplaces with plugins filtered by query."""
        if not self._filter_query:
            return self._marketplaces

        query = self._filter_query.lower()
        filtered: list[Marketplace] = []

        for marketplace in self._marketplaces:
            if marketplace.error:
                if query in marketplace.entry.name.lower():
                    filtered.append(marketplace)
                continue

            matching_plugins = [
                plugin
                for plugin in marketplace.plugins
                if query in plugin.name.lower()
                or query in plugin.description.lower()
                or query in marketplace.entry.name.lower()
            ]

            if matching_plugins:
                filtered.append(replace(marketplace, plugins=matching_plugins))

        return filtered

    def _render_marketplace_label(self, marketplace: Marketplace) -> str:
        """Render a marketplace node label."""
        count = len(marketplace.plugins)
        source_type = marketplace.entry.source.source_type
        source_info = ""
        if source_type == "github" and marketplace.entry.source.repo:
            source_info = f" [dim]({marketplace.entry.source.repo})[/]"
        elif source_type == "directory":
            source_info = " [dim](local)[/]"
        return f"[bold]{marketplace.entry.name}[/] ({count} plugins){source_info}"

    def _render_plugin_label(self, plugin: MarketplacePlugin) -> str:
        """Render a plugin node label."""
        if plugin.is_installed:
            status_icon = "[green]I[/]" if plugin.is_enabled else "[yellow]D[/]"
        else:
            status_icon = "[ ]"

        desc = f" - {plugin.description}" if plugin.description else ""
        if len(desc) > 90:
            desc = desc[:87] + "..."

        return f"{status_icon} {plugin.name}{desc}"

    def action_close_or_cancel(self) -> None:
        """Close filter input or modal."""
        if self._filter_input and self._filter_input.is_visible:
            self._filter_input.action_cancel()
        else:
            self.hide()
            self.post_message(self.ModalClosed())

    def action_search(self) -> None:
        """Show the filter input."""
        if self._filter_input:
            self._filter_input.show()

    def on_filter_input_filter_changed(self, event: FilterInput.FilterChanged) -> None:
        """Handle real-time filter changes."""
        self._filter_query = event.query
        self._build_tree()

    def on_filter_input_filter_cancelled(
        self,
        event: FilterInput.FilterCancelled,  # noqa: ARG002
    ) -> None:
        """Handle filter cancellation."""
        self._filter_query = ""
        self._build_tree()
        if self._tree:
            self._tree.focus()

    def on_filter_input_filter_applied(
        self,
        event: FilterInput.FilterApplied,  # noqa: ARG002
    ) -> None:
        """Handle filter applied (Enter)."""
        if self._filter_input:
            self._filter_input.hide()
        if self._tree:
            self._tree.focus()

    def action_toggle_plugin(self) -> None:
        """Toggle or install the selected plugin."""
        if not self._tree:
            return

        node = self._tree.cursor_node
        if node is None:
            return

        data = node.data
        if isinstance(data, MarketplacePlugin):
            self.post_message(self.PluginToggled(data))

    def action_uninstall_plugin(self) -> None:
        """Uninstall the selected plugin."""
        if not self._tree:
            return

        node = self._tree.cursor_node
        if node is None:
            return

        data = node.data
        if isinstance(data, MarketplacePlugin):
            self.post_message(self.PluginUninstall(data))

    def action_open_plugin_folder(self) -> None:
        """Open the selected plugin's folder."""
        if not self._tree:
            return

        node = self._tree.cursor_node
        if node is None:
            return

        data = node.data
        if isinstance(data, MarketplacePlugin) and data.is_installed:
            self.post_message(self.OpenPluginFolder(data))

    def action_update_marketplace(self) -> None:
        """Update the selected marketplace."""
        if not self._tree:
            return

        node = self._tree.cursor_node
        if node is None:
            return

        data = node.data
        if isinstance(data, Marketplace):
            self.post_message(self.MarketplaceUpdate(data))

    def action_preview_plugin(self) -> None:
        """Preview the selected plugin's customizations."""
        if not self._tree:
            return

        node = self._tree.cursor_node
        if node is None:
            return

        data = node.data
        if isinstance(data, MarketplacePlugin):
            self.post_message(self.PluginPreview(data))

    def action_cursor_down(self) -> None:
        """Move cursor down in tree."""
        if self._tree:
            self._tree.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in tree."""
        if self._tree:
            self._tree.action_cursor_up()

    def action_toggle_node(self) -> None:
        """Toggle node expansion."""
        if self._tree:
            self._tree.action_select_cursor()

    def action_expand_node(self) -> None:
        """Expand current node."""
        if self._tree and self._tree.cursor_node:
            self._tree.cursor_node.expand()

    def action_collapse_node(self) -> None:
        """Collapse current node."""
        if self._tree and self._tree.cursor_node:
            self._tree.cursor_node.collapse()

    def refresh_tree(self) -> None:
        """Refresh the tree after changes, preserving cursor position."""
        selected_id: str | None = None
        if self._tree and self._tree.cursor_node:
            data = self._tree.cursor_node.data
            if isinstance(data, MarketplacePlugin):
                selected_id = data.full_plugin_id
            elif isinstance(data, Marketplace):
                selected_id = f"marketplace:{data.entry.name}"

        if self._loader:
            self._loader.refresh()
        self._load_data()
        self._build_tree()

        if selected_id and self._tree:
            self._tree.call_after_refresh(self._restore_cursor, selected_id)

    def _restore_cursor(self, selected_id: str) -> None:
        """Restore cursor to the node with the given ID."""
        if not self._tree:
            return

        for node in self._tree.root.children:
            data = node.data
            if isinstance(data, Marketplace):
                if selected_id == f"marketplace:{data.entry.name}":
                    self._tree.select_node(node)
                    self._update_footer(data)
                    return
                for child in node.children:
                    child_data = child.data
                    if (
                        isinstance(child_data, MarketplacePlugin)
                        and child_data.full_plugin_id == selected_id
                    ):
                        self._tree.select_node(child)
                        self._update_footer(child_data)
                        return

    @property
    def is_visible(self) -> bool:
        """Check if the modal is visible."""
        return self.has_class("visible")
