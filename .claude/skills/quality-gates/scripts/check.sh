#!/usr/bin/env bash
# Quality Gates - Run all code quality checks for lazyclaude
set -e

cd "$(git rev-parse --show-toplevel)"

echo "=== Running Quality Gates ==="
echo ""

echo "[1/4] Ruff Lint (with auto-fix)..."
uv run ruff check src tests --fix
echo "OK"
echo ""

echo "[2/4] Ruff Format..."
uv run ruff format src tests
echo "OK"
echo ""

echo "[3/4] Mypy Type Check..."
uv run mypy src
echo "OK"
echo ""

echo -n "[4/4] Pytest... "
uv run pytest tests/ -q --tb=no --no-header 2>&1 | tail -1
echo ""

echo "=== All Quality Gates Passed ==="
