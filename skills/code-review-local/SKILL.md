---
name: code-review-local
description: 'Review the current branch''s changes against the base branch before opening a PR. Checks the diff against the SpecKit/OpenSpec spec or the hand-written plan for completeness, plus correctness, security, and the project''s conventions, then saves a report with blockers and suggestions. Use when asked to: review my code, review my changes, check my work, self-review, local review, is this ready for a PR.'
user-invocable: true
disable-model-invocation: true
context: fork
agent: general-purpose
background: false
argument-hint: "[base-branch]"
---

# Code Review Local

A senior-engineer pass over the branch before anyone else sees it. Reviews are read-only: this skill reports and never edits code.

In Claude Code, `/code-review-local` runs as an isolated subagent that hasn't seen the conversation, so it judges the diff against the spec and the ticket, not against what was discussed while building it. Everything it needs comes from git and the spec files. It never stops to ask: anything it would ask about goes in the report.

## Workflow

### 1. Scope

1. **Base branch:** use the one passed as an argument (`$ARGUMENTS`) or named by the caller, else `git config codekit.basebranch`, else `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), else `main`.
2. `git fetch origin <base-branch>`. If the fetch fails (offline), compare against the local ref and say so.
3. Gather the diff:
   - Committed: `git diff origin/<base-branch>...HEAD`
   - Uncommitted: `git diff HEAD`
   - Untracked: `git ls-files --others --exclude-standard`. Read these files in full.
4. If the diff is empty, say so and stop.

### 2. Load intent

Find what the change is *supposed* to do, using the first source that exists:

1. **SpecKit:** `spec.md`, `plan.md`, `tasks.md` in the feature directory named by `.specify/feature.json`
2. **OpenSpec:** `openspec/changes/<change-id>/` (proposal, design, tasks, spec deltas)
3. **Manual:** `specs/<ticket>/ticket.md` and `plan.md`

Then load the conventions: `docs/FOUNDATIONS.md`, `docs/PRINCIPLES.md`, `CONTRIBUTING.md`, and `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`.

If there's no spec, do a general quality review and say so in the report.

### 3. Review

Read each changed file in full where the diff alone lacks context. Check:

- **Completeness:** every requirement and task in the spec is implemented. Name the missing ones.
- **Correctness:** logic errors, unhandled edge cases, error paths, concurrency, off-by-ones.
- **Security:** committed secrets, injection, unsafe deserialization, missing authorization checks, logging sensitive data.
- **Tests:** new behavior has tests, and the tests assert the behavior rather than the implementation.
- **Conventions:** the change matches the documented foundations and the surrounding code. Flag where it reinvents something a foundation already provides.
- **Scope:** unrelated changes, debug leftovers, commented-out code.

Severity:
- **Blocker:** wrong behavior, a security issue, a missing required piece, or a broken build or test.
- **Suggestion:** would make the code better, but merging without it is fine.

Each finding needs a `file:line`, what's wrong, and a concrete fix. Don't pad: an empty section is fine.

### 4. Report

Write the report to `${TMPDIR:-/tmp}/codekit/<repo>/reviews/<branch-name-with-slashes-as-dashes>.md`, where `<repo>` is the name of the repo's top-level folder, creating the directory if needed. It's the system temp folder, so nothing lands in the repo and the OS clears old reports eventually. Give the full path in your reply so the caller can find it.

```markdown
# Local review: <branch>

**Base:** <base-branch> · **Commit:** <short-sha> · **Ticket:** <ticket-id or none> · **Spec:** <path or none>

## Summary
<what the change does, in 2-3 sentences>

## Completeness
<requirement → done / missing / partial>

## Blockers
- `path:line`: <problem>. **Fix:** <fix>

## Suggestions
- `path:line`: <problem>. **Fix:** <fix>
```

### 5. Present

Print the report and its path. End with one line: **Ready for PR** if there are no blockers, otherwise **N blocker(s) to fix first**.
