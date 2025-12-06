# Tasks: Claude Code Customization Viewer

**Input**: Design documents from `/specs/001-customization-viewer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/services.md

**Tests**: Not explicitly requested in spec. Tests can be added in Polish phase if needed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- Source: `src/lazyclaude/`
- Tests: `tests/`
- Styles: `src/lazyclaude/styles/`

---

## Phase 1: Setup (Project Infrastructure)

**Purpose**: Initialize Python project with uv, Textual, and required dependencies

- [x] T001 Create pyproject.toml with uv-compatible config, textual>=0.89.0, rich, pyyaml dependencies in pyproject.toml
- [x] T002 Create src/lazyclaude/__init__.py with package version and exports
- [x] T003 [P] Create src/lazyclaude/__main__.py entry point for `python -m lazyclaude`
- [x] T004 [P] Configure ruff linting/formatting in pyproject.toml
- [x] T005 Run `uv sync` to generate uv.lock and verify installation

**Checkpoint**: Project initializes with `uv run python -m lazyclaude`

---

## Phase 2: Foundational (Core Models & Parsers)

**Purpose**: Core data models and parsers that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create ConfigLevel enum in src/lazyclaude/models/customization.py
- [x] T007 [P] Create CustomizationType enum in src/lazyclaude/models/customization.py
- [x] T008 Create Customization dataclass with all fields in src/lazyclaude/models/customization.py
- [x] T009 [P] Create SlashCommandMetadata dataclass in src/lazyclaude/models/customization.py
- [x] T010 [P] Create SubagentMetadata dataclass in src/lazyclaude/models/customization.py
- [x] T011 [P] Create SkillMetadata dataclass in src/lazyclaude/models/customization.py
- [x] T012 [P] Create MCPServerMetadata dataclass in src/lazyclaude/models/customization.py
- [x] T013 Create src/lazyclaude/models/__init__.py with all model exports
- [x] T014 Create ICustomizationParser base interface in src/lazyclaude/services/parsers/__init__.py
- [x] T015 Implement frontmatter parsing utility in src/lazyclaude/services/parsers/__init__.py
- [x] T016 [P] Implement SlashCommandParser in src/lazyclaude/services/parsers/slash_command.py
- [x] T017 [P] Implement SubagentParser in src/lazyclaude/services/parsers/subagent.py
- [x] T018 [P] Implement SkillParser in src/lazyclaude/services/parsers/skill.py
- [x] T019 [P] Implement MemoryFileParser in src/lazyclaude/services/parsers/memory_file.py
- [x] T020 [P] Implement MCPParser in src/lazyclaude/services/parsers/mcp.py
- [x] T021 Implement IConfigDiscoveryService interface in src/lazyclaude/services/discovery.py
- [x] T022 Implement ConfigDiscoveryService with all parsers in src/lazyclaude/services/discovery.py
- [x] T023 Create src/lazyclaude/services/__init__.py with service exports

**Checkpoint**: Foundation ready - `ConfigDiscoveryService().discover_all()` returns customizations

---

## Phase 3: User Story 1 - View All Customizations at a Glance (Priority: P1) 🎯 MVP

**Goal**: Users see all customizations organized by type in 5 panels on app launch

**Independent Test**: Launch app with test config directory, verify 5 panels with items visible, keyboard navigation works

### Implementation for User Story 1

- [x] T024 [P] [US1] Create base TypePanel widget in src/lazyclaude/widgets/type_panel.py
- [x] T025 [P] [US1] Create base DetailPane widget (empty state) in src/lazyclaude/widgets/detail_pane.py
- [x] T026 [US1] Create main LazyClaude App class with compose() in src/lazyclaude/app.py
- [x] T027 [US1] Implement 5-panel layout (Slash Commands, Subagents, Skills, Memory Files, MCPs) in src/lazyclaude/app.py
- [x] T028 [US1] Create app.tcss with lazygit-style panel layout in src/lazyclaude/styles/app.tcss
- [x] T029 [US1] Implement startup config detection (.claude/ vs ~/.claude/) in src/lazyclaude/app.py
- [x] T030 [US1] Add j/k navigation bindings to TypePanel in src/lazyclaude/widgets/type_panel.py
- [x] T031 [US1] Add Tab panel switching bindings in src/lazyclaude/app.py
- [x] T032 [US1] Add visual level indicators [U]/[P]/[L] to TypePanel items in src/lazyclaude/widgets/type_panel.py
- [x] T033 [US1] Implement panel header with item count in src/lazyclaude/widgets/type_panel.py
- [x] T034 [US1] Add Footer widget with keybinding hints in src/lazyclaude/app.py
- [x] T035 [US1] Add global q (quit), ? (help), R (refresh) bindings in src/lazyclaude/app.py
- [x] T036 [US1] Implement empty state message for panels with no items in src/lazyclaude/widgets/type_panel.py
- [x] T037 [US1] Add error indicator for malformed customizations in src/lazyclaude/widgets/type_panel.py
- [x] T038 [US1] Style active panel border (bold/colored) in src/lazyclaude/styles/app.tcss

**Checkpoint**: User Story 1 complete - app launches with all customizations visible, keyboard navigation works

---

## Phase 4: User Story 2 - Drill Down into Customization Details (Priority: P2)

**Goal**: Users can select a customization and see full details in the right pane

**Independent Test**: Select any item with Enter, verify detail pane shows name/description/path/content, Esc returns to list

### Implementation for User Story 2

- [x] T039 [US2] Implement SelectionChanged message in src/lazyclaude/widgets/type_panel.py
- [x] T040 [US2] Implement DrillDown message on Enter key in src/lazyclaude/widgets/type_panel.py
- [x] T041 [US2] Wire SelectionChanged to update DetailPane preview in src/lazyclaude/app.py
- [x] T042 [US2] Implement full detail view in DetailPane in src/lazyclaude/widgets/detail_pane.py
- [x] T043 [US2] Add metadata display (level, path, description) to DetailPane in src/lazyclaude/widgets/detail_pane.py
- [x] T044 [US2] Add content preview with syntax highlighting to DetailPane in src/lazyclaude/widgets/detail_pane.py
- [x] T045 [US2] Implement content scrolling (j/k/g/G) in DetailPane in src/lazyclaude/widgets/detail_pane.py
- [x] T046 [US2] Implement Esc to return focus to TypePanel in src/lazyclaude/app.py
- [x] T047 [US2] Show error details when customization has error in src/lazyclaude/widgets/detail_pane.py
- [x] T048 [US2] Add truncation indicator for long content in src/lazyclaude/widgets/detail_pane.py

**Checkpoint**: User Story 2 complete - drill-down works, details visible, Esc returns to list

---

## Phase 5: User Story 3 - Switch Between Configuration Levels (Priority: P2)

**Goal**: Users can toggle between All/User/Project views using 1/2/3 keys

**Independent Test**: Press 1/2/3, verify panel lists filter by level, status bar shows current filter

### Implementation for User Story 3

- [x] T049 [US3] Implement IFilterService interface in src/lazyclaude/services/filter.py
- [x] T050 [US3] Implement FilterService with level filtering in src/lazyclaude/services/filter.py
- [x] T051 [US3] Add LevelFilterChanged message in src/lazyclaude/app.py
- [x] T052 [US3] Add 1 (All), 2 (User), 3 (Project) keybindings in src/lazyclaude/app.py
- [x] T053 [US3] Wire level filter to update all TypePanels in src/lazyclaude/app.py
- [x] T054 [US3] Update status bar to show current level filter in src/lazyclaude/app.py
- [x] T055 [US3] Show "No items at this level" message when filtered list empty in src/lazyclaude/widgets/type_panel.py

**Checkpoint**: User Story 3 complete - level switching works, filter state visible in status bar

---

## Phase 6: User Story 4 - Filter and Search Customizations (Priority: P3)

**Goal**: Users can press / to enter filter mode and search across all types

**Independent Test**: Press /, type search term, verify results filter in real-time, Esc clears filter

### Implementation for User Story 4

- [x] T056 [P] [US4] Create FilterInput widget in src/lazyclaude/widgets/filter_input.py
- [x] T057 [US4] Extend FilterService with text search in src/lazyclaude/services/filter.py
- [x] T058 [US4] Add SearchFilterChanged message in src/lazyclaude/app.py
- [x] T059 [US4] Add / keybinding to activate filter mode in src/lazyclaude/app.py
- [x] T060 [US4] Wire FilterInput to FilterService in src/lazyclaude/app.py
- [x] T061 [US4] Implement real-time filtering as user types in src/lazyclaude/app.py
- [x] T062 [US4] Implement Esc to clear filter and hide FilterInput in src/lazyclaude/app.py
- [x] T063 [US4] Show "No matches" message when search returns empty in src/lazyclaude/widgets/type_panel.py
- [x] T064 [US4] Update status bar to show active search query in src/lazyclaude/app.py
- [x] T065 [US4] Style FilterInput widget in src/lazyclaude/styles/app.tcss

**Checkpoint**: User Story 4 complete - search works, real-time filtering, Esc clears

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T066 Implement create_app() factory function in src/lazyclaude/app.py
- [x] T067 Add CLI argument parsing for target directory in src/lazyclaude/__main__.py
- [x] T068 Add --version flag support in src/lazyclaude/__main__.py
- [x] T069 Implement help overlay triggered by ? key in src/lazyclaude/app.py
- [x] T070 Add g/G keybindings for go to top/bottom in TypePanel in src/lazyclaude/widgets/type_panel.py
- [x] T071 Verify all keybindings match constitution table in src/lazyclaude/app.py
- [x] T072 Run quickstart.md validation (uv sync, uv run lazyclaude)
- [x] T073 Performance check: verify <1s startup, <100ms filter response

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1): Required before US2 (needs panels)
  - US2 (P2): Can start after US1 (needs selection)
  - US3 (P2): Can start after US1 (only needs panels)
  - US4 (P3): Can start after US1 (only needs panels and filter service)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 2 (Foundational)
        │
        ▼
Phase 3 (US1: View All) ─────┬───────────────┐
        │                    │               │
        ▼                    ▼               ▼
Phase 4 (US2: Details)  Phase 5 (US3)  Phase 6 (US4)
        │                    │               │
        └────────────────────┴───────────────┘
                             │
                             ▼
                    Phase 7 (Polish)
```

### Within Each User Story

- Models before services (already in Foundational)
- Widgets before app integration
- Core functionality before edge cases
- Bindings after widgets exist

### Parallel Opportunities

**Phase 1** (all [P] tasks):
- T003, T004 can run in parallel

**Phase 2** (all [P] tasks):
- T006, T007 can run in parallel (enums)
- T009, T010, T011, T012 can run in parallel (metadata classes)
- T016, T017, T018, T019, T020 can run in parallel (parsers)

**Phase 3** (US1):
- T024, T025 can run in parallel (base widgets)

**Phase 6** (US4):
- T056 can run parallel with T057

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all enum definitions together:
Task: "T006 Create ConfigLevel enum in src/lazyclaude/models/customization.py"
Task: "T007 Create CustomizationType enum in src/lazyclaude/models/customization.py"

# Launch all metadata classes together:
Task: "T009 Create SlashCommandMetadata dataclass in src/lazyclaude/models/customization.py"
Task: "T010 Create SubagentMetadata dataclass in src/lazyclaude/models/customization.py"
Task: "T011 Create SkillMetadata dataclass in src/lazyclaude/models/customization.py"
Task: "T012 Create MCPServerMetadata dataclass in src/lazyclaude/models/customization.py"

# Launch all parsers together:
Task: "T016 Implement SlashCommandParser in src/lazyclaude/services/parsers/slash_command.py"
Task: "T017 Implement SubagentParser in src/lazyclaude/services/parsers/subagent.py"
Task: "T018 Implement SkillParser in src/lazyclaude/services/parsers/skill.py"
Task: "T019 Implement MemoryFileParser in src/lazyclaude/services/parsers/memory_file.py"
Task: "T020 Implement MCPParser in src/lazyclaude/services/parsers/mcp.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Launch app, verify all 5 panels visible with items
5. Deploy/demo if ready - this is a functional MVP!

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP Complete**
3. Add User Story 2 → Test independently → Drill-down works
4. Add User Story 3 → Test independently → Level filtering works
5. Add User Story 4 → Test independently → Search works
6. Polish phase → Full feature complete

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

This delivers:
- All 5 panels with customizations
- Keyboard navigation (j/k, Tab)
- Level indicators on items
- Basic status bar

Excludes (for later):
- Detail drill-down (US2)
- Level filtering (US3)
- Search (US4)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after US1 foundation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Spec does not request tests - add in Polish phase if needed

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 73 |
| **Phase 1 (Setup)** | 5 tasks |
| **Phase 2 (Foundational)** | 18 tasks |
| **User Story 1 (P1)** | 15 tasks |
| **User Story 2 (P2)** | 10 tasks |
| **User Story 3 (P2)** | 7 tasks |
| **User Story 4 (P3)** | 10 tasks |
| **Polish** | 8 tasks |
| **Parallel Opportunities** | 17 tasks marked [P] |
| **MVP Scope** | Setup + Foundational + US1 (38 tasks) |
