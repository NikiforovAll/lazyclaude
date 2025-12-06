# Feature Specification: Claude Code Customization Viewer

**Feature Branch**: `001-customization-viewer`
**Created**: 2025-12-06
**Status**: Draft
**Input**: User description: "I want to be able to visualize Claude Code artifacts such as Custom Slash Commands, Subagents, Skills, MCPs; it is very important to separate configurations on different levels: user, project"

## Clarifications

### Session 2025-12-06

- Q: Panel layout structure? → A: Left sidebar with stacked type panels + right detail pane (lazygit style)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View All Customizations at a Glance (Priority: P1)

As a Claude Code user, I want to see all my configured customizations (Slash Commands, Subagents, Skills, MCPs) in a single organized view so I can quickly understand what's available in my current environment.

**Why this priority**: This is the core value proposition - users need visibility into their Claude Code configuration before they can effectively manage it. Without this, users must manually inspect multiple directories and files.

**Independent Test**: Can be fully tested by launching the application and seeing a populated panel with customizations organized by type. Delivers immediate value by providing visibility.

**Acceptance Scenarios**:

1. **Given** a user has Claude Code configured with various customizations, **When** they launch the customization viewer, **Then** they see all customizations organized by type in five panels ordered as: Slash Commands, Subagents, Skills, Memory Files, MCPs.
2. **Given** a user launches the viewer in a folder with .claude/ configuration, **When** the application starts, **Then** it displays project-level customizations by default.
3. **Given** a user launches the viewer in a folder without .claude/ configuration, **When** the application starts, **Then** it displays user-level (~/.claude/) customizations by default.
4. **Given** a user is viewing the customization list, **When** they navigate using keyboard (j/k or arrow keys), **Then** the selection moves between items with clear visual feedback.
5. **Given** customizations exist at both user and project levels, **When** viewing the list, **Then** each customization clearly indicates its configuration level (user vs project).

---

### User Story 2 - Drill Down into Customization Details (Priority: P2)

As a Claude Code user, I want to select a customization and see its full configuration details so I can understand exactly what each customization does and how it's configured.

**Why this priority**: Once users can see customizations, they need to inspect individual configurations. This builds on P1 and enables informed decision-making about customization usage.

**Independent Test**: Can be fully tested by selecting any customization from the list and viewing its complete configuration in a detail panel.

**Acceptance Scenarios**:

1. **Given** a user has selected a customization from the list, **When** they press Enter, **Then** a detail view shows the customization's full configuration (name, description, source file path, content preview).
2. **Given** a user is viewing customization details, **When** they press Esc, **Then** they return to the list view without losing their position.
3. **Given** a customization has a long configuration file, **When** viewing details, **Then** the content is scrollable and truncated appropriately with clear indication of more content.

---

### User Story 3 - Switch Between Configuration Levels (Priority: P2)

As a Claude Code user, I want to toggle between viewing user-level and project-level customizations so I can understand what's global vs local to my current project.

**Why this priority**: The user explicitly emphasized separating user and project configurations. This is critical for understanding customization scope and avoiding confusion.

**Independent Test**: Can be fully tested by switching between user/project/all views and seeing the customization list update accordingly.

**Acceptance Scenarios**:

1. **Given** a user is viewing customizations, **When** they use a keyboard shortcut to switch views (e.g., `1` for all, `2` for user, `3` for project), **Then** the list filters to show only customizations from the selected level.
2. **Given** a user has switched to "project only" view, **When** viewing the list, **Then** only project-level customizations are shown with clear indication of the current filter.
3. **Given** a project has no project-level customizations, **When** switching to "project only" view, **Then** a helpful message indicates no project customizations exist.

---

### User Story 4 - Filter and Search Customizations (Priority: P3)

As a Claude Code user with many customizations, I want to filter and search across all customization types so I can quickly find specific configurations.

**Why this priority**: As customization counts grow, users need efficient discovery. This enhances usability for power users without blocking core functionality.

**Independent Test**: Can be fully tested by entering filter mode with `/`, typing a search term, and seeing filtered results across all customization types.

**Acceptance Scenarios**:

1. **Given** a user is viewing the customization list, **When** they press `/` and type a search term, **Then** only customizations matching the term (in name or description) are displayed.
2. **Given** a user has filtered results, **When** they press Esc, **Then** the filter is cleared and all customizations are visible again.
3. **Given** a search returns no results, **When** viewing the filtered list, **Then** a clear "No matches" message is displayed.

---

### Edge Cases

- What happens when no customizations are configured? Display helpful empty state with guidance on how to add customizations.
- What happens when configuration files are malformed or unreadable? Display error indicator for that customization with ability to see error details.
- What happens when configuration directories don't exist? Gracefully handle missing directories and show appropriate empty state.
- What happens when user lacks read permissions? Display permission error message for affected customizations.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use a lazygit-style layout with a left sidebar containing five stacked type panels (Slash Commands, Subagents, Skills, Memory Files, MCPs) and a right detail pane for content display.
- **FR-002**: System MUST on startup check for project configuration (./.claude/) first; if found, display project-level customizations by default; if not found, display user-level (~/.claude/) customizations by default.
- **FR-003**: System MUST discover and display Custom Slash Commands from both user (~/.claude/commands/) and project (.claude/commands/) levels.
- **FR-004**: System MUST discover and display Subagents from both user and project configuration levels.
- **FR-005**: System MUST discover and display Skills from both user and project configuration levels.
- **FR-006**: System MUST discover and display Memory Files (AGENTS.md, CLAUDE.md) from both user and project levels.
- **FR-007**: System MUST discover and display MCP server configurations from user, project, and project-local (~/.claude.json) configuration levels.
- **FR-008**: System MUST visually distinguish between user-level, project-level, and project-local customizations using clear labeling or iconography.
- **FR-009**: System MUST support keyboard-only navigation following lazygit conventions (j/k, Enter, Esc, /).
- **FR-010**: System MUST display customization metadata including name, description (if available), source file path, and configuration level.
- **FR-011**: System MUST provide real-time filtering of customizations based on user search input.
- **FR-012**: System MUST show a detail view for selected customizations with full configuration content.
- **FR-013**: System MUST indicate current navigation context via status bar or breadcrumbs.

### Key Entities

- **Customization**: Represents a single Claude Code configuration item (Slash Command, Subagent, Skill, Memory File, or MCP). Contains name, type, configuration level, source path, and content.
- **Configuration Level**: Enumeration of where a customization is defined (User, Project, ProjectLocal).
- **Customization Type**: Enumeration of customization categories (SlashCommand, Subagent, Skill, MemoryFile, MCP).
- **Memory File**: Special configuration files (AGENTS.md, CLAUDE.md) that provide context and instructions to Claude Code.

## Assumptions

- Claude Code follows standard configuration paths (~/.claude for user, .claude for project, ~/.claude.json for project-local).
- Slash commands are markdown files in commands/ subdirectories.
- Memory Files are AGENTS.md and CLAUDE.md at user and project levels.
- MCP configurations are stored in Claude Code's settings files at all three configuration levels.
- The application runs in the same environment where Claude Code is configured.
- Users have read access to configuration directories.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view all configured customizations within 2 seconds of launching the application.
- **SC-002**: Users can navigate to any customization using only keyboard controls in under 5 keystrokes from the main view.
- **SC-003**: Search/filter results appear instantly (under 100ms perceived latency) as the user types.
- **SC-004**: Users can distinguish customization configuration level (user vs project) at a glance without drilling into details.
- **SC-005**: 90% of users can successfully find a specific customization on first attempt without consulting documentation.
- **SC-006**: Application startup time is under 1 second for typical customization counts (up to 50 items).
