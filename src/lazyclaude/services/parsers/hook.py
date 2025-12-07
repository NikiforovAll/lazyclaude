"""Parser for hook customizations."""

import json
from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.parsers import ICustomizationParser


class HookParser(ICustomizationParser):
    """
    Parser for hook configurations.

    File patterns:
    - ~/.claude/settings.json -> hooks (User)
    - ./.claude/settings.json -> hooks (Project)
    - ./.claude/settings.local.json -> hooks (Project-Local)
    - {plugin}/hooks/hooks.json -> hooks (Plugin)

    Each file with hooks becomes one item in the panel.
    """

    HOOK_FILE_NAMES = {"settings.json", "settings.local.json", "hooks.json"}

    def can_parse(self, path: Path) -> bool:
        """Check if path is a known hook config file."""
        return path.name in self.HOOK_FILE_NAMES

    def parse(self, path: Path, level: ConfigLevel) -> list[Customization]:  # type: ignore[override]
        """
        Parse a configuration file for hooks.

        Returns a single Customization if hooks are present, empty list otherwise.
        """
        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError) as e:
            return [
                Customization(
                    name=path.name,
                    type=CustomizationType.HOOK,
                    level=level,
                    path=path,
                    error=f"Failed to parse hook config: {e}",
                )
            ]

        hooks_data = data.get("hooks", {})
        if not hooks_data:
            return []

        event_names = list(hooks_data.keys())
        description = ", ".join(event_names) if event_names else "hooks"

        name = "hooks" if path.name == "hooks.json" else path.name

        return [
            Customization(
                name=name,
                type=CustomizationType.HOOK,
                level=level,
                path=path,
                description=description,
                content=json.dumps(hooks_data, indent=2),
                metadata={},
            )
        ]

    def parse_single(self, path: Path, level: ConfigLevel) -> Customization:
        """Parse interface implementation - returns hook config or empty."""
        results = self.parse(path, level)
        if results:
            return results[0]
        return Customization(
            name=path.name,
            type=CustomizationType.HOOK,
            level=level,
            path=path,
            description="No hooks configured",
            content="{}",
            metadata={},
        )
