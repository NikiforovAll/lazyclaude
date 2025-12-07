"""Tests for MCP server discovery."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestMCPDiscovery:
    """Tests for MCP server discovery."""

    def test_discovers_user_mcps(
        self,
        user_config_path: Path,
        user_mcp_config: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        mcps = service.discover_by_type(CustomizationType.MCP)

        user_mcps = [m for m in mcps if m.level == ConfigLevel.USER]
        assert len(user_mcps) == 1
        assert user_mcps[0].name == "user-server"

    def test_discovers_project_mcps(
        self,
        user_config_path: Path,
        project_config_path: Path,
        project_mcp_config: Path,  # noqa: ARG002
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=project_config_path,
        )

        mcps = service.discover_by_type(CustomizationType.MCP)

        project_mcps = [m for m in mcps if m.level == ConfigLevel.PROJECT]
        assert len(project_mcps) == 1
        assert project_mcps[0].name == "project-server"

    def test_mcp_metadata_parsed(
        self,
        user_config_path: Path,
        user_mcp_config: Path,  # noqa: ARG002
        fake_project_root: Path,
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        mcps = service.discover_by_type(CustomizationType.MCP)

        user_server = next(m for m in mcps if m.name == "user-server")
        assert user_server.metadata.get("transport_type") == "stdio"
        assert user_server.metadata.get("command") == "user-mcp"
