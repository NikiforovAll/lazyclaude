"""Parsers for Claude Code customization files."""

import re
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from lazyclaude.models.customization import ConfigLevel, Customization


class ICustomizationParser(ABC):
    """Base interface for customization parsers."""

    @abstractmethod
    def parse(self, path: Path, level: ConfigLevel) -> Customization:
        """
        Parse a single customization file.

        Args:
            path: Absolute path to the configuration file.
            level: Configuration level this file belongs to.

        Returns:
            Customization object with parsed content.
            On parse failure, error field is set instead of content.
        """
        ...

    @abstractmethod
    def can_parse(self, path: Path) -> bool:
        """
        Check if this parser can handle the given path.

        Args:
            path: Path to check.

        Returns:
            True if this parser handles this file type.
        """
        ...


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Extract YAML frontmatter and body from markdown content.

    Args:
        content: Full file content.

    Returns:
        Tuple of (frontmatter dict, body content).
        If no frontmatter found, returns ({}, original content).
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError:
            return {}, content
    return {}, content


def parse_tools_list(tools_value: str | list | None) -> list[str]:
    """Parse tools specification into a list of tool names."""
    if tools_value is None:
        return []
    if isinstance(tools_value, list):
        return [str(t).strip() for t in tools_value]
    return [t.strip() for t in str(tools_value).split(",") if t.strip()]


__all__ = [
    "ICustomizationParser",
    "parse_frontmatter",
    "parse_tools_list",
]
