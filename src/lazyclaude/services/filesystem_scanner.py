"""Generic filesystem scanner for discovering customization files."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lazyclaude.models.customization import ConfigLevel, Customization, PluginInfo

if TYPE_CHECKING:
    from lazyclaude.services.gitignore_filter import GitignoreFilter


class GlobStrategy(Enum):
    """How to scan for files in a directory."""

    RGLOB = auto()  # Recursive: commands/**/*.md
    GLOB = auto()  # Flat: agents/*.md
    SUBDIR = auto()  # Subdirectory pattern: skills/*/SKILL.md


@dataclass
class ScanConfig:
    """Configuration for a single directory scan."""

    subdir: str
    pattern: str
    strategy: GlobStrategy
    parser_factory: Callable[[Path], Any]


class FilesystemScanner:
    """Scans directories for customization files using configurable patterns."""

    def __init__(self, gitignore_filter: "GitignoreFilter | None" = None) -> None:
        self._filter = gitignore_filter

    def scan_directory(
        self,
        base_path: Path,
        config: ScanConfig,
        level: ConfigLevel,
        plugin_info: PluginInfo | None = None,
    ) -> list[Customization]:
        """
        Scan a directory for customization files.

        Args:
            base_path: Root directory to scan (e.g., ~/.claude or plugin install path)
            config: Scan configuration defining subdir, pattern, strategy
            level: ConfigLevel to assign to discovered items
            plugin_info: Optional plugin info to attach to customizations

        Returns:
            List of discovered customizations
        """
        customizations: list[Customization] = []
        target_dir = base_path / config.subdir

        if not target_dir.is_dir():
            return customizations

        try:
            parser = config.parser_factory(target_dir, gitignore_filter=self._filter)  # type: ignore[call-arg]
        except TypeError:
            parser = config.parser_factory(target_dir)

        files = self._get_files(target_dir, config)

        for file_path in files:
            customization: Customization = parser.parse(file_path, level)
            if plugin_info:
                customization.plugin_info = plugin_info
            customizations.append(customization)

        return customizations

    def _get_files(self, target_dir: Path, config: ScanConfig) -> list[Path]:
        """Get files based on scan strategy."""
        if config.strategy == GlobStrategy.RGLOB:
            if self._filter:
                return list(self._filter.walk_filtered(target_dir, config.pattern))
            return list(target_dir.rglob(config.pattern))
        elif config.strategy == GlobStrategy.GLOB:
            files = list(target_dir.glob(config.pattern))
            if self._filter:
                return [f for f in files if not self._filter.is_ignored(f)]
            return files
        elif config.strategy == GlobStrategy.SUBDIR:
            subdirs = [
                subdir
                for subdir in target_dir.iterdir()
                if subdir.is_dir()
                and (
                    not self._filter
                    or (
                        not self._filter.should_skip_dir(subdir.name)
                        and not self._filter.is_dir_ignored(subdir)
                    )
                )
            ]
            files = [
                subdir / config.pattern
                for subdir in subdirs
                if (subdir / config.pattern).is_file()
            ]
            if self._filter:
                return [f for f in files if not self._filter.is_ignored(f)]
            return files
        return []
