"""Core data models for Claude Code customizations."""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ConfigLevel(Enum):
    """Configuration level where a customization is defined."""

    USER = auto()  # ~/.claude/
    PROJECT = auto()  # ./.claude/
    PROJECT_LOCAL = auto()  # ~/.claude.json (for MCPs only)


class CustomizationType(Enum):
    """Type of Claude Code customization."""

    SLASH_COMMAND = auto()
    SUBAGENT = auto()
    SKILL = auto()
    MEMORY_FILE = auto()
    MCP = auto()


@dataclass
class SlashCommandMetadata:
    """Metadata specific to slash commands."""

    allowed_tools: list[str] = field(default_factory=list)
    argument_hint: str | None = None
    model: str | None = None
    disable_model_invocation: bool = False


@dataclass
class SubagentMetadata:
    """Metadata specific to subagents."""

    tools: list[str] = field(default_factory=list)
    model: str | None = None
    permission_mode: str | None = None
    skills: list[str] = field(default_factory=list)


@dataclass
class SkillMetadata:
    """Metadata specific to skills."""

    tags: list[str] = field(default_factory=list)
    has_reference: bool = False
    has_examples: bool = False
    has_scripts: bool = False
    has_templates: bool = False


@dataclass
class MCPServerMetadata:
    """Metadata specific to MCP servers."""

    transport_type: str = "stdio"  # "stdio" | "http" | "sse"
    command: str | None = None
    url: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class Customization:
    """A Claude Code customization item."""

    name: str
    type: CustomizationType
    level: ConfigLevel
    path: Path

    description: str | None = None
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    error: str | None = None

    @property
    def has_error(self) -> bool:
        """Check if this customization failed to load."""
        return self.error is not None

    @property
    def display_name(self) -> str:
        """Name for display in UI, with level indicator."""
        level_indicator = {
            ConfigLevel.USER: "[U]",
            ConfigLevel.PROJECT: "[P]",
            ConfigLevel.PROJECT_LOCAL: "[L]",
        }
        return f"{self.name} {level_indicator[self.level]}"

    @property
    def level_label(self) -> str:
        """Human-readable level label."""
        return {
            ConfigLevel.USER: "User",
            ConfigLevel.PROJECT: "Project",
            ConfigLevel.PROJECT_LOCAL: "Project-Local",
        }[self.level]

    @property
    def type_label(self) -> str:
        """Human-readable type label."""
        return {
            CustomizationType.SLASH_COMMAND: "Slash Command",
            CustomizationType.SUBAGENT: "Subagent",
            CustomizationType.SKILL: "Skill",
            CustomizationType.MEMORY_FILE: "Memory File",
            CustomizationType.MCP: "MCP Server",
        }[self.type]
