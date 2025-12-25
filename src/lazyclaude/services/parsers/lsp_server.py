"""Parser for LSP server customizations."""

import json
from pathlib import Path
from typing import Any

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.parsers import ICustomizationParser


class LSPServerParser(ICustomizationParser):
    """
    Parser for LSP server configurations.

    File patterns:
    - {plugin}/.lsp.json -> language server configs
    - {plugin}/.claude-plugin/plugin.json -> lspServers field
    """

    LSP_FILE_NAMES = {".lsp.json"}

    def can_parse(self, path: Path) -> bool:
        """Check if path is a known LSP config file."""
        return path.name in self.LSP_FILE_NAMES

    def parse(self, path: Path, level: ConfigLevel) -> list[Customization]:  # type: ignore[override]
        """
        Parse an LSP configuration file.

        Returns a list of Customization objects, one per language server.
        """
        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError) as e:
            return [
                Customization(
                    name=path.name,
                    type=CustomizationType.LSP_SERVER,
                    level=level,
                    path=path,
                    error=f"Failed to parse LSP config: {e}",
                )
            ]

        if not data or not isinstance(data, dict):
            return []

        customizations = []
        for language_name, server_config in data.items():
            if isinstance(server_config, dict):
                customizations.append(
                    self.parse_server_config(language_name, server_config, path, level)
                )

        return customizations

    def parse_server_config(
        self,
        language_name: str,
        server_config: dict[str, Any],
        source_path: Path,
        level: ConfigLevel,
    ) -> Customization:
        """Parse a single LSP server configuration."""
        command = server_config.get("command")
        transport = server_config.get("transport", "stdio")

        if command:
            description = f"{transport.upper()} command: {command}"
        else:
            description = f"{transport.upper()} server"

        return Customization(
            name=language_name,
            type=CustomizationType.LSP_SERVER,
            level=level,
            path=source_path,
            description=description,
            content=json.dumps(server_config, indent=2),
            metadata=server_config,
        )

    def parse_plugin_json(self, path: Path, level: ConfigLevel) -> list[Customization]:
        """
        Parse lspServers field from a plugin.json file.

        Returns a list of Customization objects, one per language server.
        Returns an error customization if parsing fails.
        """
        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError) as e:
            return [
                Customization(
                    name=path.name,
                    type=CustomizationType.LSP_SERVER,
                    level=level,
                    path=path,
                    error=f"Failed to parse plugin.json for LSP servers: {e}",
                )
            ]

        lsp_servers = data.get("lspServers", {})
        if not lsp_servers or not isinstance(lsp_servers, dict):
            return []

        customizations = []
        for language_name, server_config in lsp_servers.items():
            if isinstance(server_config, dict):
                customizations.append(
                    self.parse_server_config(language_name, server_config, path, level)
                )

        return customizations

    def parse_single(self, path: Path, level: ConfigLevel) -> Customization:
        """
        Parse interface implementation - returns first server or error.

        For LSP files, prefer using parse() directly to get all servers.
        """
        results = self.parse(path, level)
        if results:
            return results[0]
        return Customization(
            name=path.name,
            type=CustomizationType.LSP_SERVER,
            level=level,
            path=path,
            description="No LSP servers configured",
            content="{}",
            metadata={},
        )
