"""Parser for skill customizations."""

from pathlib import Path

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    SkillFile,
    SkillMetadata,
)
from lazyclaude.services.parsers import ICustomizationParser, parse_frontmatter


def _read_skill_files(
    directory: Path, exclude: set[str] | None = None
) -> list[SkillFile]:
    """Recursively read all files in a skill directory."""
    if exclude is None:
        exclude = set()

    files: list[SkillFile] = []
    try:
        entries = sorted(
            directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
        )
    except OSError:
        return files

    for entry in entries:
        if entry.name in exclude or entry.name.startswith("."):
            continue

        if entry.is_dir():
            children = _read_skill_files(entry)
            files.append(
                SkillFile(
                    name=entry.name,
                    path=entry,
                    is_directory=True,
                    children=children,
                )
            )
        elif entry.is_file():
            try:
                content = entry.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                content = None
            files.append(
                SkillFile(
                    name=entry.name,
                    path=entry,
                    content=content,
                )
            )

    return files


class SkillParser(ICustomizationParser):
    """
    Parser for skill directories.

    File pattern: skills/*/SKILL.md
    """

    def __init__(self, skills_dir: Path) -> None:
        """
        Initialize with the skills directory path.

        Args:
            skills_dir: Path to the skills directory (e.g., ~/.claude/skills)
        """
        self.skills_dir = skills_dir

    def can_parse(self, path: Path) -> bool:
        """Check if path is a SKILL.md file in a skill subdirectory."""
        return path.name == "SKILL.md" and path.parent.parent == self.skills_dir

    def parse(self, path: Path, level: ConfigLevel) -> Customization:
        """Parse a skill SKILL.md file and detect directory contents."""
        skill_dir = path.parent

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            return Customization(
                name=skill_dir.name,
                type=CustomizationType.SKILL,
                level=level,
                path=path,
                error=f"Failed to read file: {e}",
            )

        frontmatter, _ = parse_frontmatter(content)

        name = frontmatter.get("name") or skill_dir.name
        description = frontmatter.get("description")

        tags_value = frontmatter.get("tags")
        tags = []
        if tags_value:
            if isinstance(tags_value, list):
                tags = [str(t).strip() for t in tags_value]
            else:
                tags = [t.strip() for t in str(tags_value).split(",") if t.strip()]

        skill_files = _read_skill_files(skill_dir, exclude={"SKILL.md"})

        metadata = SkillMetadata(
            tags=tags,
            has_reference=(skill_dir / "reference.md").exists(),
            has_examples=(skill_dir / "examples.md").exists(),
            has_scripts=(skill_dir / "scripts").is_dir(),
            has_templates=(skill_dir / "templates").is_dir(),
            files=skill_files,
        )

        return Customization(
            name=name,
            type=CustomizationType.SKILL,
            level=level,
            path=path,
            description=description,
            content=content,
            metadata=metadata.__dict__,
        )
