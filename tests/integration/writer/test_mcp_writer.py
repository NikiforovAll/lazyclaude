"""Tests for MCP copy/move functionality."""

import json
from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.writer import CustomizationWriter


def _create_mcp_customization(
    name: str,
    level: ConfigLevel,
    path: Path,
    config: dict | None = None,
) -> Customization:
    """Create an MCP customization for testing."""
    if config is None:
        config = {"type": "stdio", "command": f"{name}-cmd"}
    return Customization(
        name=name,
        type=CustomizationType.MCP,
        level=level,
        path=path,
        description=f"Test MCP {name}",
        content=json.dumps(config),
        metadata={"transport_type": config.get("type", "stdio")},
    )


class TestMCPCopyToUser:
    """Tests for copying MCP servers to USER level."""

    def test_copy_mcp_to_user_creates_file(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Copying MCP to user level creates ~/.claude.json."""
        fs.create_dir(fake_project_root / ".claude")
        project_mcp = fake_project_root / ".mcp.json"
        fs.create_file(
            project_mcp, contents='{"mcpServers": {"test-server": {"type": "stdio"}}}'
        )

        customization = _create_mcp_customization(
            "test-server",
            ConfigLevel.PROJECT,
            project_mcp,
            {"type": "stdio", "command": "test-cmd"},
        )
        writer = CustomizationWriter()

        success, msg = writer.write_mcp_customization(
            customization,
            ConfigLevel.USER,
            fake_project_root / ".claude",
        )

        assert success is True
        assert "Copied" in msg
        user_claude_json = fake_home / ".claude.json"
        assert user_claude_json.is_file()
        data = json.loads(user_claude_json.read_text())
        assert "test-server" in data["mcpServers"]

    def test_copy_mcp_to_user_merges_with_existing(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Copying MCP preserves existing mcpServers."""
        fs.create_dir(fake_project_root / ".claude")
        user_claude = fake_home / ".claude.json"
        fs.create_file(
            user_claude,
            contents='{"mcpServers": {"existing-server": {"type": "http"}}}',
        )
        project_mcp = fake_project_root / ".mcp.json"
        fs.create_file(project_mcp, contents='{"mcpServers": {}}')

        customization = _create_mcp_customization(
            "new-server",
            ConfigLevel.PROJECT,
            project_mcp,
        )
        writer = CustomizationWriter()

        success, _ = writer.write_mcp_customization(
            customization,
            ConfigLevel.USER,
            fake_project_root / ".claude",
        )

        assert success is True
        data = json.loads(user_claude.read_text())
        assert "existing-server" in data["mcpServers"]
        assert "new-server" in data["mcpServers"]


class TestMCPCopyToProject:
    """Tests for copying MCP servers to PROJECT level."""

    def test_copy_mcp_to_project_creates_mcp_json(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Copying MCP to project level creates .mcp.json."""
        fs.create_dir(fake_project_root / ".claude")
        user_claude = fake_home / ".claude.json"
        fs.create_file(
            user_claude,
            contents='{"mcpServers": {"user-server": {"type": "stdio"}}}',
        )

        customization = _create_mcp_customization(
            "user-server",
            ConfigLevel.USER,
            user_claude,
        )
        writer = CustomizationWriter()

        success, msg = writer.write_mcp_customization(
            customization,
            ConfigLevel.PROJECT,
            fake_project_root / ".claude",
        )

        assert success is True
        assert "Copied" in msg
        project_mcp = fake_project_root / ".mcp.json"
        assert project_mcp.is_file()
        data = json.loads(project_mcp.read_text())
        assert "user-server" in data["mcpServers"]


class TestMCPCopyToProjectLocal:
    """Tests for copying MCP servers to PROJECT_LOCAL level."""

    def test_copy_mcp_to_project_local_creates_entry(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Copying MCP to project-local adds to ~/.claude.json projects section."""
        fs.create_dir(fake_project_root / ".claude")
        project_mcp = fake_project_root / ".mcp.json"
        fs.create_file(
            project_mcp,
            contents='{"mcpServers": {"project-server": {"type": "stdio"}}}',
        )

        customization = _create_mcp_customization(
            "project-server",
            ConfigLevel.PROJECT,
            project_mcp,
        )
        writer = CustomizationWriter()

        success, msg = writer.write_mcp_customization(
            customization,
            ConfigLevel.PROJECT_LOCAL,
            fake_project_root / ".claude",
        )

        assert success is True
        assert "Project-Local" in msg
        user_claude = fake_home / ".claude.json"
        assert user_claude.is_file()
        data = json.loads(user_claude.read_text())
        project_path = str(fake_project_root).replace("\\", "/")
        assert project_path in data["projects"]
        assert "project-server" in data["projects"][project_path]["mcpServers"]


class TestMCPConflictDetection:
    """Tests for MCP conflict detection."""

    def test_copy_mcp_detects_conflict(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Copying MCP fails if server with same name exists at target."""
        fs.create_dir(fake_project_root / ".claude")
        user_claude = fake_home / ".claude.json"
        fs.create_file(
            user_claude,
            contents='{"mcpServers": {"test-server": {"type": "http"}}}',
        )
        project_mcp = fake_project_root / ".mcp.json"
        fs.create_file(project_mcp, contents='{"mcpServers": {}}')

        customization = _create_mcp_customization(
            "test-server",
            ConfigLevel.PROJECT,
            project_mcp,
        )
        writer = CustomizationWriter()

        success, msg = writer.write_mcp_customization(
            customization,
            ConfigLevel.USER,
            fake_project_root / ".claude",
        )

        assert success is False
        assert "already exists" in msg


class TestMCPDelete:
    """Tests for MCP deletion."""

    def test_delete_mcp_from_user_level(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting MCP removes server from mcpServers."""
        fs.create_dir(fake_project_root / ".claude")
        user_claude = fake_home / ".claude.json"
        fs.create_file(
            user_claude,
            contents='{"mcpServers": {"test-server": {"type": "stdio"}, "other": {"type": "http"}}}',
        )

        customization = _create_mcp_customization(
            "test-server",
            ConfigLevel.USER,
            user_claude,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_mcp_customization(
            customization,
            fake_project_root / ".claude",
        )

        assert success is True
        assert "Deleted" in msg
        data = json.loads(user_claude.read_text())
        assert "test-server" not in data["mcpServers"]
        assert "other" in data["mcpServers"]

    def test_delete_last_mcp_from_project_removes_file(
        self,
        fake_home: Path,  # noqa: ARG002
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting the last MCP from .mcp.json removes the file."""
        fs.create_dir(fake_project_root / ".claude")
        project_mcp = fake_project_root / ".mcp.json"
        fs.create_file(
            project_mcp,
            contents='{"mcpServers": {"only-server": {"type": "stdio"}}}',
        )

        customization = _create_mcp_customization(
            "only-server",
            ConfigLevel.PROJECT,
            project_mcp,
        )
        writer = CustomizationWriter()

        success, _ = writer.delete_mcp_customization(
            customization,
            fake_project_root / ".claude",
        )

        assert success is True
        assert not project_mcp.exists()

    def test_delete_mcp_preserves_other_settings(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting MCP preserves other settings in the file."""
        fs.create_dir(fake_project_root / ".claude")
        user_claude = fake_home / ".claude.json"
        fs.create_file(
            user_claude,
            contents='{"otherSetting": true, "mcpServers": {"test-server": {}}}',
        )

        customization = _create_mcp_customization(
            "test-server",
            ConfigLevel.USER,
            user_claude,
        )
        writer = CustomizationWriter()

        success, _ = writer.delete_mcp_customization(
            customization,
            fake_project_root / ".claude",
        )

        assert success is True
        data = json.loads(user_claude.read_text())
        assert data["otherSetting"] is True

    def test_delete_mcp_not_found_fails(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting non-existent MCP returns error."""
        fs.create_dir(fake_project_root / ".claude")
        user_claude = fake_home / ".claude.json"
        fs.create_file(user_claude, contents='{"mcpServers": {}}')

        customization = _create_mcp_customization(
            "missing-server",
            ConfigLevel.USER,
            user_claude,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_mcp_customization(
            customization,
            fake_project_root / ".claude",
        )

        assert success is False
        assert "not found" in msg


class TestMCPDeleteFromProjectLocal:
    """Tests for deleting MCP from PROJECT_LOCAL level."""

    def test_delete_mcp_from_project_local(
        self,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting MCP from project-local removes from projects section."""
        fs.create_dir(fake_project_root / ".claude")
        project_path = str(fake_project_root).replace("\\", "/")
        user_claude = fake_home / ".claude.json"
        content = {
            "projects": {
                project_path: {
                    "mcpServers": {
                        "local-server": {"type": "http"},
                        "other": {"type": "stdio"},
                    }
                }
            }
        }
        fs.create_file(user_claude, contents=json.dumps(content))

        customization = _create_mcp_customization(
            "local-server",
            ConfigLevel.PROJECT_LOCAL,
            user_claude,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_mcp_customization(
            customization,
            fake_project_root / ".claude",
        )

        assert success is True
        assert "Deleted" in msg
        data = json.loads(user_claude.read_text())
        assert "local-server" not in data["projects"][project_path]["mcpServers"]
        assert "other" in data["projects"][project_path]["mcpServers"]
