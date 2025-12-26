"""Customization actions mixin for LazyClaude application."""

from typing import TYPE_CHECKING

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.writer import CustomizationWriter
from lazyclaude.widgets.delete_confirm import DeleteConfirm
from lazyclaude.widgets.level_selector import LevelSelector
from lazyclaude.widgets.plugin_confirm import PluginConfirm

if TYPE_CHECKING:
    from lazyclaude.services.discovery import ConfigDiscoveryService
    from lazyclaude.widgets.combined_panel import CombinedPanel
    from lazyclaude.widgets.detail_pane import MainPane
    from lazyclaude.widgets.type_panel import TypePanel


class CustomizationActionsMixin:
    """Mixin providing copy/move/delete operations for customizations."""

    _COPYABLE_TYPES: tuple[CustomizationType, ...]
    _PROJECT_LOCAL_TYPES: tuple[CustomizationType, ...]
    _main_pane: "MainPane | None"
    _level_selector: LevelSelector | None
    _plugin_confirm: PluginConfirm | None
    _delete_confirm: DeleteConfirm | None
    _pending_customization: Customization | None
    _panel_before_selector: "TypePanel | None"
    _combined_before_selector: bool
    _combined_panel: "CombinedPanel | None"
    _discovery_service: "ConfigDiscoveryService"

    def action_copy_customization(self) -> None:
        """Copy selected customization to another level."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if customization.type not in self._COPYABLE_TYPES:
            self._show_status_error(  # type: ignore[attr-defined]
                f"Cannot copy {customization.type_label} customizations"
            )
            return

        available = self._get_available_target_levels(customization)
        if not available:
            self._show_status_error("No available target levels")  # type: ignore[attr-defined]
            return

        self._pending_customization = customization
        self._panel_before_selector = self._get_focused_panel()  # type: ignore[attr-defined]
        self._combined_before_selector = (
            self._combined_panel.has_focus if self._combined_panel else False
        )
        if self._level_selector:
            self._level_selector.show(available, "copy")

    def action_move_customization(self) -> None:
        """Move selected customization to another level."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if customization.type not in self._COPYABLE_TYPES:
            self._show_status_error(  # type: ignore[attr-defined]
                f"Cannot move {customization.type_label} customizations"
            )
            return

        if customization.level == ConfigLevel.PLUGIN:
            self._show_status_error("Cannot move from plugin-level customizations")  # type: ignore[attr-defined]
            return

        available = self._get_available_target_levels(customization)
        if not available:
            self._show_status_error("No available target levels")  # type: ignore[attr-defined]
            return

        self._pending_customization = customization
        self._panel_before_selector = self._get_focused_panel()  # type: ignore[attr-defined]
        self._combined_before_selector = (
            self._combined_panel.has_focus if self._combined_panel else False
        )
        if self._level_selector:
            self._level_selector.show(available, "move")

    def action_delete_customization(self) -> None:
        """Delete selected customization."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if customization.type not in self._COPYABLE_TYPES:
            self._show_status_error(  # type: ignore[attr-defined]
                f"Cannot delete {customization.type_label} customizations"
            )
            return

        if customization.level == ConfigLevel.PLUGIN:
            self._show_status_error("Cannot delete plugin-level customizations")  # type: ignore[attr-defined]
            return

        self._panel_before_selector = self._get_focused_panel()  # type: ignore[attr-defined]
        self._combined_before_selector = (
            self._combined_panel.has_focus if self._combined_panel else False
        )
        if self._delete_confirm:
            self._delete_confirm.show(customization)

    def action_toggle_plugin_enabled(self) -> None:
        """Toggle enabled state for selected plugin customization."""
        if not self._main_pane or not self._main_pane.customization:
            return

        customization = self._main_pane.customization

        if not customization.plugin_info:
            self._show_status_error("Not a plugin customization")  # type: ignore[attr-defined]
            return

        self._panel_before_selector = self._get_focused_panel()  # type: ignore[attr-defined]
        self._combined_before_selector = (
            self._combined_panel.has_focus if self._combined_panel else False
        )
        if self._plugin_confirm:
            self._plugin_confirm.show(
                plugin_info=customization.plugin_info,
                customizations=self._customizations,  # type: ignore[attr-defined]
            )

    def _get_available_target_levels(
        self, customization: Customization
    ) -> list[ConfigLevel]:
        """Get available target levels for copy/move based on customization type."""
        if customization.type in self._PROJECT_LOCAL_TYPES:
            all_levels = [
                ConfigLevel.USER,
                ConfigLevel.PROJECT,
                ConfigLevel.PROJECT_LOCAL,
            ]
        else:
            all_levels = [ConfigLevel.USER, ConfigLevel.PROJECT]
        return [level for level in all_levels if level != customization.level]

    def _delete_customization(
        self, customization: Customization, writer: CustomizationWriter
    ) -> tuple[bool, str]:
        """Delete customization using type-specific method."""
        if customization.type == CustomizationType.MCP:
            return writer.delete_mcp_customization(
                customization, self._discovery_service.project_config_path
            )
        elif customization.type == CustomizationType.HOOK:
            return writer.delete_hook_customization(customization)
        else:
            return writer.delete_customization(customization)

    def _handle_copy_or_move(
        self, customization: Customization, target_level: ConfigLevel, operation: str
    ) -> None:
        """Handle copy or move operation."""
        if operation == "move" and customization.level == ConfigLevel.PLUGIN:
            self._show_status_error("Cannot move from plugin (read-only source)")  # type: ignore[attr-defined]
            return

        writer = CustomizationWriter()

        if customization.type == CustomizationType.MCP:
            success, msg = writer.write_mcp_customization(
                customization,
                target_level,
                self._discovery_service.project_config_path,
            )
        elif customization.type == CustomizationType.HOOK:
            success, msg = writer.write_hook_customization(
                customization,
                target_level,
                self._discovery_service.user_config_path,
                self._discovery_service.project_config_path,
            )
        else:
            success, msg = writer.write_customization(
                customization,
                target_level,
                self._discovery_service.user_config_path,
                self._discovery_service.project_config_path,
            )

        if not success:
            self._show_status_error(msg)  # type: ignore[attr-defined]
            return

        if operation == "move":
            delete_success, delete_msg = self._delete_customization(
                customization, writer
            )
            if not delete_success:
                self._show_status_error(  # type: ignore[attr-defined]
                    f"Copied but failed to delete source: {delete_msg}"
                )
                return
            msg = f"Moved '{customization.name}' to {target_level.label} level"

        self._show_status_success(msg)  # type: ignore[attr-defined]
        self.action_refresh()  # type: ignore[attr-defined]

    def on_level_selector_level_selected(
        self, message: LevelSelector.LevelSelected
    ) -> None:
        """Handle level selection from the level selector bar."""
        if self._pending_customization:
            self._handle_copy_or_move(
                self._pending_customization, message.level, message.operation
            )
            self._pending_customization = None
        self._restore_focus_after_selector()  # type: ignore[attr-defined]

    def on_level_selector_selection_cancelled(
        self,
        message: LevelSelector.SelectionCancelled,  # noqa: ARG002
    ) -> None:
        """Handle level selector cancellation."""
        self._pending_customization = None
        self._restore_focus_after_selector()  # type: ignore[attr-defined]

    def on_plugin_confirm_plugin_confirmed(
        self, message: PluginConfirm.PluginConfirmed
    ) -> None:
        """Handle plugin toggle confirmation."""
        writer = CustomizationWriter()
        success, msg = writer.toggle_plugin_enabled(
            message.plugin_info,
            self._discovery_service.user_config_path,
            self._discovery_service.project_config_path,
        )

        if success:
            self.notify(msg, severity="information")  # type: ignore[attr-defined]
            self.action_refresh()  # type: ignore[attr-defined]
            self._restore_focus_after_selector()  # type: ignore[attr-defined]
        else:
            self.notify(msg, severity="error")  # type: ignore[attr-defined]
            self._restore_focus_after_selector()  # type: ignore[attr-defined]

    def on_plugin_confirm_confirmation_cancelled(
        self,
        message: PluginConfirm.ConfirmationCancelled,  # noqa: ARG002
    ) -> None:
        """Handle plugin confirmation cancellation."""
        self._restore_focus_after_selector()  # type: ignore[attr-defined]

    def on_delete_confirm_delete_confirmed(
        self, message: DeleteConfirm.DeleteConfirmed
    ) -> None:
        """Handle delete confirmation."""
        customization = message.customization
        writer = CustomizationWriter()
        success, msg = self._delete_customization(customization, writer)

        if success:
            self.notify(msg, severity="information")  # type: ignore[attr-defined]
            self.action_refresh()  # type: ignore[attr-defined]
        else:
            self.notify(msg, severity="error")  # type: ignore[attr-defined]
        self._restore_focus_after_selector()  # type: ignore[attr-defined]

    def on_delete_confirm_delete_cancelled(
        self,
        message: DeleteConfirm.DeleteCancelled,  # noqa: ARG002
    ) -> None:
        """Handle delete cancellation."""
        self._restore_focus_after_selector()  # type: ignore[attr-defined]
