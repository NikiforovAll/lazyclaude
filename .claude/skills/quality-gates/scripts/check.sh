#!/usr/bin/env bash
# Quality Gates - Run code quality checks for lazyclaude
# Usage: check.sh [--lint] [--format] [--mypy] [--test] [--all]
#   --lint    Run ruff lint
#   --format  Run ruff format
#   --mypy    Run mypy type check
#   --test    Run pytest
#   --all     Run all checks (default if no flags)
set -e

cd "$(git rev-parse --show-toplevel)"

RUN_LINT=false
RUN_FORMAT=false
RUN_MYPY=false
RUN_TEST=false

# Parse arguments
if [[ $# -eq 0 ]]; then
  # No args = run all checks
  RUN_LINT=true
  RUN_FORMAT=true
  RUN_MYPY=true
  RUN_TEST=true
fi

for arg in "$@"; do
  case $arg in
    --lint)   RUN_LINT=true ;;
    --format) RUN_FORMAT=true ;;
    --mypy)   RUN_MYPY=true ;;
    --test)   RUN_TEST=true ;;
    --all)
      RUN_LINT=true
      RUN_FORMAT=true
      RUN_MYPY=true
      RUN_TEST=true
      ;;
  esac
done

echo "=== Running Quality Gates ==="
echo ""

step=1

if $RUN_LINT; then
  echo "[$step] Ruff Lint (with auto-fix)..."
  uv run ruff check src tests --fix
  echo "OK"
  echo ""
  ((step++))
fi

if $RUN_FORMAT; then
  echo "[$step] Ruff Format..."
  uv run ruff format src tests
  echo "OK"
  echo ""
  ((step++))
fi

if $RUN_MYPY; then
  echo "[$step] Mypy Type Check..."
  uv run mypy src
  echo "OK"
  echo ""
  ((step++))
fi

if $RUN_TEST; then
  echo -n "[$step] Pytest... "
  uv run pytest tests/ -q --tb=no --no-header 2>&1 | tail -1
  pytest_status=${PIPESTATUS[0]}
  echo ""
  if [[ $pytest_status -ne 0 ]]; then
    exit "$pytest_status"
  fi
fi

echo "=== All Quality Gates Passed ==="
