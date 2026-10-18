---
name: update-deps
description: 'Upgrade a project''s dependencies to their latest versions safely, in any ecosystem (uv, pip, poetry, npm, bun, pnpm, yarn, cargo, go). Researches every major bump through Context7 and web search, applies everything that verifies green as one batch, then brings the user only the decisions that need a human: a short card per update that requires a code change or fails, plus new features the project could use, implemented now or filed as a Linear issue. Use when asked to: update dependencies, upgrade packages, bump a package, refresh the lockfile, fix outdated or stale packages, clear dependabot alerts, what''s new in a library, move to a new major version.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[package ...]"
---

# Update dependencies

The goal is to leave the project on the newest versions of everything, with the test suite green, and with the user having made only the decisions that are genuinely theirs. Every question you ask costs the user attention. A question whose answer is obviously "yes, apply it" is a wasted question; a question they cannot answer without reading a changelog is a badly framed one. Decide everything you can decide with research and a green test run, and bring the user only what is left.

The flow has five phases. Do them in order, because each depends on the state left by the previous one.

1. **Discover** what the project uses and how it verifies itself.
2. **Research and apply**: research every non-trivial bump, apply everything that verifies green.
3. **Decisions**: one short card per update that still needs the user.
4. **New features**: what the upgraded packages now offer that fits this project.
5. **Report**: what changed, what was skipped, what is blocked, then an offer to commit through `sdd-commit`.

With package names as arguments (`/update-deps react zod`), the run covers only those packages; with none, it covers everything.

Per-ecosystem commands live in [references/ecosystems.md](references/ecosystems.md). Read the section for each ecosystem you detect before running anything. Do not run commands from memory for an ecosystem you have not read up on; the flags differ in ways that matter (for example `bun update` alone respects semver ranges and will silently not do what the user asked).

## How to research a package

Your training data is stale for this by definition; the whole point is versions newer than what you know. Never describe a version's changes from memory.

1. **Context7 first.** Call `resolve-library-id` with the package name, then `query-docs` with a focused query: "breaking changes in vX", "migration guide from vX to vY", or "what's new in vY". Context7 has current docs and migration guides for most mainstream libraries and returns them already summarized. Use it for both the breaking-change research and the new-feature research.
2. **Web search when Context7 is thin or unclear.** Smaller packages, very recent releases, and "does vY still support Z" questions are often not in Context7. Use WebSearch for "<package> vY release notes" or "<package> vX to vY breaking changes", then WebFetch the GitHub releases page or `CHANGELOG.md`. The package's repo URL is in its registry metadata (see the reference file).
3. **Read only the span between the current and latest version.** A v3 to v5 jump means the v4 notes too.
4. **Then check the project, not the package.** Grep the codebase for the renamed function, the removed option, the changed import path, the config key. A breaking change the project does not touch is not a breaking change for this project.

Research is cheap next to the user's time. Do it for every major bump and every minor bump on a 0.x package before deciding anything.

## Phase 1: Discover

**Get off the base branch.** Resolve `<base-branch>`: `git config codekit.basebranch`, then `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), then `main`. If `git branch --show-current` equals `<base-branch>`, offer to create `deps/update-<YYYY-MM-DD>` from it before touching anything. `sdd-commit` refuses to commit to the base branch, so the update needs a branch of its own to land.

**Find every manifest.** Look for `pyproject.toml`, `requirements*.txt`, `package.json`, `Cargo.toml`, `go.mod`, and so on, excluding `node_modules`, `.venv`, and build output. A repo often has more than one ecosystem (Python backend plus JS frontend is the common case) and more than one manifest per ecosystem (workspaces, monorepos). Detect the package manager from the lockfile that sits next to the manifest, not from what is installed globally: `uv.lock` means uv, `bun.lock` means bun, `pnpm-lock.yaml` means pnpm.

**Find how the project verifies itself.** The project almost always already has an answer, and using it is far more trustworthy than inventing one. Check, in order: a `Makefile` with `check`, `test`, `lint`, or `typecheck` targets; `package.json` scripts; a pre-commit config; CI workflow files under `.github/workflows`. Compose a single verification command from what you find. If there is genuinely nothing, the fallback is: install, import or build, and run whatever tests exist.

**Read the project's own instructions.** `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, or a README often mention steps that must follow a dependency change: exporting a `requirements.txt`, syncing a vendored copy of shared code into another deploy unit, regenerating a schema. Miss these and the update looks complete but breaks the deploy. Note them now and run them after every install. Also note tool versions pinned outside the manifest, such as a pre-commit hook `rev`, that should move with the package.

**Baseline.** Run the verification command before touching anything. If it already fails, tell the user which failures are pre-existing and carry on; otherwise every later failure gets blamed on the wrong package. Check `git status`; if the tree is dirty, say so and leave those changes alone.

**Check for security alerts.** If `gh` is authenticated and the repo is on GitHub, run:
```bash
gh api "repos/{owner}/{repo}/dependabot/alerts?state=open&per_page=100" \
  --jq '.[] | "\(.number)\t\(.security_vulnerability.package.name)\t\(.security_vulnerability.vulnerable_version_range)\tfixed: \(.security_vulnerability.first_patched_version.identifier // "none")\t\(.security_advisory.severity)"'
```
Otherwise use the ecosystem's audit command (`bun audit`, `npm audit`, `pnpm audit`, `pip-audit`, `cargo audit`, `govulncheck`). Most alerts are on transitive packages the manifests never name, so this is the only way they enter the table. Note each one: package, locked version, first patched version.

**List what is outdated.** Run the outdated-listing command for each ecosystem. These commands show direct dependencies only, which is what you want for classification; transitives are handled by the refresh in Phase 2. Build one table across ecosystems: package, location, current, latest, and a first-pass classification:

- **safe**: patch or minor bump under a stable major (1.x and up). No research needed.
- **research**: a major bump, or a minor bump on a 0.x package. Research decides what happens to these.
- **held**: a pin that looks intentional, such as `typescript: "~5.9.3"` when everything else is `^`, or `==2.1.0`, or a constraint with a comment. Still research it, because the user will want to know what they are holding back from, but never move it without asking.

Do not stop to present this table for approval. Show it as context and keep going.

## Phase 2: Research and apply

**Research every "research" item** using the process above. Each one lands in one of three buckets:

- **Nothing affected.** The project does not touch anything the release changed, and no runtime floor is crossed. This joins the safe batch. It is not a decision for the user; the report will show it with a note like "major, nothing affected" so they can see it happened.
- **Needs a code change.** The project uses something that was renamed, removed, or re-shaped. This becomes a card in Phase 3, with the fix you would make named in the card.
- **Needs something outside the repo.** A newer Node or Python than the machine or CI has, a real deploy to validate against, a peer package that has not caught up, a policy change such as a linter turning on hundreds of new rules. Card.

**Apply the whole batch**, safe items plus "nothing affected" items, in each ecosystem, using the command that also rewrites the constraint in the manifest (not just the lockfile; a lockfile-only upgrade drifts back the next time someone re-resolves).

**Then refresh transitives.** Upgrading by package name holds every other locked version exactly where it was, so a lockfile can carry a vulnerable transitive for months while direct deps look current. Finish the batch with the lockfile-wide refresh that stays inside declared constraints: `uv lock --upgrade`, `bun update` (no `--latest`), `npm update`, `pnpm update`, `cargo update`, `go get -u ./... && go mod tidy`. This is low risk by construction, since nothing crosses a range the manifests already allow, and it is what actually clears most security alerts.

Then install, run the project-specific follow-up steps you noted, bump any pinned tool revisions that mirror a package you moved, and run the verification command once.

**Re-check the security alerts** after the refresh. Any alert whose package is still below the first patched version becomes a card: the patched version is outside a constraint (find which direct dependency pins it and research bumping that), or no patched version exists yet (report it as blocked with the advisory link).

**If verification passes**, the batch is done. Say so in one line.

**If verification fails**, find the culprit rather than reverting the whole batch. Read the error first; it usually names the package. If it does not, bisect: revert half, re-verify, repeat. Once you have it:

1. Try one obvious fix if the failure is clearly a rename, a moved import, a changed config key, or a stricter type. Obvious means you can see the fix in the error or the migration guide in under a minute. Re-verify.
2. If that does not work, revert just that package to its previous version, re-verify to confirm green, and move it to Phase 3 as a card with the exact error.

Never leave the tree red between phases. The user should be able to stop you at any point and have a working project.

In a workspace or monorepo, a package declared in several members must move together, since they share a lockfile. Treat it as one update.

## Phase 3: Decisions

Everything that reaches this phase needs the user for a real reason: it changes their code, changes a policy, needs a machine or deploy you cannot touch, or moves a pin they chose. Present one card per item. Keep it very short. Three lines and a question. Word budget: about fifteen words per line. If you need more, you have not finished distilling; put the detail in an appendix at the bottom of the report and keep the card clean.

```
**<package> <current> → <latest>**
What changed: <the one thing that matters here>
You have: <where the project touches it, e.g. "`.dict()` in 3 files under service/models/">
You need to: <the fix in one clause, and whether you will do it, e.g. "rename to `.model_dump()`, I can do it">
```

Then ask: apply or skip. Use AskUserQuestion when available. Where a card has more than one sensible path (adopt the new lint rules versus pin the old set; step to an intermediate major versus hold), offer those as the options and mark the one you recommend. Several cards can share one AskUserQuestion call, up to its limit, so the user answers in one pass.

For a held pin, "What changed" says what they are holding back from and what you think the reason for the hold is; they know the real reason and may unpin it.

On apply: bump the constraint, install, make the fix you promised, run follow-up steps, verify. If verification fails and one more obvious attempt does not fix it, revert that package, re-verify green, and report it as blocked with the error. Do not spend a long time fighting one package; the user would rather hear about it.

On skip: leave it exactly as it was and record it as skipped in the report.

**Working unattended.** Sometimes there is no one to answer: the user said they are stepping away, the session is non-interactive, or AskUserQuestion is not available. Do not guess. Finish Phase 2, then write every card to the report under "Waiting on you", with the batch applied and verified and the card items untouched. If the user explicitly pre-authorized breaking changes ("apply everything and fix what breaks"), treat every card as approved: apply, fix, verify, and lean on the revert-and-block path whenever a fix is not obvious.

## Phase 4: New features

For each package that moved a meaningful distance (any major bump, or a minor whose release notes have a features or highlights section), look at what was added between the old and new version. Use Context7 with "what's new in vY" or "new features in vY"; you already have the migration notes open for the majors. Fall back to the releases page for packages Context7 does not cover.

Relevance is decided by the project, not by the package. A new router API matters if the project has routes; a new streaming helper matters if the project streams. Grep for the pattern the feature replaces or improves. Skip features the project has no use for; a list of ten irrelevant features trains the user to ignore this section. Three to five well-chosen items is a good report; zero is fine.

Present them compactly:

```
**<package> <version>**: <feature in one sentence>. Fits because <what in this project it would improve, one clause>.
```

Ask, as one multi-select where possible: implement now, file a Linear issue, or skip. Use AskUserQuestion when available.

- **Implement now**: do it, verify, include it in the report.
- **Linear issue**: file it as described below. Keep it to what a developer needs to pick it up cold in two months.
- **Skip**: drop it.

**Filing an issue.** If `git config codekit.linear` is `false`, don't file anything: put the issue text in the report under "Not filed". Otherwise, use the team from `git config codekit.linear-team`. If that's unset, call `list_teams`, ask once which team, and offer to save it with `git config --local codekit.linear-team <team-key>`. Before creating, call `list_issues` with that `team` and the title as `query`; if an open issue with the same title exists, reuse it rather than filing a duplicate. Otherwise call `save_issue` with `team`, `project` (from `git config codekit.linear-project`, if set), `title: "<Package>: <feature name>"`, and `description` from the template below. If the branch name carries a Linear ID (`[A-Za-z][A-Za-z0-9]+-\d+`, uppercased), pass it as `relatedTo`. If Linear fails, warn, put the issue text in the report under "Not filed", and carry on; a failed filing never undoes the update.

Issue description template:

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

When unattended, list the features under "Waiting on you" instead of asking; do not file issues nobody asked for.

## Phase 5: Report

End with one report that stands alone. Someone who did not watch the session should be able to read it and know the state of the tree. Use this shape:

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

Then offer to commit. Never commit without a yes. On yes, read [../sdd-commit/SKILL.md](../sdd-commit/SKILL.md) and follow it. Its template and review step apply here too, and the "Updated" table is the raw material for the message. When unattended, stop at the report.

## Judgment calls worth getting right

**Peer and transitive conflicts.** JS updates often fail at install because a plugin's peer range excludes the new major of its host (eslint plugins are the classic case). Treat the host and its plugins as one unit: research the plugin's compatible version and bump them together, or hold them together.

**Runtime version floors.** A new version may drop support for the project's Python or Node version, or need a newer one than the machine has. Check `requires-python`, `engines`, and the installed runtime before batching; a crossed floor is a card, not a safe update, even if the package manager installs it without complaint.

**Linter and formatter majors.** A new default rule set or formatting change is a policy decision, not a code fix, even when every finding is auto-fixable. Card it with the count of findings and the two paths (adopt versus pin the old configuration).

**Prereleases.** Latest means latest stable. Never move a project onto an alpha, beta, or rc unless the user names it.

**Lockfile-only tools.** When the project uses plain `requirements.txt` with pins and no manifest, the pins are the manifest. Bump them in place and keep the file format (pins stay pins, ranges stay ranges).
