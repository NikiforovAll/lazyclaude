"""Parser for slash command customizations."""

from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    SlashCommandMetadata,
)
from lazyclaude.services.parsers import (
    ICustomizationParser,
    parse_frontmatter,
    parse_tools_list,
)


class SlashCommandParser(ICustomizationParser):
    """
    Parser for slash command markdown files.

    File pattern: commands/**/*.md
    """

    def __init__(self, commands_dir: Path) -> None:
        """
        Initialize with the commands directory path.

        Args:
            commands_dir: Path to the commands directory (e.g., ~/.claude/commands)
        """
        self.commands_dir = commands_dir

    def can_parse(self, path: Path) -> bool:
        """Check if path is a markdown file in commands directory."""
        return path.suffix == ".md" and self.commands_dir in path.parents

    def parse(self, path: Path, level: ConfigLevel) -> Customization:
        """Parse a slash command markdown file."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            return Customization(
                name=self._derive_name(path),
                type=CustomizationType.SLASH_COMMAND,
                level=level,
                path=path,
                error=f"Failed to read file: {e}",
            )

        frontmatter, body = parse_frontmatter(content)

        description = frontmatter.get("description")
        if not description and body.strip():
            first_line = body.strip().split("\n")[0]
            if not first_line.startswith("#"):
                description = first_line[:100]

        metadata = SlashCommandMetadata(
            allowed_tools=parse_tools_list(frontmatter.get("allowed-tools")),
            argument_hint=frontmatter.get("argument-hint"),
            model=frontmatter.get("model"),
            disable_model_invocation=frontmatter.get(
                "disable-model-invocation", False
            ),
        )

        return Customization(
            name=self._derive_name(path),
            type=CustomizationType.SLASH_COMMAND,
            level=level,
            path=path,
            description=description,
            content=content,
            metadata=metadata.__dict__,
        )

    def _derive_name(self, path: Path) -> str:
        """
        Derive command name from file path.

        For nested paths: dir/file.md -> dir:file
        For simple paths: file.md -> file
        """
        try:
            relative = path.relative_to(self.commands_dir)
            parts = list(relative.parts)
            parts[-1] = parts[-1].removesuffix(".md")
            return ":".join(parts)
        except ValueError:
            return path.stem
