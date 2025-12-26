"""LazyClaude - A lazygit-style TUI for visualizing Claude Code customizations."""

try:
    from lazyclaude._version import __version__
except ImportError:
    __version__ = "0.0.0+dev"

__author__ = "nikiforovall"

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)

__all__ = [
    "__version__",
    "ConfigLevel",
    "Customization",
    "CustomizationType",
]
