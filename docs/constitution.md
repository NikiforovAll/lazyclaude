# LazyClaude Constitution

## Core Principles

### I. Keyboard-First Ergonomics

All functionality MUST be accessible via keyboard without requiring mouse interaction.
The design philosophy prioritizes "keyboard-first" interaction, eliminating reliance on
menu navigation for frequent operations.

**Non-Negotiable Rules**:

- Every user action MUST have a keyboard shortcut
- Single-letter commands for common actions (following lazygit convention)
- Vim-like navigation MUST be supported (`h/j/k/l` alongside arrow keys)
- `<Esc>` MUST always return to parent context or cancel current operation
- `<Enter>` MUST always confirm or drill into selected item
- `/` MUST activate filter/search mode
- `?` MUST display contextual help showing available keybindings

**Rationale**: CLI power users expect keyboard-driven workflows. Mouse-dependent
interfaces break flow and reduce productivity.

### II. Lazygit-Inspired Panel Layout

The application MUST implement a multi-panel layout mirroring lazygit's structure,
with panels for distinct functional areas that users can navigate between.

**Non-Negotiable Rules**:

- Panel layout MUST be clearly divided with visible boundaries
- Focus indicator MUST clearly show which panel is active
- `+` and `_` keys SHOULD cycle between panel expansion modes
- Each panel MUST have contextual keybindings that activate when focused
- Global keybindings (`q` quit, `?` help, `R` refresh) MUST work from any panel
- Panel navigation keys MUST be consistent (Tab or number keys to switch panels)

**Rationale**: Multi-panel layouts enable users to see multiple contexts simultaneously
while maintaining clear separation of concerns.

### III. Contextual Navigation

Navigation MUST be hierarchical and contextual, allowing users to drill down into
items and return to parent views seamlessly.

**Non-Negotiable Rules**:

- `<Enter>` drills into selected items (e.g., selecting a commit shows its files)
- `<Esc>` returns to parent view without side effects
- Breadcrumb or status line MUST indicate current navigation depth
- Range selection MUST be supported via `v` key or shift+arrow combinations
- Filter mode (`/`) MUST narrow visible content without losing context

**Rationale**: Users need to explore data hierarchically while maintaining orientation
within the application structure.

### IV. Modal Minimalism

The interface MUST be primarily non-modal for standard navigation, with modal dialogs
reserved only for complex operations requiring multiple inputs or confirmations.

**Non-Negotiable Rules**:

- Standard navigation and common actions MUST NOT require entering a mode
- Modal dialogs MUST only appear for:
  - Operations with multiple options (e.g., rebase menu)
  - Destructive operations requiring confirmation
  - Multi-field input forms
- Modals MUST be dismissible via `<Esc>`
- Uppercase keys MAY present options (e.g., `d` executes, `D` shows options menu)

**Rationale**: Modal interfaces disrupt workflow. The hybrid approach provides power
for complex operations while maintaining flow for common tasks.

### V. Textual Framework Integration

The application MUST be built using the Textual framework, leveraging its widget system,
CSS-based styling, and testing infrastructure.

**Non-Negotiable Rules**:

- All UI components MUST be Textual widgets or extend from them
- Layout MUST use Textual's CSS system for responsive design
- Custom keybindings MUST integrate with Textual's event system
- Application MUST support the Command Palette (`Ctrl+P`) for discoverability
- Components MUST be de-coupled for testability
- All widgets MUST be testable using Textual's testing framework

**Rationale**: Textual provides a mature foundation for building complex TUIs with
proper testing support. Fighting the framework leads to maintenance burden.

### VI. UV Packaging

The application MUST use uv as the package manager and build tool, with distribution
via uvx for zero-install execution.

**Non-Negotiable Rules**:

- Project MUST use `pyproject.toml` with uv-compatible configuration
- Dependencies MUST be managed via `uv add` / `uv remove`
- Lock file (`uv.lock`) MUST be committed to version control
- Application MUST be installable and runnable via `uvx lazyclaude`
- Package MUST be published to PyPI for uvx discovery
- Development environment MUST use `uv sync` for reproducible setup
- Scripts and entry points MUST be defined in `pyproject.toml` `[project.scripts]`

**Rationale**: UV provides fast, reliable Python package management with built-in
virtual environment handling. UVX enables users to run lazyclaude instantly without
explicit installation, matching the frictionless experience expected from CLI tools.

## UI/UX Constraints

**Visual Design**:

- Panels MUST have visible borders distinguishing them from each other
- Active panel MUST have a distinct border style (e.g., bold or colored)
- Status bar MUST display current mode, keybinding hints, and navigation context
- Color scheme MUST be consistent and support terminal color capabilities
- Text truncation with ellipsis for long content that doesn't fit

**Keybinding Consistency** (following lazygit conventions):

| Key | Action | Scope |
|-----|--------|-------|
| `q` | Quit | Global |
| `?` | Show help | Global |
| `R` | Refresh | Global |
| `/` | Filter/Search | Global |
| `<Enter>` | Confirm/Drill down | Context |
| `<Esc>` | Cancel/Back | Context |
| `j`/`<Down>` | Move down | List |
| `k`/`<Up>` | Move up | List |
| `h`/`<Left>` | Scroll left/Collapse | Context |
| `l`/`<Right>` | Scroll right/Expand | Context |
| `g`/`G` | Go to top/bottom | List |
| `<PgUp>`/`<PgDn>` | Page scroll | List |

**Accessibility**:

- High contrast mode MUST be supported
- Keybindings SHOULD be customizable via configuration file
- Status messages MUST be readable (minimum 2 second display for transient messages)

## Development Workflow

**Code Organization**:

- Single Python package with clear module boundaries
- Widgets in dedicated `widgets/` directory
- Keybinding handlers in `keybindings/` directory
- Business logic separated from UI code in `services/` directory
- CSS styles in dedicated `.css` or `.tcss` files

**Testing Requirements**:

- All widgets MUST have corresponding tests using Textual's test framework
- Keybinding handlers MUST be testable independently of UI
- Integration tests MUST verify panel navigation and focus management
- Snapshot tests recommended for visual regression testing

**Quality Gates**:

- Type hints required for all public functions
- Linting via ruff
- Formatting via ruff format
- Pre-commit hooks enforced
- `uv run pytest` for test execution

