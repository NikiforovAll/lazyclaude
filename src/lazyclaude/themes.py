"""Custom themes for LazyClaude TUI application."""

from textual.theme import Theme

LAZYGIT_THEME = Theme(
    name="lazygit",
    primary="#d4d4d4",
    secondary="#808080",
    accent="#4a90d9",
    foreground="#cccccc",
    background="#1a1a1a",
    surface="#222222",
    panel="#2d2d2d",
    success="#98c379",
    warning="#e5c07b",
    error="#e06c75",
    dark=True,
    variables={
        "border": "#3a3a3a",
        "footer-background": "#1a1a1a",
        "footer-foreground": "#808080",
        "footer-key-background": "#1a1a1a",
        "footer-key-foreground": "#4a90d9",
        "footer-description-foreground": "#707070",
    },
)

CUSTOM_THEMES = [LAZYGIT_THEME]

DEFAULT_THEME = "gruvbox"
