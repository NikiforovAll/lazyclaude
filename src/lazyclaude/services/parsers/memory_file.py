"""Parser for memory file customizations."""

import re
from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    MemoryFileRef,
)
from lazyclaude.services.parsers import ICustomizationParser, parse_frontmatter

MEMORY_FILE_NAMES = {"CLAUDE.md", "AGENTS.md", "CLAUDE.local.md"}
MAX_IMPORT_DEPTH = 5


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

        imports = re.findall(r"@([\w./~-]+\.md)", body)

        description = None
        for line in body.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("@"):
                description = line[:100]
                break

        if not description:
            description = "Memory file"

        refs = self._resolve_references(imports, path.parent)

        metadata = {
            "imports": imports,
            "tags": frontmatter.get("tags", []),
            "refs": refs,
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

    def _resolve_references(
        self,
        imports: list[str],
        base_dir: Path,
        depth: int = 0,
        visited: set[Path] | None = None,
    ) -> list[MemoryFileRef]:
        """Resolve @path references recursively."""
        if visited is None:
            visited = set()

        refs: list[MemoryFileRef] = []
        for ref_name in imports:
            ref = self._resolve_single_reference(ref_name, base_dir, depth, visited)
            refs.append(ref)
        return refs

    def _resolve_single_reference(
        self,
        ref_name: str,
        base_dir: Path,
        depth: int,
        visited: set[Path],
    ) -> MemoryFileRef:
        """Resolve a single @path reference."""
        if depth >= MAX_IMPORT_DEPTH:
            return MemoryFileRef(name=ref_name, path=None, exists=False)

        resolved = self._resolve_path(ref_name, base_dir)
        if resolved is None:
            return MemoryFileRef(name=ref_name, path=None, exists=False)

        try:
            resolved = resolved.resolve()
        except OSError:
            return MemoryFileRef(name=ref_name, path=None, exists=False)

        if resolved in visited:
            return MemoryFileRef(name=ref_name, path=resolved, exists=True)

        visited.add(resolved)

        if not resolved.exists() or not resolved.is_file():
            return MemoryFileRef(name=ref_name, path=resolved, exists=False)

        try:
            content = resolved.read_text(encoding="utf-8")
        except OSError:
            return MemoryFileRef(name=ref_name, path=resolved, exists=True)

        nested_imports = re.findall(r"@([\w./~-]+\.md)", content)
        children = self._resolve_references(
            nested_imports, resolved.parent, depth + 1, visited
        )

        return MemoryFileRef(
            name=ref_name,
            path=resolved,
            content=content,
            exists=True,
            children=children,
        )

    def _resolve_path(self, ref: str, base_dir: Path) -> Path | None:
        """Resolve a reference path to an absolute path."""
        if ref.startswith("~/"):
            return Path.home() / ref[2:]
        if ref.startswith("/"):
            return Path(ref)
        if len(ref) > 1 and ref[1] == ":":
            return Path(ref)
        return base_dir / ref
