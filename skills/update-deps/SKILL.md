---
name: update-deps
description: 'Upgrade a project''s dependencies to their latest versions safely, in any ecosystem (uv, pip, poetry, npm, bun, pnpm, yarn, cargo, go). Researches every major bump through Context7 and web search, applies everything that verifies green as one batch, then brings the user only the decisions that need a human: a short card per update that requires a code change or fails, plus new features the project could use, implemented now or filed as a Linear issue. Use when asked to: update dependencies, upgrade packages, bump a package, refresh the lockfile, fix outdated or stale packages, clear dependabot alerts, what''s new in a library, move to a new major version.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[package ...]"
---

# Update dependencies

Leave the project on the newest versions of everything, with its checks green, having asked the user only what's genuinely theirs to decide. Don't ask anything a green run already answers, and frame each question so it can be answered without reading a changelog.

Five phases, in order, since each builds on the last: **Discover**, **Research and apply**, **Decisions**, **New features**, **Report**. With package names as arguments (`/update-deps react zod`), cover only those packages; with none, cover everything.

Per-ecosystem commands are in [references/ecosystems.md](references/ecosystems.md). Read the section for each ecosystem you detect before running anything in it. The flags differ in ways that matter: `bun update` alone respects semver ranges and silently skips majors.

## How to research a package

The versions you're moving to are newer than your training data, so never describe a version's changes from memory.

1. **Context7 first:** `resolve-library-id`, then `query-docs` with a focused query ("breaking changes in vX", "migration guide from vX to vY", "what's new in vY"). Use it for both breaking changes and new features.
2. **Web search when Context7 is thin:** smaller packages, very recent releases, "does vY still support Z". Search for "<package> vY release notes", then fetch the GitHub releases page or `CHANGELOG.md` (the repo URL is in the registry metadata; see the reference file).
3. **Read every version in the span:** v3 → v5 means the v4 notes too.
4. **Then check the project:** grep for the renamed function, removed option, changed import path, or config key. A breaking change the project doesn't touch isn't one for this project.

Do this for every major bump, and every minor bump on a 0.x package, before deciding anything.

## Phase 1: Discover

**Get off the base branch.** Resolve `<base-branch>`: `git config codekit.basebranch`, then `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), then `main`. If you're on it, offer to create `deps/<YYYY-MM-DD>` before touching anything: `git fetch origin <base-branch>`, then `git checkout --no-track -b deps/<YYYY-MM-DD> origin/<base-branch>` (from the local branch if there's no `origin`). `sdd-commit` refuses to commit to the base branch. Keep the name free of anything shaped like a ticket ID: `deps/update-2026-10-22` reads as `UPDATE-2026`.

**Find every manifest** (`pyproject.toml`, `requirements*.txt`, `package.json`, `Cargo.toml`, `go.mod`, …), skipping `node_modules`, `.venv`, and build output. Expect more than one ecosystem, and more than one manifest per ecosystem (workspaces, monorepos). Take the package manager from the lockfile beside each manifest (`uv.lock` → uv, `bun.lock` → bun, `pnpm-lock.yaml` → pnpm), not from what's installed globally.

**Find how the project verifies itself,** and compose one verification command from it. Check, in order: `Makefile` targets (`check`, `test`, `lint`, `typecheck`), `package.json` scripts, the pre-commit config (codekit's is `.config/.pre-commit-config.yaml`, so pass `--config`), and `.github/workflows`. With none of these, install, import or build, and run whatever tests exist.

**Read the project's instructions** (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, the README) for steps that must follow a dependency change, such as exporting a `requirements.txt`, syncing vendored code into another deploy unit, or regenerating a schema. Run them after every install, or the update looks done but breaks the deploy. Also note tool versions pinned outside the manifest, such as a pre-commit hook `rev`, that should move with a package.

**Baseline.** Run the verification command before changing anything, and record any failures as pre-existing, so later ones aren't blamed on the wrong package. If `git status` shows a dirty tree, leave those changes alone and note the files, so Phase 5 keeps them out of the commit.

**Security alerts.** If `gh` is authenticated and the repo is on GitHub, run:
```bash
gh api "repos/{owner}/{repo}/dependabot/alerts?state=open&per_page=100" \
  --jq '.[] | "\(.number)\t\(.security_vulnerability.package.name)\t\(.security_vulnerability.vulnerable_version_range)\tfixed: \(.security_vulnerability.first_patched_version.identifier // "none")\t\(.security_advisory.severity)"'
```
Otherwise, or if GitHub refuses the call (alerts off, or no access), use the ecosystem's audit command (`bun audit`, `npm audit`, `pnpm audit`, `pip-audit`, `cargo audit`, `govulncheck`). Most alerts are on transitive packages no manifest names, so this is how they get on the list. Note each one's package, locked version, and first patched version.

**List what's outdated** with each ecosystem's outdated command. It shows direct dependencies only; Phase 2's refresh handles transitives. Show one table across ecosystems as context, without stopping for approval: package, location, current, latest, and class:

- **safe:** a patch or minor bump under a stable major (1.x and up). No research needed.
- **research:** a major bump, or a minor bump on a 0.x package.
- **held:** a pin that looks intentional, such as `typescript: "~5.9.3"` when everything else is `^`, an `==2.1.0`, or a constraint with a comment. Research it anyway, so the user knows what they're holding back from, but never move it without asking.

## Phase 2: Research and apply

Research each **research** item. It lands in one of three buckets:

- **Nothing affected:** the project touches nothing that changed and crosses no runtime floor. It joins the safe batch, and the report notes "major, nothing affected". It's not a decision for the user.
- **Needs a code change:** something the project uses was renamed, removed, or reshaped. A card in Phase 3, naming the fix.
- **Needs something outside the repo:** a newer runtime than the machine or CI has, a deploy to validate against, a peer package that hasn't caught up, or a policy change such as a linter turning on hundreds of rules. A card.

**Apply the batch** (safe plus nothing affected) with the command that also rewrites the manifest's constraint. A lockfile-only upgrade drifts back the next time someone re-resolves.

**Refresh transitives.** Upgrading by name leaves every other locked version where it was, so a vulnerable transitive can sit in the lockfile for months while direct dependencies look current. Finish with the lockfile-wide refresh inside declared constraints: `uv lock --upgrade`, `bun update` (no `--latest`), `npm update`, `pnpm update`, `cargo update`, `go get -u ./... && go mod tidy`. It crosses no range the manifests don't already allow, and it's what clears most security alerts.

Then install, run the follow-up steps you noted, bump pinned tool revisions that mirror a moved package, and run the verification command once.

**Re-check the security alerts.** An alert still below its first patched version becomes a card: find the direct dependency whose constraint holds it back and research bumping that, or, if no patched release exists, report it as blocked with the advisory link.

**Green:** say so in one line. **Red:** find the culprit instead of reverting the whole batch. The error usually names the package; if it doesn't, bisect (revert half, re-verify, repeat). Then:

1. If the fix is obvious from the error or the migration guide (a rename, a moved import, a changed config key, a stricter type), make it and re-verify.
2. Otherwise revert just that package, confirm green, and make it a card with the exact error.

Never leave the tree red between phases: the user can stop you at any point and have a working project. In a workspace, a package declared in several members shares one lockfile, so it moves as one update.

## Phase 3: Decisions

What reaches this phase needs the user for a real reason: it changes their code or a policy, needs a machine or deploy you can't touch, or moves a pin they chose. One card per item: three lines of about fifteen words each. If it needs more, distill further and put the detail in the report's appendix.

```
**<package> <current> → <latest>**
What changed: <the one thing that matters here>
You have: <where the project touches it, e.g. "`.dict()` in 3 files under service/models/">
You need to: <the fix in one clause, and whether you will do it, e.g. "rename to `.model_dump()`, I can do it">
```

Ask apply or skip with AskUserQuestion, several cards per call so the user answers in one pass. When a card has more than one sensible path (adopt the new lint rules or pin the old set; step to an intermediate major or hold), offer those as the options and mark the one you recommend. For a held pin, "What changed" says what they're holding back from and what you guess the hold is for; they know the real reason.

- **Apply:** bump, install, make the promised fix, run the follow-ups, verify. If it fails and one more obvious attempt doesn't fix it, revert, re-verify green, and report it as blocked with the error. Don't fight one package for long.
- **Skip:** leave it exactly as it was and record it.

**Unattended** (the user said they're stepping away, the session is non-interactive, or AskUserQuestion isn't available): don't guess. Finish Phase 2 and put every card under "Waiting on you" in the report. If the user pre-authorized breaking changes ("apply everything and fix what breaks"), treat every card as approved, and fall back to revert-and-block whenever a fix isn't obvious.

## Phase 4: New features

For each package that moved a meaningful distance (a major, or a minor whose notes have a features section), find what was added: Context7 "what's new in vY", else the releases page. Keep only what fits this project, by grepping for the pattern a feature replaces or improves. Three to five well-chosen items is plenty, and zero is fine; a list of irrelevant features teaches the user to skip this section.

```
**<package> <version>**: <feature in one sentence>. Fits because <what in this project it would improve, one clause>.
```

Ask in one multi-select: **implement now** (do it, verify, and report it), **file a Linear issue** (below), or **skip**. When unattended, list them under "Waiting on you" and file nothing.

**Filing an issue.** If `git config codekit.linear` is `false`, don't file: put the issue text in the report under "Not filed". Otherwise use the team from `git config codekit.linear-team`. If that's unset, call `list_teams`, ask once, and offer to save it with `git config -f .config/.gitconfig codekit.linear-team <team-key>` (`--local` if that file doesn't exist).

1. Call `list_issues` with that `team` and the title as `query`. If an open issue with the same title exists, reuse it.
2. Otherwise call `save_issue` with `team`, `project` (from `git config codekit.linear-project`, if set), `title: "<Package>: <feature name>"`, and `description` from the template below.
3. If the branch name carries a Linear ID (`[A-Za-z][A-Za-z0-9]+-\d+`, uppercased) whose prefix is the team key, or that `get_issue` finds, pass it as `relatedTo`. Version numbers match the same pattern, and a `relatedTo` that doesn't exist fails the whole filing.

If Linear fails, warn, put the issue text under "Not filed", and carry on: a failed filing never undoes the update. Write the issue so a developer can pick it up cold in two months:

```markdown
**Package:** <name> <version it arrived in>
**Found:** <YYYY-MM-DD> during a dependency update

## What it is
<Two or three sentences. Link to the release note or docs page.>

## Why it fits this project
<What the project does today that this would improve or replace. Name the files or modules.>

## Rough steps
1. <step>
2. <step>

## Notes
<Gotchas, prerequisites, anything you noticed while researching.>
```

## Phase 5: Report

End with one report that stands alone: someone who didn't watch the session should know the state of the tree.

```markdown
## Dependency update: <date>

### Updated (verified green)
| Package | Location | From | To | Notes |
<"major, nothing affected" or "0.x minor, nothing affected" in Notes where that was the reason it was batched>

### Skipped by you
| Package | From | Latest | Reason given |

### Blocked
| Package | From | Latest | Error |

### Linear issues
- <ID>: <title>, filed or reused
<"Not filed" entries with the full issue text, if Linear failed>

### Waiting on you   <!-- only when unattended -->
<the cards and feature list>

### Security alerts
| Alert | Package | Was | Now | Status |
<resolved / still open with reason>

### Follow-ups run
<e.g. "make sync-agents", "bumped pre-commit ruff rev to match", "transitive refresh: 96 packages moved">

### Appendix   <!-- optional -->
<research detail that did not fit in a card>
```

Then offer to commit, and never commit without a yes. On a yes, read [../sdd-commit/SKILL.md](../sdd-commit/SKILL.md) and follow it; its template and review step apply here too, and the "Updated" table is the raw material for the message. Tell it to leave out the files that were dirty at baseline. When unattended, stop at the report.

## Judgment calls

- **Peer conflicts.** JS installs often fail because a plugin's peer range excludes its host's new major (eslint plugins are the classic case). Treat the host and its plugins as one unit: bump them together to compatible versions, or hold them together.
- **Runtime floors.** Check `requires-python`, `engines`, and the installed runtime before batching. A new version that drops the project's runtime, or needs a newer one than the machine has, is a card, even if the package manager installs it without complaint.
- **Linter and formatter majors.** A new default rule set or formatting change is a policy decision, even when every finding is auto-fixable. Card it with the count of findings and the two paths: adopt, or pin the old configuration.
- **Prereleases.** Latest means latest stable. Never move to an alpha, beta, or rc unless the user names it.
- **Pins as the manifest.** With a plain pinned `requirements.txt` and no other manifest, bump the pins in place and keep the file's format: pins stay pins, ranges stay ranges.
