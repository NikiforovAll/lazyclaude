"""Tests for LevelSelector widget."""

import pytest

from lazyclaude.models.customization import ConfigLevel
from lazyclaude.widgets.level_selector import LevelSelector


class TestLevelSelector:
    """Tests for LevelSelector widget."""

    def test_initial_state_is_hidden(self) -> None:
        """Widget should be hidden by default."""
        selector = LevelSelector()
        assert not selector.is_visible

    def test_show_adds_visible_class(self) -> None:
        """show() should add visible class."""
        selector = LevelSelector()
        selector._update_prompt = lambda: None  # type: ignore
        selector.focus = lambda: None  # type: ignore
        selector.show([ConfigLevel.USER, ConfigLevel.PROJECT], "copy")
        assert selector.has_class("visible")
        assert selector.is_visible

    def test_hide_removes_visible_class(self) -> None:
        """hide() should remove visible class."""
        selector = LevelSelector()
        selector.add_class("visible")
        selector.hide()
        assert not selector.has_class("visible")
        assert not selector.is_visible

    def test_show_stores_operation(self) -> None:
        """show() should store the operation type."""
        selector = LevelSelector()
        selector._update_prompt = lambda: None  # type: ignore
        selector.focus = lambda: None  # type: ignore
        selector.show([ConfigLevel.USER], "move")
        assert selector._operation == "move"

    def test_show_stores_available_levels(self) -> None:
        """show() should store available levels."""
        selector = LevelSelector()
        selector._update_prompt = lambda: None  # type: ignore
        selector.focus = lambda: None  # type: ignore
        levels = [ConfigLevel.USER, ConfigLevel.PROJECT]
        selector.show(levels, "copy")
        assert selector._available_levels == levels

    def test_default_operation_is_copy(self) -> None:
        """Default operation should be copy."""
        selector = LevelSelector()
        assert selector._operation == "copy"


class TestLevelSelectorMessages:
    """Tests for LevelSelector message emission."""

    @pytest.mark.asyncio
    async def test_select_user_posts_message_when_available(self) -> None:
        """action_select_user should post LevelSelected when USER is available."""
        selector = LevelSelector()
        selector._available_levels = [ConfigLevel.USER, ConfigLevel.PROJECT]
        selector._operation = "copy"

        messages: list[LevelSelector.LevelSelected] = []

        def capture_message(msg: LevelSelector.LevelSelected) -> None:
            messages.append(msg)

        selector.post_message = capture_message  # type: ignore
        selector.hide = lambda: None  # type: ignore

        selector.action_select_user()

        assert len(messages) == 1
        assert messages[0].level == ConfigLevel.USER
        assert messages[0].operation == "copy"

    @pytest.mark.asyncio
    async def test_select_user_does_nothing_when_not_available(self) -> None:
        """action_select_user should do nothing when USER is not available."""
        selector = LevelSelector()
        selector._available_levels = [ConfigLevel.PROJECT]

        messages: list[LevelSelector.LevelSelected] = []
        selector.post_message = lambda msg: messages.append(msg)  # type: ignore

        selector.action_select_user()

        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_select_project_posts_message_when_available(self) -> None:
        """action_select_project should post LevelSelected when PROJECT is available."""
        selector = LevelSelector()
        selector._available_levels = [ConfigLevel.USER, ConfigLevel.PROJECT]
        selector._operation = "move"

        messages: list[LevelSelector.LevelSelected] = []
        selector.post_message = lambda msg: messages.append(msg)  # type: ignore
        selector.hide = lambda: None  # type: ignore

        selector.action_select_project()

        assert len(messages) == 1
        assert messages[0].level == ConfigLevel.PROJECT
        assert messages[0].operation == "move"

    @pytest.mark.asyncio
    async def test_cancel_posts_selection_cancelled(self) -> None:
        """action_cancel should post SelectionCancelled message."""
        selector = LevelSelector()

        messages: list[LevelSelector.SelectionCancelled] = []
        selector.post_message = lambda msg: messages.append(msg)  # type: ignore
        selector.hide = lambda: None  # type: ignore

        selector.action_cancel()

        assert len(messages) == 1
        assert isinstance(messages[0], LevelSelector.SelectionCancelled)


class TestLevelSelectorBindings:
    """Tests for LevelSelector key bindings."""

    def test_has_key_1_binding(self) -> None:
        """Should have binding for key 1."""
        bindings = {b.key for b in LevelSelector.BINDINGS}
        assert "1" in bindings

    def test_has_key_2_binding(self) -> None:
        """Should have binding for key 2."""
        bindings = {b.key for b in LevelSelector.BINDINGS}
        assert "2" in bindings

    def test_has_escape_binding(self) -> None:
        """Should have binding for escape."""
        bindings = {b.key for b in LevelSelector.BINDINGS}
        assert "escape" in bindings
