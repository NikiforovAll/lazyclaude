"""Service for filtering customizations."""

from abc import ABC, abstractmethod

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)


class IFilterService(ABC):
    """Service for filtering customizations."""

    @abstractmethod
    def filter(
        self,
        customizations: list[Customization],
        query: str = "",
        level: ConfigLevel | None = None,
    ) -> list[Customization]:
        """
        Filter customizations by search query and/or level.

        Args:
            customizations: Source list to filter.
            query: Search string (matches name only).
            level: Optional level filter (None = all levels).

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
    ) -> list[Customization]:
        """Filter customizations by search query and/or level."""
        result = customizations

        if level is not None:
            result = [c for c in result if c.level == level]

        if query:
            query_lower = query.lower()
            result = [c for c in result if self._matches_query(c, query_lower)]

        return result

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
