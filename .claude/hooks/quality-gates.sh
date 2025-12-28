#!/bin/bash
# Hook: Run quality gates after Claude finishes responding
# Triggered by: Stop hook event
# Exit 2 + stderr = blocks stop, shows output to Claude
# Filters checks based on changed file types

# Read input from stdin
input=$(cat)

# Check if stop hook is already active (prevent infinite loops)
if echo "$input" | grep -q '"stop_hook_active":true'; then
  exit 0
fi

# Check for changed Python files (staged or unstaged)
python_changed=$(git diff --name-only HEAD 2>/dev/null | grep -E '\.py$' || true)
python_staged=$(git diff --cached --name-only 2>/dev/null | grep -E '\.py$' || true)

if [ -z "$python_changed" ] && [ -z "$python_staged" ]; then
  # No Python files changed, skip quality gates
  exit 0
fi

# Run the quality gates script with passed arguments
if [ -f ".claude/skills/quality-gates/scripts/check.sh" ]; then
  output=$(bash ".claude/skills/quality-gates/scripts/check.sh" "$@" 2>&1)
  exit_code=$?

  if [ $exit_code -eq 0 ]; then
    # Silent on success
    exit 0
  else
    # Pass the full output back to Claude via stderr
    echo "Quality gates failed. Please fix the issues:" >&2
    echo "" >&2
    echo "$output" >&2
    exit 2
  fi
fi

exit 0
