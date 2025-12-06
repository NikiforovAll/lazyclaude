"""Parser for MCP server customizations."""

import json
from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    MCPServerMetadata,
)
from lazyclaude.services.parsers import ICustomizationParser


class MCPParser(ICustomizationParser):
    """
    Parser for MCP server configurations.

    File patterns:
    - ~/.claude.json -> mcpServers (User)
    - ./.mcp.json -> mcpServers (Project)
    """

    MCP_FILE_NAMES = {".claude.json", ".mcp.json"}

    def can_parse(self, path: Path) -> bool:
        """Check if path is a known MCP config file."""
        return path.name in self.MCP_FILE_NAMES

    def parse(self, path: Path, level: ConfigLevel) -> list[Customization]:
        """
        Parse an MCP configuration file.

        Returns a list of Customization objects, one per server.
        """
        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError) as e:
            return [
                Customization(
                    name=path.name,
                    type=CustomizationType.MCP,
                    level=level,
                    path=path,
                    error=f"Failed to parse MCP config: {e}",
                )
            ]

        mcp_servers = data.get("mcpServers", {})
        if not mcp_servers:
            return []

        customizations = []
        for server_name, server_config in mcp_servers.items():
            transport_type = server_config.get("type", "stdio")
            command = server_config.get("command")
            url = server_config.get("url")
            args = server_config.get("args", [])
            env = server_config.get("env", {})

            if transport_type in ("http", "sse") and url:
                description = f"{transport_type.upper()} server: {url}"
            elif command:
                description = f"{transport_type.upper()} command: {command}"
            else:
                description = f"{transport_type.upper()} server"

            metadata = MCPServerMetadata(
                transport_type=transport_type,
                command=command,
                url=url,
                args=args if isinstance(args, list) else [],
                env=env if isinstance(env, dict) else {},
            )

            customizations.append(
                Customization(
                    name=server_name,
                    type=CustomizationType.MCP,
                    level=level,
                    path=path,
                    description=description,
                    content=json.dumps(server_config, indent=2),
                    metadata=metadata.__dict__,
                )
            )

        return customizations

    def parse_single(self, path: Path, level: ConfigLevel) -> Customization:
        """
        Parse interface implementation - returns first server or error.

        For MCP files, prefer using parse() directly to get all servers.
        """
        results = self.parse(path, level)
        if results:
            return results[0]
        return Customization(
            name=path.name,
            type=CustomizationType.MCP,
            level=level,
            path=path,
            description="No MCP servers configured",
            content="{}",
            metadata={},
        )
