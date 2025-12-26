"""Services for LazyClaude."""

from lazyclaude.services.discovery import (
    ConfigDiscoveryService,
    IConfigDiscoveryService,
)
from lazyclaude.services.filter import FilterService, IFilterService
from lazyclaude.services.gitignore_filter import GitignoreFilter
from lazyclaude.services.settings import SettingsService

__all__ = [
    "ConfigDiscoveryService",
    "FilterService",
    "GitignoreFilter",
    "IConfigDiscoveryService",
    "IFilterService",
    "SettingsService",
]
