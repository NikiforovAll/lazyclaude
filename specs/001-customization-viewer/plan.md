# Implementation Plan: Claude Code Customization Viewer

**Branch**: `001-customization-viewer` | **Date**: 2025-12-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-customization-viewer/spec.md`

## Summary

Build a lazygit-style TUI application using Textual framework that visualizes Claude Code customizations (Slash Commands, Subagents, Skills, Memory Files, MCPs) with clear separation between user-level (~/.claude/), project-level (.claude/), and project-local (~/.claude.json) configurations. The application provides keyboard-first navigation with vim-like keybindings and a multi-panel layout.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: textual>=0.89.0, rich, pyyaml (for YAML frontmatter parsing)
**Storage**: Filesystem (reads Claude Code configuration files, no persistence)
**Testing**: pytest with pytest-asyncio and pytest-textual-snapshot
**Target Platform**: Cross-platform CLI (Windows, macOS, Linux)
**Project Type**: Single Python package
**Performance Goals**: <1s startup, <100ms filter response, instant keyboard navigation
**Constraints**: Read-only access to config files, no network calls, <50MB memory
**Scale/Scope**: Typical user has <50 customizations, 5 panels, 1 detail pane

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate Question | Status |
|-----------|---------------|--------|
| I. Keyboard-First Ergonomics | Does every feature have keyboard shortcuts? Are vim-like keys supported? | [x] Pass |
| II. Lazygit-Inspired Panel Layout | Does the layout use multi-panel structure with clear focus indicators? | [x] Pass |
| III. Contextual Navigation | Does Enter drill down and Esc go back? Is navigation hierarchical? | [x] Pass |
| IV. Modal Minimalism | Are modals used only for complex/destructive operations? | [x] Pass |
| V. Textual Framework Integration | Are all components Textual widgets? Is CSS-based styling used? | [x] Pass |
| VI. UV Packaging | Is uv used for package management? Is uvx execution supported? | [x] Pass |

**Constitution Compliance Notes**:
- I. ✓ All navigation via j/k/Enter/Esc//, level switching via 1/2/3, vim keys throughout
- II. ✓ Left sidebar with 5 stacked type panels + right detail pane (lazygit layout)
- III. ✓ Enter drills into detail view, Esc returns to list, hierarchical navigation
- IV. ✓ No modals needed - this is a read-only viewer with direct actions
- V. ✓ All widgets extend Textual base classes, CSS for styling
- VI. ✓ pyproject.toml with uv, uvx lazyclaude entry point

**UI/UX Constraints**:
- [x] Panels have visible borders
- [x] Active panel clearly indicated (bold/colored border)
- [x] Status bar shows mode and keybinding hints (Footer widget)
- [x] Keybinding table in constitution followed

## Project Structure

### Documentation (this feature)

```text
specs/001-customization-viewer/
├── plan.md              # This file
├── research.md          # Phase 0: Technology research
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Developer setup guide
├── contracts/           # Phase 1: Internal interfaces
│   └── services.md      # Service layer contracts
└── tasks.md             # Phase 2: Implementation tasks (/speckit.tasks)
```

### Source Code (repository root)

```text
src/lazyclaude/
├── __init__.py
├── __main__.py          # Entry point for `python -m lazyclaude`
├── app.py               # Main Textual App class
├── models/
│   ├── __init__.py
│   ├── customization.py # Customization, ConfigLevel, CustomizationType
│   └── errors.py        # Custom exceptions
├── services/
│   ├── __init__.py
│   ├── discovery.py     # ConfigDiscoveryService - finds all customizations
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── slash_command.py
│   │   ├── subagent.py
│   │   ├── skill.py
│   │   ├── memory_file.py
│   │   └── mcp.py
│   └── filter.py        # FilterService - search/filter logic
├── widgets/
│   ├── __init__.py
│   ├── type_panel.py    # TypePanel - list of customizations by type
│   ├── detail_pane.py   # DetailPane - shows selected customization
│   ├── filter_input.py  # FilterInput - search input widget
│   └── status_bar.py    # StatusBar - mode/keybinding hints
├── keybindings/
│   ├── __init__.py
│   └── handlers.py      # Keybinding action handlers
└── styles/
    └── app.tcss         # Textual CSS styles

tests/
├── conftest.py          # Pytest fixtures
├── unit/
│   ├── test_models.py
│   ├── test_parsers.py
│   └── test_filter.py
├── integration/
│   ├── test_discovery.py
│   └── test_app.py
└── snapshots/           # Visual regression tests
    └── test_layout.py

pyproject.toml           # uv-compatible project config
uv.lock                  # Dependency lock file
```

**Structure Decision**: Single Python package following standard src-layout. The `src/lazyclaude/` structure enables clean imports and proper packaging for PyPI distribution via uvx.

## Complexity Tracking

> No constitution violations. Design follows all principles directly.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
