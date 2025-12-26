"""Help mixin for LazyClaude application."""

from textual.widgets import Static

from lazyclaude import __version__


class HelpMixin:
    """Mixin providing help overlay functionality."""

    _help_visible: bool

    def action_toggle_help(self) -> None:
        """Toggle help overlay visibility."""
        if self._help_visible:
            self._hide_help()
        else:
            self._show_help()

    def _show_help(self) -> None:
        """Show help overlay."""
        help_content = f"""[bold]LazyClaude v{__version__}[/]

[bold]Navigation[/]
  j/k or Up/Down     Move up/down in list
  d/u            Page down/up (detail pane)
  g/G            Go to top/bottom
  0              Focus main pane
  1-3            Focus panel by number
  4-6            Focus combined panel tab
  Tab            Switch between panels
  Enter          Drill down
  Esc            Go back

[bold]Filtering[/]
  /              Search by name/description
  a              Show all levels
  u              Show user-level only
  p              Show project-level only
  P              Show plugin-level only
  D              Toggle disabled plugins

[bold]Views[/]
  [ / ]         Main: content/metadata
                 Combined: switch tabs

[bold]Actions[/]
  e              Open in $EDITOR
  c              Copy to level
  m              Move to level
  t              Toggle plugin enabled
  C              Copy path to clipboard
  r              Refresh from disk
  Ctrl+u         Open user config
  M              Open marketplace
  ?              Toggle this help
  q              Quit

[dim]Press ? or Esc to close[/]"""

        if not self.query("#help-overlay"):  # type: ignore[attr-defined]
            help_widget = Static(help_content, id="help-overlay")
            self.mount(help_widget)  # type: ignore[attr-defined]
            self._help_visible = True

    def _hide_help(self) -> None:
        """Hide help overlay."""
        try:
            help_widget = self.query_one("#help-overlay")  # type: ignore[attr-defined]
            help_widget.remove()
            self._help_visible = False
        except Exception:
            pass
