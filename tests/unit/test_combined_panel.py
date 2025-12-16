"""Tests for CombinedPanel widget."""

import pytest

from lazyclaude.models.customization import CustomizationType
from lazyclaude.widgets.combined_panel import CombinedPanel


class TestCombinedPanel:
    """Tests for CombinedPanel widget initialization and state."""

    def test_initial_active_type_is_memory_file(self) -> None:
        """Initial active type should be MEMORY_FILE."""
        panel = CombinedPanel()
        assert panel.active_type == CustomizationType.MEMORY_FILE

    def test_combined_types_contains_three_types(self) -> None:
        """COMBINED_TYPES should contain exactly 3 types."""
        assert len(CombinedPanel.COMBINED_TYPES) == 3
        assert CustomizationType.MEMORY_FILE in CombinedPanel.COMBINED_TYPES
        assert CustomizationType.MCP in CombinedPanel.COMBINED_TYPES
        assert CustomizationType.HOOK in CombinedPanel.COMBINED_TYPES

    def test_type_labels_defined_for_all_combined_types(self) -> None:
        """TYPE_LABELS should have labels for all combined types."""
        for ctype in CombinedPanel.COMBINED_TYPES:
            assert ctype in CombinedPanel.TYPE_LABELS
            num, label = CombinedPanel.TYPE_LABELS[ctype]
            assert isinstance(num, str)
            assert isinstance(label, str)

    def test_initial_selected_index_is_zero(self) -> None:
        """Initial selected index should be 0."""
        panel = CombinedPanel()
        assert panel.selected_index == 0

    def test_initial_is_active_is_false(self) -> None:
        """Initial is_active should be False."""
        panel = CombinedPanel()
        assert panel.is_active is False

    def test_can_focus_is_true(self) -> None:
        """Panel should be focusable."""
        panel = CombinedPanel()
        assert panel.can_focus is True

    def test_selected_indices_initialized_for_all_types(self) -> None:
        """Per-type selection indices should be initialized."""
        panel = CombinedPanel()
        for ctype in CombinedPanel.COMBINED_TYPES:
            assert ctype in panel._selected_indices
            assert panel._selected_indices[ctype] == 0


class TestCombinedPanelTabSwitching:
    """Tests for tab switching behavior."""

    def test_next_tab_cycles_forward(self) -> None:
        """action_next_tab should cycle to next type."""
        panel = CombinedPanel()
        panel.active_type = CustomizationType.MEMORY_FILE
        panel.action_next_tab()
        assert panel.active_type == CustomizationType.MCP

    def test_next_tab_cycles_to_hook(self) -> None:
        """action_next_tab should cycle from MCP to HOOK."""
        panel = CombinedPanel()
        panel.active_type = CustomizationType.MCP
        panel.action_next_tab()
        assert panel.active_type == CustomizationType.HOOK

    def test_next_tab_wraps_around(self) -> None:
        """action_next_tab should wrap from HOOK to MEMORY_FILE."""
        panel = CombinedPanel()
        panel.active_type = CustomizationType.HOOK
        panel.action_next_tab()
        assert panel.active_type == CustomizationType.MEMORY_FILE

    def test_prev_tab_cycles_backward(self) -> None:
        """action_prev_tab should cycle to previous type."""
        panel = CombinedPanel()
        panel.active_type = CustomizationType.MCP
        panel.action_prev_tab()
        assert panel.active_type == CustomizationType.MEMORY_FILE

    def test_prev_tab_cycles_to_mcp(self) -> None:
        """action_prev_tab should cycle from HOOK to MCP."""
        panel = CombinedPanel()
        panel.active_type = CustomizationType.HOOK
        panel.action_prev_tab()
        assert panel.active_type == CustomizationType.MCP

    def test_prev_tab_wraps_around(self) -> None:
        """action_prev_tab should wrap from MEMORY_FILE to HOOK."""
        panel = CombinedPanel()
        panel.active_type = CustomizationType.MEMORY_FILE
        panel.action_prev_tab()
        assert panel.active_type == CustomizationType.HOOK

    def test_tab_switching_clamps_restored_index_to_valid_range(self) -> None:
        """Restored index should be clamped if items were removed."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()

        memory_files = [
            Customization(
                name=f"memory{i}",
                type=CustomizationType.MEMORY_FILE,
                path=f"/test/memory{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(10)
        ]
        mcps = [
            Customization(
                name=f"mcp{i}",
                type=CustomizationType.MCP,
                path=f"/test/mcp{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(3)
        ]
        panel.customizations = memory_files + mcps

        panel.active_type = CustomizationType.MEMORY_FILE
        panel.selected_index = 8

        panel.switch_to_type(CustomizationType.MCP)

        fewer_memory_files = [
            Customization(
                name=f"memory{i}",
                type=CustomizationType.MEMORY_FILE,
                path=f"/test/memory{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(3)
        ]
        panel.customizations = fewer_memory_files + mcps

        panel.switch_to_type(CustomizationType.MEMORY_FILE)

        assert panel.selected_index == 2

    def test_tab_switching_handles_empty_type_after_items_removed(self) -> None:
        """Switching to type with no items should set index to 0."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()

        memory_files = [
            Customization(
                name=f"memory{i}",
                type=CustomizationType.MEMORY_FILE,
                path=f"/test/memory{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(5)
        ]
        mcps = [
            Customization(
                name=f"mcp{i}",
                type=CustomizationType.MCP,
                path=f"/test/mcp{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(3)
        ]
        panel.customizations = memory_files + mcps

        panel.active_type = CustomizationType.MEMORY_FILE
        panel.selected_index = 3

        panel.switch_to_type(CustomizationType.MCP)

        panel.customizations = mcps

        panel.switch_to_type(CustomizationType.MEMORY_FILE)

        assert panel.selected_index == 0

    def test_tab_switching_preserves_per_type_selection_indices(self) -> None:
        """Selection indices should be preserved when switching between tabs."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()

        memory_files = [
            Customization(
                name=f"memory{i}",
                type=CustomizationType.MEMORY_FILE,
                path=f"/test/memory{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(5)
        ]
        mcps = [
            Customization(
                name=f"mcp{i}",
                type=CustomizationType.MCP,
                path=f"/test/mcp{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(4)
        ]
        hooks = [
            Customization(
                name=f"hook{i}",
                type=CustomizationType.HOOK,
                path=f"/test/hook{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(3)
        ]
        panel.customizations = memory_files + mcps + hooks

        panel.active_type = CustomizationType.MEMORY_FILE
        panel.selected_index = 2

        panel.switch_to_type(CustomizationType.MCP)
        panel.selected_index = 3

        panel.switch_to_type(CustomizationType.HOOK)
        panel.selected_index = 1

        panel.switch_to_type(CustomizationType.MEMORY_FILE)
        assert panel.selected_index == 2

        panel.switch_to_type(CustomizationType.MCP)
        assert panel.selected_index == 3

        panel.switch_to_type(CustomizationType.HOOK)
        assert panel.selected_index == 1

        panel.action_next_tab()
        assert panel.active_type == CustomizationType.MEMORY_FILE
        assert panel.selected_index == 2

        panel.action_prev_tab()
        assert panel.active_type == CustomizationType.HOOK
        assert panel.selected_index == 1

    def test_switch_to_type_changes_active_type(self) -> None:
        """switch_to_type should change the active type."""
        panel = CombinedPanel()
        panel.switch_to_type(CustomizationType.HOOK)
        assert panel.active_type == CustomizationType.HOOK

    def test_switch_to_type_ignores_invalid_type(self) -> None:
        """switch_to_type should ignore types not in COMBINED_TYPES."""
        panel = CombinedPanel()
        panel.switch_to_type(CustomizationType.SLASH_COMMAND)
        assert panel.active_type == CustomizationType.MEMORY_FILE


class TestCombinedPanelMessages:
    """Tests for CombinedPanel message emission."""

    @pytest.mark.asyncio
    async def test_drill_down_posts_message(self) -> None:
        """action_select should post DrillDown when customization selected."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()
        customization = Customization(
            name="test",
            type=CustomizationType.MEMORY_FILE,
            path="/test/path",
            level=ConfigLevel.USER,
            content="test content",
        )
        panel.customizations = [customization]
        panel.selected_index = 0

        messages: list[CombinedPanel.DrillDown] = []
        panel.post_message = lambda msg: messages.append(msg)  # type: ignore

        panel.action_select()

        assert len(messages) == 1
        assert isinstance(messages[0], CombinedPanel.DrillDown)
        assert messages[0].customization == customization

    @pytest.mark.asyncio
    async def test_drill_down_does_nothing_when_no_selection(self) -> None:
        """action_select should do nothing when no customization selected."""
        panel = CombinedPanel()
        panel.customizations = []

        messages: list[CombinedPanel.DrillDown] = []
        panel.post_message = lambda msg: messages.append(msg)  # type: ignore

        panel.action_select()

        assert len(messages) == 0


class TestCombinedPanelBindings:
    """Tests for CombinedPanel key bindings."""

    def test_has_bracket_bindings(self) -> None:
        """Should have [ and ] bindings for tab switching."""
        bindings = {b.key for b in CombinedPanel.BINDINGS}
        assert "[" in bindings
        assert "]" in bindings

    def test_has_navigation_bindings(self) -> None:
        """Should have j/k navigation bindings."""
        bindings = {b.key for b in CombinedPanel.BINDINGS}
        assert "j" in bindings
        assert "k" in bindings

    def test_has_arrow_navigation_bindings(self) -> None:
        """Should have up/down arrow bindings."""
        bindings = {b.key for b in CombinedPanel.BINDINGS}
        assert "up" in bindings
        assert "down" in bindings

    def test_has_enter_binding(self) -> None:
        """Should have enter binding for drill down."""
        bindings = {b.key for b in CombinedPanel.BINDINGS}
        assert "enter" in bindings

    def test_has_escape_binding(self) -> None:
        """Should have escape binding for back."""
        bindings = {b.key for b in CombinedPanel.BINDINGS}
        assert "escape" in bindings

    def test_has_top_bottom_bindings(self) -> None:
        """Should have g/G bindings for top/bottom."""
        bindings = {b.key for b in CombinedPanel.BINDINGS}
        assert "g" in bindings
        assert "G" in bindings


class TestCombinedPanelCursorNavigation:
    """Tests for cursor navigation within panel."""

    def test_cursor_down_increments_index(self) -> None:
        """action_cursor_down should increment selected_index."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()
        panel.customizations = [
            Customization(
                name=f"test{i}",
                type=CustomizationType.MEMORY_FILE,
                path=f"/test/path{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(3)
        ]
        panel.selected_index = 0

        panel.action_cursor_down()

        assert panel.selected_index == 1

    def test_cursor_down_stops_at_end(self) -> None:
        """action_cursor_down should not go past last item."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()
        panel.customizations = [
            Customization(
                name="test",
                type=CustomizationType.MEMORY_FILE,
                path="/test/path",
                level=ConfigLevel.USER,
                content="test",
            )
        ]
        panel.selected_index = 0

        panel.action_cursor_down()

        assert panel.selected_index == 0

    def test_cursor_up_decrements_index(self) -> None:
        """action_cursor_up should decrement selected_index."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()
        panel.customizations = [
            Customization(
                name=f"test{i}",
                type=CustomizationType.MEMORY_FILE,
                path=f"/test/path{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(3)
        ]
        panel.selected_index = 2

        panel.action_cursor_up()

        assert panel.selected_index == 1

    def test_cursor_up_stops_at_top(self) -> None:
        """action_cursor_up should not go below 0."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()
        panel.customizations = [
            Customization(
                name="test",
                type=CustomizationType.MEMORY_FILE,
                path="/test/path",
                level=ConfigLevel.USER,
                content="test",
            )
        ]
        panel.selected_index = 0

        panel.action_cursor_up()

        assert panel.selected_index == 0

    def test_cursor_top_goes_to_first_item(self) -> None:
        """action_cursor_top should set selected_index to 0."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()
        panel.customizations = [
            Customization(
                name=f"test{i}",
                type=CustomizationType.MEMORY_FILE,
                path=f"/test/path{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(3)
        ]
        panel.selected_index = 2

        panel.action_cursor_top()

        assert panel.selected_index == 0

    def test_cursor_bottom_goes_to_last_item(self) -> None:
        """action_cursor_bottom should set selected_index to last."""
        from lazyclaude.models.customization import ConfigLevel, Customization

        panel = CombinedPanel()
        panel.customizations = [
            Customization(
                name=f"test{i}",
                type=CustomizationType.MEMORY_FILE,
                path=f"/test/path{i}",
                level=ConfigLevel.USER,
                content="test",
            )
            for i in range(3)
        ]
        panel.selected_index = 0

        panel.action_cursor_bottom()

        assert panel.selected_index == 2
