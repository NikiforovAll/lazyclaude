"""Parser for memory file customizations."""

import re
from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.parsers import ICustomizationParser, parse_frontmatter

MEMORY_FILE_NAMES = {"CLAUDE.md", "AGENTS.md", "CLAUDE.local.md"}


class MemoryFileParser(ICustomizationParser):
    """
    Parser for memory files (CLAUDE.md, AGENTS.md).

    File patterns:
    - ~/.claude/CLAUDE.md (User)
    - .claude/CLAUDE.md or ./CLAUDE.md (Project)
    - ./CLAUDE.local.md (Project, local override)
    """

    def can_parse(self, path: Path) -> bool:
        """Check if path is a known memory file."""
        return path.name in MEMORY_FILE_NAMES

    def parse(self, path: Path, level: ConfigLevel) -> Customization:
        """Parse a memory file."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            return Customization(
                name=path.name,
                type=CustomizationType.MEMORY_FILE,
                level=level,
                path=path,
                error=f"Failed to read file: {e}",
            )

        frontmatter, body = parse_frontmatter(content)

        imports = re.findall(r"^@([^\s]+)", body, re.MULTILINE)

        description = None
        for line in body.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("@"):
                description = line[:100]
                break

        if not description:
            description = "Memory file"

        metadata = {
            "imports": imports,
            "tags": frontmatter.get("tags", []),
        }

        return Customization(
            name=path.name,
            type=CustomizationType.MEMORY_FILE,
            level=level,
            path=path,
            description=description,
            content=content,
            metadata=metadata,
        )
