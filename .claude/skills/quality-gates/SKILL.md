---
name: quality-gates
description: This skill should be used when the user wants to run code quality checks (linting, formatting, type checking, tests) on the lazyclaude project. Use this skill when asked to "run quality gates", "check the code", "run tests", "lint the code", or verify code quality before committing.
---

# Quality Gates

Run code quality checks for the lazyclaude project. This skill executes the same checks used in pre-commit hooks plus tests.

## Quality Checks

The following checks are run in order:

| Check | Command | Purpose |
|-------|---------|---------|
| **Ruff Lint** | `uv run ruff check src tests --fix` | Lint code and auto-fix issues |
| **Ruff Format** | `uv run ruff format src tests` | Format code consistently |
| **Mypy** | `uv run mypy src` | Static type checking |
| **Pytest** | `uv run pytest tests/ -q` | Run test suite |

## Usage

To run all quality gates:

```bash
.claude/skills/quality-gates/scripts/check.sh
```

Or run individual checks as needed using the commands above.

## Workflow

1. Run the `.claude/skills/quality-gates/scripts/check.sh` script from the project root
2. Review any failures and fix issues
3. Re-run until all checks pass
4. Preset user with consize summary of results in markdown table format

## Common Issues

- **Ruff lint failures**: Usually auto-fixed. If not, check the error message for manual fixes needed.
- **Mypy errors**: Type annotation issues. Add or fix type hints as indicated.
- **Test failures**: Review test output, fix failing tests or underlying code.
