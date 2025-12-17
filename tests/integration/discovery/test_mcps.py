"""Tests for MCP server discovery."""

import json
from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

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


class TestLocalMCPDiscovery:
    """Tests for local-scoped MCP discovery from ~/.claude.json projects."""

    def test_discovers_local_mcps_from_projects(
        self,
        user_config_path: Path,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Discovers MCPs from ~/.claude.json projects section."""
        claude_json = fake_home / ".claude.json"
        resolved_path = str(fake_project_root.resolve()).replace("\\", "/")
        content = {
            "projects": {
                resolved_path: {
                    "mcpServers": {
                        "local-server": {
                            "type": "http",
                            "url": "https://api.example.com/mcp",
                        }
                    }
                }
            }
        }
        fs.create_file(claude_json, contents=json.dumps(content))

        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        mcps = service.discover_by_type(CustomizationType.MCP)

        local_mcps = [m for m in mcps if m.level == ConfigLevel.PROJECT_LOCAL]
        assert len(local_mcps) == 1
        assert local_mcps[0].name == "local-server"

    def test_local_mcp_metadata_parsed(
        self,
        user_config_path: Path,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Local MCP metadata is correctly parsed."""
        claude_json = fake_home / ".claude.json"
        resolved_path = str(fake_project_root.resolve()).replace("\\", "/")
        content = {
            "projects": {
                resolved_path: {
                    "mcpServers": {
                        "local-server": {
                            "type": "http",
                            "url": "https://api.example.com/mcp",
                        }
                    }
                }
            }
        }
        fs.create_file(claude_json, contents=json.dumps(content))

        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        mcps = service.discover_by_type(CustomizationType.MCP)

        local_server = next(m for m in mcps if m.level == ConfigLevel.PROJECT_LOCAL)
        assert local_server.metadata.get("transport_type") == "http"
        assert local_server.metadata.get("url") == "https://api.example.com/mcp"

    def test_handles_missing_projects_key(
        self,
        user_config_path: Path,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Handles ~/.claude.json without projects key gracefully."""
        claude_json = fake_home / ".claude.json"
        fs.create_file(claude_json, contents=json.dumps({"mcpServers": {}}))

        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        mcps = service.discover_by_type(CustomizationType.MCP)
        local_mcps = [m for m in mcps if m.level == ConfigLevel.PROJECT_LOCAL]
        assert len(local_mcps) == 0

    def test_handles_project_not_in_projects_list(
        self,
        user_config_path: Path,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Returns empty when current project is not in projects list."""
        claude_json = fake_home / ".claude.json"
        content = {
            "projects": {
                "/some/other/project": {
                    "mcpServers": {"other-server": {"type": "stdio"}}
                }
            }
        }
        fs.create_file(claude_json, contents=json.dumps(content))

        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        mcps = service.discover_by_type(CustomizationType.MCP)
        local_mcps = [m for m in mcps if m.level == ConfigLevel.PROJECT_LOCAL]
        assert len(local_mcps) == 0

    def test_handles_backslash_path_format(
        self,
        user_config_path: Path,
        fake_home: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Discovers local MCPs when path uses backslashes."""
        claude_json = fake_home / ".claude.json"
        resolved_path = str(fake_project_root.resolve())
        backslash_path = resolved_path.replace("/", "\\")
        content = {
            "projects": {
                backslash_path: {
                    "mcpServers": {
                        "backslash-server": {"type": "sse", "url": "http://localhost"}
                    }
                }
            }
        }
        fs.create_file(claude_json, contents=json.dumps(content))

        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        mcps = service.discover_by_type(CustomizationType.MCP)
        local_mcps = [m for m in mcps if m.level == ConfigLevel.PROJECT_LOCAL]
        assert len(local_mcps) == 1
        assert local_mcps[0].name == "backslash-server"
