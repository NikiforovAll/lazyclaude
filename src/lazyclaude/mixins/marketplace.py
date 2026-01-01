"""Marketplace mixin for LazyClaude application."""

import os
import subprocess
from typing import TYPE_CHECKING

from textual import work

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    PluginInfo,
)
from lazyclaude.models.marketplace import MarketplacePlugin
from lazyclaude.services.opener import open_github_source, open_in_file_explorer
from lazyclaude.widgets.marketplace_confirm import MarketplaceConfirm
from lazyclaude.widgets.marketplace_modal import MarketplaceModal
from lazyclaude.widgets.marketplace_source_input import MarketplaceSourceInput

if TYPE_CHECKING:
    from lazyclaude.models.settings import AppSettings
    from lazyclaude.services.discovery import ConfigDiscoveryService
    from lazyclaude.services.marketplace_loader import MarketplaceLoader
    from lazyclaude.widgets.app_footer import AppFooter
    from lazyclaude.widgets.combined_panel import CombinedPanel
    from lazyclaude.widgets.detail_pane import MainPane
    from lazyclaude.widgets.filter_input import FilterInput
    from lazyclaude.widgets.status_panel import StatusPanel
    from lazyclaude.widgets.type_panel import TypePanel


class MarketplaceMixin:
    """Mixin providing marketplace browser functionality."""

    _marketplace_modal: MarketplaceModal | None
    _marketplace_confirm: MarketplaceConfirm | None
    _marketplace_source_input: MarketplaceSourceInput | None
    _marketplace_loader: "MarketplaceLoader | None"
    _plugin_preview_mode: bool
    _previewing_plugin: MarketplacePlugin | None
    _plugin_customizations: list[Customization]
    _search_query: str
    _discovery_service: "ConfigDiscoveryService"
    _main_pane: "MainPane | None"
    _combined_panel: "CombinedPanel | None"
    _status_panel: "StatusPanel | None"
    _filter_input: "FilterInput | None"
    _app_footer: "AppFooter | None"
    _panel_before_selector: "TypePanel | None"
    _combined_before_selector: bool
    _settings: "AppSettings"

    def action_toggle_marketplace(self) -> None:
        """Toggle the marketplace browser modal."""
        if self._marketplace_modal:
            if self._marketplace_modal.is_visible:
                self._marketplace_modal.hide()
                self._restore_focus_after_selector()  # type: ignore[attr-defined]
            else:
                self._panel_before_selector = self._get_focused_panel()  # type: ignore[attr-defined]
                self._combined_before_selector = (
                    self._combined_panel.has_focus if self._combined_panel else False
                )
                self._marketplace_modal.show(
                    auto_collapse=self._settings.marketplace_auto_collapse
                )
            self._update_footer_actions()  # type: ignore[attr-defined]

    def _enter_plugin_preview(self, plugin: MarketplacePlugin) -> None:
        """Enter plugin preview mode - show plugin's customizations in panels."""
        if not self._marketplace_loader:
            self.notify("Marketplace loader not available", severity="error")  # type: ignore[attr-defined]
            return

        plugin_dir = self._marketplace_loader.get_plugin_source_dir(plugin)
        if not plugin_dir or not plugin_dir.exists():
            self.notify("Plugin source not found", severity="warning")  # type: ignore[attr-defined]
            return

        plugin_info = PluginInfo(
            plugin_id=plugin.full_plugin_id,
            short_name=plugin.name,
            version="preview",
            install_path=plugin_dir,
            is_enabled=plugin.is_enabled,
        )
        self._plugin_customizations = self._discovery_service.discover_from_directory(
            plugin_dir, plugin_info, marketplace_plugin=plugin
        )
        self._previewing_plugin = plugin
        self._plugin_preview_mode = True

        if self._marketplace_modal:
            self._marketplace_modal.hide(preserve_state=True)

        self._update_panels()  # type: ignore[attr-defined]
        self._update_subtitle()  # type: ignore[attr-defined]
        self._update_footer_actions()  # type: ignore[attr-defined]
        self.refresh_bindings()  # type: ignore[attr-defined]
        if self._status_panel:
            if plugin.is_installed:
                resolved_version = plugin_dir.name
            else:
                resolved_version = plugin.extra_metadata.get("version", "dev")
            self._status_panel.config_path = (
                f"Preview: {plugin.name} [dim]({resolved_version})[/]"
            )
            self._status_panel.filter_level = "Plugin"

        if self._main_pane:
            readme_path = plugin_dir / "README.md"
            if readme_path.is_file():
                try:
                    readme_content = readme_path.read_text(encoding="utf-8")
                    readme_customization = Customization(
                        name="README.md",
                        type=CustomizationType.MEMORY_FILE,
                        level=ConfigLevel.PLUGIN,
                        path=readme_path,
                        description=f"Plugin documentation for {plugin.name}",
                        content=readme_content,
                        plugin_info=plugin_info,
                    )
                    self._main_pane.customization = readme_customization
                except OSError:
                    self._main_pane.customization = None
            else:
                self._main_pane.customization = None

        if self._combined_panel:
            self._combined_panel.switch_to_type(CustomizationType.MCP)

    def _exit_plugin_preview(self) -> None:
        """Exit plugin preview mode and return to marketplace."""
        self._plugin_preview_mode = False
        self._previewing_plugin = None
        self._plugin_customizations = []
        self._search_query = ""
        if self._filter_input:
            self._filter_input.clear()
        self._update_panels()  # type: ignore[attr-defined]
        self._update_subtitle()  # type: ignore[attr-defined]
        self._update_status_panel()  # type: ignore[attr-defined]
        self._update_footer_actions()  # type: ignore[attr-defined]
        self.refresh_bindings()  # type: ignore[attr-defined]

        if self._main_pane:
            self._main_pane.customization = None

        if self._marketplace_modal:
            self._marketplace_modal.show(preserve_state=True)

    def action_exit_preview(self) -> None:
        """Exit plugin preview mode (visible binding for Esc in preview)."""
        self._exit_plugin_preview()

    def on_marketplace_modal_plugin_preview(
        self, message: MarketplaceModal.PluginPreview
    ) -> None:
        """Handle plugin preview request from marketplace modal."""
        self._enter_plugin_preview(message.plugin)

    def on_marketplace_modal_plugin_toggled(
        self, message: MarketplaceModal.PluginToggled
    ) -> None:
        """Handle plugin toggle/install from marketplace modal."""
        plugin = message.plugin

        if not plugin.is_installed:
            cmd = ["claude", "plugin", "install", plugin.full_plugin_id]
            action_msg = f"Installing {plugin.name}..."
            success_msg = f"Installed {plugin.name}"
        elif plugin.is_enabled:
            cmd = ["claude", "plugin", "disable", plugin.full_plugin_id]
            action_msg = f"Disabling {plugin.name}..."
            success_msg = f"Disabled {plugin.name}"
        else:
            cmd = ["claude", "plugin", "enable", plugin.full_plugin_id]
            action_msg = f"Enabling {plugin.name}..."
            success_msg = f"Enabled {plugin.name}"

        self.notify(action_msg, severity="information", timeout=2.0)  # type: ignore[attr-defined]
        self._run_plugin_command(cmd, success_msg)

    def on_marketplace_modal_plugin_uninstall(
        self, message: MarketplaceModal.PluginUninstall
    ) -> None:
        """Handle plugin uninstall from marketplace modal."""
        plugin = message.plugin

        if not plugin.is_installed:
            self.notify("Plugin not installed", severity="warning")  # type: ignore[attr-defined]
            return

        self.notify(  # type: ignore[attr-defined]
            f"Uninstalling {plugin.name}...", severity="information", timeout=2.0
        )
        cmd = ["claude", "plugin", "uninstall", plugin.full_plugin_id]
        self._run_plugin_command(cmd, f"Uninstalled {plugin.name}")

    @work(thread=True)
    def _run_plugin_command(self, cmd: list[str], success_msg: str) -> None:
        """Run a plugin command in a background worker."""
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                shell=True,
                encoding="utf-8",
                errors="replace",
            )
            self.call_from_thread(self._on_plugin_command_success, success_msg)  # type: ignore[attr-defined]
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed: {e.stderr or e}"
            self.call_from_thread(self._on_plugin_command_error, error_msg)  # type: ignore[attr-defined]
        except FileNotFoundError:
            self.call_from_thread(self._on_plugin_command_error, "Claude CLI not found")  # type: ignore[attr-defined]

    def _on_plugin_command_success(self, success_msg: str) -> None:
        """Handle successful plugin command completion."""
        self.notify(success_msg, severity="information")  # type: ignore[attr-defined]
        if self._marketplace_modal:
            self._marketplace_modal.refresh_tree()
        self.action_refresh()  # type: ignore[attr-defined]

    def _on_plugin_command_error(self, error_msg: str) -> None:
        """Handle plugin command error."""
        self.notify(error_msg, severity="error")  # type: ignore[attr-defined]
        if self._marketplace_modal:
            self._marketplace_modal.refresh_tree()

    def on_marketplace_modal_open_plugin_folder(
        self, message: MarketplaceModal.OpenPluginFolder
    ) -> None:
        """Handle opening plugin folder from marketplace modal."""
        plugin = message.plugin

        if not plugin.install_path or not plugin.install_path.exists():
            self.notify("Plugin folder not found", severity="warning")  # type: ignore[attr-defined]
            return

        editor = os.environ.get("EDITOR", "vi")
        subprocess.Popen([editor, str(plugin.install_path)], shell=True)

    def on_marketplace_modal_open_plugin_source(
        self, message: MarketplaceModal.OpenPluginSource
    ) -> None:
        """Handle opening plugin source location from marketplace modal."""
        plugin = message.plugin
        marketplace = message.marketplace
        source_type = marketplace.entry.source.source_type

        if source_type == "directory":
            if plugin.is_installed and plugin.install_path:
                path = plugin.install_path
            else:
                path = (marketplace.entry.install_location / plugin.source).resolve()

            success, error = open_in_file_explorer(path)
            if not success:
                self.notify(error or "Failed to open", severity="warning")  # type: ignore[attr-defined]
        elif source_type == "github":
            repo = marketplace.entry.source.repo
            if repo:
                open_github_source(repo, plugin.source)
            else:
                self.notify("GitHub repository not configured", severity="warning")  # type: ignore[attr-defined]
        else:
            self.notify(f"Unknown source type: {source_type}", severity="warning")  # type: ignore[attr-defined]

    def on_marketplace_modal_open_marketplace_source(
        self, message: MarketplaceModal.OpenMarketplaceSource
    ) -> None:
        """Handle opening marketplace source location."""
        marketplace = message.marketplace
        source_type = marketplace.entry.source.source_type

        if source_type == "directory":
            success, error = open_in_file_explorer(marketplace.entry.install_location)
            if not success:
                self.notify(error or "Failed to open", severity="warning")  # type: ignore[attr-defined]
        elif source_type == "github":
            repo = marketplace.entry.source.repo
            if repo:
                open_github_source(repo)
            else:
                self.notify("GitHub repository not configured", severity="warning")  # type: ignore[attr-defined]
        else:
            self.notify(f"Unknown source type: {source_type}", severity="warning")  # type: ignore[attr-defined]

    def on_marketplace_modal_marketplace_update(
        self, message: MarketplaceModal.MarketplaceUpdate
    ) -> None:
        """Handle marketplace update request."""
        marketplace = message.marketplace
        self.notify(f"Updating {marketplace.entry.name}...", severity="information")  # type: ignore[attr-defined]
        cmd = ["claude", "plugin", "marketplace", "update", marketplace.entry.name]
        self._run_plugin_command(cmd, f"Updated {marketplace.entry.name}")

    def on_marketplace_modal_plugin_update(
        self, message: MarketplaceModal.PluginUpdate
    ) -> None:
        """Handle plugin update request."""
        plugin = message.plugin
        self.notify(f"Updating {plugin.name}...", severity="information")  # type: ignore[attr-defined]
        cmd = ["claude", "plugin", "update", plugin.full_plugin_id]
        self._run_plugin_command(cmd, f"Updated {plugin.name}")

    def on_marketplace_modal_modal_closed(
        self,
        message: MarketplaceModal.ModalClosed,  # noqa: ARG002
    ) -> None:
        """Handle marketplace modal close."""
        self._restore_focus_after_selector()  # type: ignore[attr-defined]
        self._update_footer_actions()  # type: ignore[attr-defined]

    def on_marketplace_modal_marketplace_remove(
        self, message: MarketplaceModal.MarketplaceRemove
    ) -> None:
        """Handle marketplace remove request - show confirmation."""
        if self._marketplace_confirm:
            self._marketplace_confirm.show(message.marketplace)

    def on_marketplace_modal_marketplace_add_request(
        self,
        message: MarketplaceModal.MarketplaceAddRequest,  # noqa: ARG002
    ) -> None:
        """Handle request to add marketplace - show source input."""
        if self._marketplace_source_input:
            self._marketplace_source_input.show()

    def on_marketplace_confirm_remove_confirmed(
        self, message: MarketplaceConfirm.RemoveConfirmed
    ) -> None:
        """Handle confirmed marketplace removal."""
        marketplace = message.marketplace
        self.notify(f"Removing {marketplace.entry.name}...", severity="information")  # type: ignore[attr-defined]
        cmd = ["claude", "plugin", "marketplace", "remove", marketplace.entry.name]
        self._run_plugin_command(cmd, f"Removed {marketplace.entry.name}")
        if self._marketplace_modal:
            self._marketplace_modal.call_after_refresh(  # type: ignore[attr-defined]
                self._marketplace_modal.focus_tree
            )

    def on_marketplace_confirm_remove_cancelled(
        self,
        message: MarketplaceConfirm.RemoveCancelled,  # noqa: ARG002
    ) -> None:
        """Handle marketplace removal cancellation."""
        if self._marketplace_modal:
            self._marketplace_modal.call_after_refresh(  # type: ignore[attr-defined]
                self._marketplace_modal.focus_tree
            )

    def on_marketplace_source_input_source_submitted(
        self, message: MarketplaceSourceInput.SourceSubmitted
    ) -> None:
        """Handle marketplace source submission."""
        source = message.source
        self.notify(f"Adding marketplace from {source}...", severity="information")  # type: ignore[attr-defined]
        cmd = ["claude", "plugin", "marketplace", "add", source]
        self._run_plugin_command(cmd, "Added marketplace")
        if self._marketplace_modal:
            self._marketplace_modal.focus_tree()

    def on_marketplace_source_input_source_cancelled(
        self,
        message: MarketplaceSourceInput.SourceCancelled,  # noqa: ARG002
    ) -> None:
        """Handle marketplace source input cancellation."""
        if self._marketplace_modal:
            self._marketplace_modal.focus_tree()
