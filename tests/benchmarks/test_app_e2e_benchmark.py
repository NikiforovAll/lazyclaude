"""End-to-end benchmark tests for LazyClaude app.

Measures real user-perceived performance:
- Time to first render
- Panel switch latency
- Hidden panel activation
"""

import time
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

import lazyclaude
from lazyclaude.app import LazyClaude
from lazyclaude.services.discovery import ConfigDiscoveryService

LAZYCLAUDE_SRC = Path(lazyclaude.__file__).parent


@pytest.fixture
def app_benchmark_small(
    fs: FakeFilesystem,
    fake_home: Path,
    fake_project_root: Path,
) -> tuple[Path, Path]:
    """Small benchmark config with app source files available."""
    fs.add_real_directory(LAZYCLAUDE_SRC, read_only=True)

    import json

    user_claude = fake_home / ".claude"
    project_claude = fake_project_root / ".claude"

    for d in [
        user_claude / "commands",
        user_claude / "agents",
        user_claude / "skills",
        project_claude / "commands",
        project_claude / "agents",
        project_claude / "skills",
    ]:
        fs.create_dir(d)

    # Create ~20 customizations
    for i in range(4):
        level = user_claude if i % 2 == 0 else project_claude
        fs.create_file(
            level / "commands" / f"cmd-{i}.md",
            contents=f"---\ndescription: Command {i}\n---\nContent {i}",
        )
        fs.create_file(
            level / "agents" / f"agent-{i}.md",
            contents=f"---\ndescription: Agent {i}\n---\nContent {i}",
        )
        skill_dir = level / "skills" / f"skill-{i}"
        fs.create_dir(skill_dir)
        fs.create_file(
            skill_dir / "SKILL.md",
            contents=f"---\ndescription: Skill {i}\n---\nContent {i}",
        )

    fs.create_file(user_claude / "CLAUDE.md", contents="# User memory\n")
    fs.create_file(project_claude / "CLAUDE.md", contents="# Project memory\n")

    fs.create_file(
        fake_home / ".claude.json",
        contents=json.dumps({"mcpServers": {"s1": {"command": "npx", "args": []}}}),
    )
    fs.create_file(
        fake_project_root / ".mcp.json",
        contents=json.dumps({"mcpServers": {"s2": {"command": "npx", "args": []}}}),
    )

    fs.create_file(
        user_claude / "settings.json",
        contents=json.dumps({"hooks": {"PreToolUse": []}}),
    )

    return user_claude, project_claude


@pytest.fixture
def app_benchmark_medium(
    fs: FakeFilesystem,
    fake_home: Path,
    fake_project_root: Path,
) -> tuple[Path, Path]:
    """Medium benchmark config with app source files available."""
    fs.add_real_directory(LAZYCLAUDE_SRC, read_only=True)

    import json

    user_claude = fake_home / ".claude"
    project_claude = fake_project_root / ".claude"

    for d in [
        user_claude / "commands",
        user_claude / "agents",
        user_claude / "skills",
        project_claude / "commands",
        project_claude / "agents",
        project_claude / "skills",
    ]:
        fs.create_dir(d)

    # Create ~100 customizations
    for i in range(20):
        level = user_claude if i % 2 == 0 else project_claude
        fs.create_file(
            level / "commands" / f"cmd-{i}.md",
            contents=f"---\ndescription: Command {i}\n---\nContent {i}",
        )
        fs.create_file(
            level / "agents" / f"agent-{i}.md",
            contents=f"---\ndescription: Agent {i}\n---\nContent {i}",
        )
        skill_dir = level / "skills" / f"skill-{i}"
        fs.create_dir(skill_dir)
        fs.create_file(
            skill_dir / "SKILL.md",
            contents=f"---\ndescription: Skill {i}\n---\nContent {i}",
        )
        for j in range(3):
            fs.create_file(skill_dir / f"file-{j}.py", contents=f"# file {j}\n" * 10)

    fs.create_file(user_claude / "CLAUDE.md", contents="# User memory\n")
    fs.create_file(project_claude / "CLAUDE.md", contents="# Project memory\n")

    mcps = {
        "mcpServers": {f"server-{i}": {"command": "npx", "args": []} for i in range(10)}
    }
    fs.create_file(fake_home / ".claude.json", contents=json.dumps(mcps))
    fs.create_file(fake_project_root / ".mcp.json", contents=json.dumps(mcps))

    fs.create_file(
        user_claude / "settings.json",
        contents=json.dumps({"hooks": {f"Hook{i}": [] for i in range(5)}}),
    )

    return user_claude, project_claude


class TestAppStartupBenchmark:
    """Benchmark app startup and initial render."""

    @pytest.mark.asyncio
    async def test_time_to_first_render_small(
        self,
        app_benchmark_small: tuple[Path, Path],
    ) -> None:
        """Measure time from app creation to first render with small dataset."""
        user_config, project_config = app_benchmark_small
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )

        start = time.perf_counter()
        app = LazyClaude(discovery_service=service)
        async with app.run_test() as pilot:
            await pilot.pause()
            first_render_time = time.perf_counter() - start

        print(f"\n[Small] Time to first render: {first_render_time * 1000:.2f}ms")
        assert first_render_time < 5.0  # Should be under 5 seconds

    @pytest.mark.asyncio
    async def test_time_to_first_render_medium(
        self,
        app_benchmark_medium: tuple[Path, Path],
    ) -> None:
        """Measure time from app creation to first render with medium dataset."""
        user_config, project_config = app_benchmark_medium
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )

        start = time.perf_counter()
        app = LazyClaude(discovery_service=service)
        async with app.run_test() as pilot:
            await pilot.pause()
            first_render_time = time.perf_counter() - start

        print(f"\n[Medium] Time to first render: {first_render_time * 1000:.2f}ms")
        assert first_render_time < 10.0  # Should be under 10 seconds


class TestPanelSwitchBenchmark:
    """Benchmark panel switching latency."""

    @pytest.mark.asyncio
    async def test_panel_switch_1_to_2(
        self,
        app_benchmark_small: tuple[Path, Path],
    ) -> None:
        """Measure time to switch from panel 1 to panel 2."""
        user_config, project_config = app_benchmark_small
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        app = LazyClaude(discovery_service=service)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Focus panel 1 first
            await pilot.press("1")
            await pilot.pause()

            # Measure switch to panel 2
            start = time.perf_counter()
            await pilot.press("2")
            await pilot.pause()
            switch_time = time.perf_counter() - start

        print(f"\n[1->2] Panel switch time: {switch_time * 1000:.2f}ms")
        assert switch_time < 1.0  # Should be under 1 second

    @pytest.mark.asyncio
    async def test_panel_switch_1_to_6_hidden(
        self,
        app_benchmark_small: tuple[Path, Path],
    ) -> None:
        """Measure time to switch from panel 1 to panel 6 (hidden combined panel)."""
        user_config, project_config = app_benchmark_small
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        app = LazyClaude(discovery_service=service)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Focus panel 1 first
            await pilot.press("1")
            await pilot.pause()

            # Measure switch to panel 6 (hooks - hidden panel)
            start = time.perf_counter()
            await pilot.press("6")
            await pilot.pause()
            switch_time = time.perf_counter() - start

        print(f"\n[1->6] Hidden panel switch time: {switch_time * 1000:.2f}ms")
        assert switch_time < 1.0  # Should be under 1 second

    @pytest.mark.asyncio
    async def test_tab_navigation_cycle(
        self,
        app_benchmark_small: tuple[Path, Path],
    ) -> None:
        """Measure time to cycle through all panels using Tab."""
        user_config, project_config = app_benchmark_small
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        app = LazyClaude(discovery_service=service)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Measure full tab cycle (7 panels: 0-6)
            start = time.perf_counter()
            for _ in range(7):
                await pilot.press("tab")
                await pilot.pause()
            cycle_time = time.perf_counter() - start

        print(f"\n[Tab cycle] Full panel cycle time: {cycle_time * 1000:.2f}ms")
        assert cycle_time < 5.0  # Should be under 5 seconds for full cycle


class TestRefreshBenchmark:
    """Benchmark refresh operation in running app."""

    @pytest.mark.asyncio
    async def test_refresh_small(
        self,
        app_benchmark_small: tuple[Path, Path],
    ) -> None:
        """Measure refresh time with small dataset."""
        user_config, project_config = app_benchmark_small
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        app = LazyClaude(discovery_service=service)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Measure refresh
            start = time.perf_counter()
            await pilot.press("r")
            await pilot.pause()
            refresh_time = time.perf_counter() - start

        print(f"\n[Small] Refresh time: {refresh_time * 1000:.2f}ms")
        assert refresh_time < 2.0  # Should be under 2 seconds

    @pytest.mark.asyncio
    async def test_refresh_medium(
        self,
        app_benchmark_medium: tuple[Path, Path],
    ) -> None:
        """Measure refresh time with medium dataset."""
        user_config, project_config = app_benchmark_medium
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        app = LazyClaude(discovery_service=service)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Measure refresh
            start = time.perf_counter()
            await pilot.press("r")
            await pilot.pause()
            refresh_time = time.perf_counter() - start

        print(f"\n[Medium] Refresh time: {refresh_time * 1000:.2f}ms")
        assert refresh_time < 5.0  # Should be under 5 seconds


class TestSearchBenchmark:
    """Benchmark search/filter performance in running app."""

    @pytest.mark.asyncio
    async def test_search_activation(
        self,
        app_benchmark_small: tuple[Path, Path],
    ) -> None:
        """Measure time to activate search and type query."""
        user_config, project_config = app_benchmark_small
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        app = LazyClaude(discovery_service=service)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Measure search activation and typing
            start = time.perf_counter()
            await pilot.press("/")
            await pilot.pause()
            await pilot.press("c", "m", "d")
            await pilot.pause()
            search_time = time.perf_counter() - start

        print(f"\n[Search] Activation + typing time: {search_time * 1000:.2f}ms")
        assert search_time < 2.0  # Should be under 2 seconds

    @pytest.mark.asyncio
    async def test_filter_by_level(
        self,
        app_benchmark_small: tuple[Path, Path],
    ) -> None:
        """Measure time to filter by level (press 'u' for user)."""
        user_config, project_config = app_benchmark_small
        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        app = LazyClaude(discovery_service=service)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Measure level filter
            start = time.perf_counter()
            await pilot.press("u")  # Filter to user level
            await pilot.pause()
            filter_time = time.perf_counter() - start

        print(f"\n[Filter] Level filter time: {filter_time * 1000:.2f}ms")
        assert filter_time < 1.0  # Should be under 1 second
