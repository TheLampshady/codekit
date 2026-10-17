# Antigravity Rules

Markdown rules loaded by [Antigravity](https://antigravity.google/docs/rules-workflows) as part of the codekit plugin.

| Rule | Activation | Covers |
|------|-----------|--------|
| [destructive-operations.md](destructive-operations.md) | Always On | Confirm `rm -rf`, force-pushes, hard resets, reassigning Linear issues, closing PRs |
| [secrets.md](secrets.md) | Always On | Don't read or write credential files; read keys, not values |

Rules are **guidance the model may follow**, not enforcement. Each file must stay under Antigravity's 12,000-character limit. For hard limits, use Antigravity's own permission prompts.

Claude Code doesn't load this directory. On Claude, the same guardrails come from the skills themselves (each one confirms before pushing or reassigning) and from the user's permission settings.
