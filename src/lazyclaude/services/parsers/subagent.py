"""Parser for subagent customizations."""

from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    SubagentMetadata,
)
from lazyclaude.services.parsers import (
    ICustomizationParser,
    parse_frontmatter,
    parse_tools_list,
)


class SubagentParser(ICustomizationParser):
    """
    Parser for subagent markdown files.

    File pattern: agents/*.md
    """

    def __init__(self, agents_dir: Path) -> None:
        """
        Initialize with the agents directory path.

        Args:
            agents_dir: Path to the agents directory (e.g., ~/.claude/agents)
        """
        self.agents_dir = agents_dir

    def can_parse(self, path: Path) -> bool:
        """Check if path is a markdown file in agents directory."""
        return path.suffix == ".md" and path.parent == self.agents_dir

    def parse(self, path: Path, level: ConfigLevel) -> Customization:
        """Parse a subagent markdown file."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            return Customization(
                name=path.stem,
                type=CustomizationType.SUBAGENT,
                level=level,
                path=path,
                error=f"Failed to read file: {e}",
            )

        frontmatter, _ = parse_frontmatter(content)

        name = frontmatter.get("name", path.stem)
        description = frontmatter.get("description")

        skills_value = frontmatter.get("skills")
        skills = []
        if skills_value:
            if isinstance(skills_value, list):
                skills = [str(s).strip() for s in skills_value]
            else:
                skills = [s.strip() for s in str(skills_value).split(",") if s.strip()]

        metadata = SubagentMetadata(
            tools=parse_tools_list(frontmatter.get("tools")),
            model=frontmatter.get("model"),
            permission_mode=frontmatter.get("permission-mode"),
            skills=skills,
        )

        return Customization(
            name=name,
            type=CustomizationType.SUBAGENT,
            level=level,
            path=path,
            description=description,
            content=content,
            metadata=metadata.__dict__,
        )
