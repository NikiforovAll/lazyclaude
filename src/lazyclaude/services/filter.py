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
            query: Search string (matches name and description).
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
            result = [
                c
                for c in result
                if query_lower in c.name.lower()
                or (c.description and query_lower in c.description.lower())
            ]

        return result

    def by_type(
        self,
        customizations: list[Customization],
        ctype: CustomizationType,
    ) -> list[Customization]:
        """Get customizations of a specific type."""
        return [c for c in customizations if c.type == ctype]
