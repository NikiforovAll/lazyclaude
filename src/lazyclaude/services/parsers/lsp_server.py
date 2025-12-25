"""Parser for LSP server customizations."""

import json
from pathlib import Path
from typing import Any

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    LSPServerMetadata,
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
        args = server_config.get("args", [])
        extension_to_language = server_config.get("extensionToLanguage", {})
        transport = server_config.get("transport", "stdio")
        env = server_config.get("env", {})
        initialization_options = server_config.get("initializationOptions", {})
        settings = server_config.get("settings", {})

        if command:
            description = f"{transport.upper()} command: {command}"
        else:
            description = f"{transport.upper()} server"

        metadata = LSPServerMetadata(
            command=command,
            args=args if isinstance(args, list) else [],
            extension_to_language=(
                extension_to_language if isinstance(extension_to_language, dict) else {}
            ),
            transport=transport,
            env=env if isinstance(env, dict) else {},
            initialization_options=(
                initialization_options
                if isinstance(initialization_options, dict)
                else {}
            ),
            settings=settings if isinstance(settings, dict) else {},
        )

        return Customization(
            name=language_name,
            type=CustomizationType.LSP_SERVER,
            level=level,
            path=source_path,
            description=description,
            content=json.dumps(server_config, indent=2),
            metadata=metadata.__dict__,
        )

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
