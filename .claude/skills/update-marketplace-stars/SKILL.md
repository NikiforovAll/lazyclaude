---
name: update-marketplace-stars
description: Update GitHub star counts for suggested marketplaces in DEFAULT_SUGGESTED_MARKETPLACES. Use this skill when asked to "update stars", "refresh marketplace stars", or "sync star counts".
---

# Update Marketplace Stars

Update the GitHub star counts for suggested marketplaces defined in `src/lazyclaude/services/settings.py`.

## Location

The star counts are defined in:

```
src/lazyclaude/services/settings.py
```

Look for the `DEFAULT_SUGGESTED_MARKETPLACES` dictionary near the top of the file.

## Fetch Current Stars

Use GitHub CLI to fetch current star counts for each repository:

```bash
gh api repos/{owner}/{repo} --jq '.stargazers_count'
```

Example for all current marketplaces:

```bash
gh api repos/anthropics/claude-plugins-official --jq '.stargazers_count'
gh api repos/NikiforovAll/claude-code-rules --jq '.stargazers_count'
gh api repos/SawyerHood/dev-browser --jq '.stargazers_count'
gh api repos/Piebald-AI/claude-code-lsps --jq '.stargazers_count'
gh api repos/wshobson/agents --jq '.stargazers_count'
gh api repos/davila7/claude-code-templates --jq '.stargazers_count'
gh api repos/ComposioHQ/awesome-claude-skills --jq '.stargazers_count'
gh api repos/steveyegge/beads --jq '.stargazers_count'
gh api repos/ccplugins/awesome-claude-code-plugins --jq '.stargazers_count'
```

## Workflow

1. Read `src/lazyclaude/services/settings.py` to get current marketplace repos
2. Run `gh api` commands in parallel to fetch star counts
3. Update the `stars` values in `DEFAULT_SUGGESTED_MARKETPLACES`
4. Present summary of changes (old vs new star counts)

## Notes

- Star counts are approximate and change frequently
- Run this periodically before releases to keep counts fresh
- If a repo is not found (404), keep the existing value and notify user
