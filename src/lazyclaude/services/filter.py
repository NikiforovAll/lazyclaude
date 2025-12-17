"""Service for filtering customizations."""

from abc import ABC, abstractmethod

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    PluginScope,
)


class IFilterService(ABC):
    """Service for filtering customizations."""

    @abstractmethod
    def filter(
        self,
        customizations: list[Customization],
        query: str = "",
        level: ConfigLevel | None = None,
        plugin_enabled: bool | None = None,
    ) -> list[Customization]:
        """
        Filter customizations by search query and/or level.

        Args:
            customizations: Source list to filter.
            query: Search string (matches name only).
            level: Optional level filter (None = all levels).
            plugin_enabled: Optional plugin enabled filter (None = both, True = enabled only, False = disabled only).

        Returns:
            Filtered list maintaining original order.
        """
        ...

    @abstractmethod
    def by_type(
        self,
        customizations: list[Customization],
        ctype: CustomizationType,
    ) -> list[Customization]:
        """
        Get customizations of a specific type.

        Args:
            customizations: Source list.
            ctype: Type to filter by.

        Returns:
            Customizations of the specified type.
        """
        ...


class FilterService(IFilterService):
    """Implementation of customization filtering."""

    def filter(
        self,
        customizations: list[Customization],
        query: str = "",
        level: ConfigLevel | None = None,
        plugin_enabled: bool | None = None,
    ) -> list[Customization]:
        """Filter customizations by search query and/or level."""
        result = customizations

        if level is not None:
            result = [c for c in result if self._matches_level(c, level)]

        if plugin_enabled is not None:
            result = [
                c
                for c in result
                if c.plugin_info is None or c.plugin_info.is_enabled == plugin_enabled
            ]

        if query:
            query_lower = query.lower()
            result = [c for c in result if self._matches_query(c, query_lower)]

        return result

    def _matches_level(self, customization: Customization, level: ConfigLevel) -> bool:
        """Check if customization matches the level filter.

        PROJECT_LOCAL items and project-scoped plugins (PluginScope.PROJECT and
        PluginScope.PROJECT_LOCAL) match both their own level and PROJECT level.
        """
        if customization.level == level:
            return True

        if level == ConfigLevel.PROJECT:
            # PROJECT_LOCAL items appear in Project filter
            if customization.level == ConfigLevel.PROJECT_LOCAL:
                return True
            # Project-scoped plugins also appear in Project filter
            if (
                customization.plugin_info is not None
                and customization.plugin_info.scope
                in (PluginScope.PROJECT, PluginScope.PROJECT_LOCAL)
            ):
                return True

        return False

    def _matches_query(self, customization: Customization, query: str) -> bool:
        """Check if customization matches the search query."""
        if query in customization.name.lower():
            return True
        if customization.plugin_info:
            prefix = f"{customization.plugin_info.short_name}:".lower()
            full_name = f"{prefix}{customization.name.lower()}"
            if query in prefix or query in full_name:
                return True
        return False

    def by_type(
        self,
        customizations: list[Customization],
        ctype: CustomizationType,
    ) -> list[Customization]:
        """Get customizations of a specific type."""
        return [c for c in customizations if c.type == ctype]
