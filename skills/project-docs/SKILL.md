---
name: project-docs
description: 'Keep the app''s project docs current for people who don''t read the code: a Product Map (what the app does and what its data and interfaces support, in product language, each entry linked to code), a Decision Log (what was decided and why, from each shipped spec), and a Glossary. They live in the app''s Linear project, or in docs/project/ when the repo doesn''t use Linear. Updates only what changed since the last sync; the first build also logs the decisions in specs already merged. Runs after each merge from the codekit-docs Action, or inside sdd-push without Linear. Use when asked to: update the project docs, build or rebuild the product map, update the decision log, add to the glossary, refresh the docs for PMs, the project docs are behind.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[--full] [--ci] [--git-dir <path>]"
---

# Project docs

Keeps the app's project docs current for people who don't read the code:

- **Product Map**: what the app does today, in product language, including what its data and interfaces support (the basis for effort questions). It's generated, so this skill rewrites it and hand edits don't survive.
- **Decision Log**: what was decided and why, one entry per shipped ticket or spec. It's a reference for people looking up why something was built a certain way. Nothing in codekit feeds it to an agent: it's AI-extracted and grows with every ticket, so as planning context it would be bloated and sometimes wrong. Each entry links its source.
- **Glossary**: the shared vocabulary. It belongs to the team, so people edit it directly, and this skill only appends terms to it.

Each has a template in [resources/](resources/), relative to this `SKILL.md`. The plugin root (`<plugin>`) is two folders up.

## Where they live

`git config codekit.linear` picks the mode:

| | **Linear** (anything but `false`) | **Repo** (`false`) |
|--|--|--|
| Where | Documents in the app's Linear project, where PMs read them, ask Linear Agent about them, and file tickets | `docs/project/product-map.md`, `decision-log.md`, and `glossary.md` |
| Updated by | The `codekit-docs` Action after every merge, with `--ci` | `sdd-push`, inside each PR. A pre-push hook warns when commits pushed another way leave them behind. |
| Decisions from | The spec documents on each ticket's Linear issue | The spec folders committed with the code |
| Publish | Through the Linear API, after showing the changes and asking (unless `--ci`) | Write the files. The diff is the review, and they're committed with the code. |

Run it by hand for the first build (`/codekit init` offers it), or to check a change before it merges.

## Flags

| Flag | Effect |
|------|--------|
| `--ci` | Non-interactive. Never ask; take the default at every decision, and put anything a person should look at in the summary. The Action passes this. |
| `--git-dir <path>` | Read the git input that [scripts/collect_git.sh](scripts/collect_git.sh) collected into `<path>` (`<tmp>/git`) and run no git command. The Action passes it, because its allowlist has no `git`. See [Git input](#git-input). |
| `--full` | Rebuild the map from the whole codebase instead of updating it from the commits since the last sync. |

## Working folder

Run every command from the repo root and never `cd` or use `git -C`: in the Action, the allowlist matches commands as written, and a moved shell stops every later command. Reach `<tmp>` (Step 2) by absolute path.

## Git input

With `--git-dir <path>`, a script has already run git for you: `<plugin>/skills/project-docs/scripts/collect_git.sh [--full]`, which also puts the current docs in `<tmp>/docs/`. Read these files instead of running git, in Steps 1 to 5. If one is missing, end with `CODEKIT-RESULT: blocked git input missing`.

| File | Replaces |
|------|----------|
| `repo.txt` | `git rev-parse --show-toplevel`, the base branch (`base=`), `HEAD` (`head=`), and `git config codekit.linear-project` (`linear-project=`) |
| `mode.txt` | `git config codekit.linear` (`mode=`), Step 3's full or incremental choice (`run=`, with `since=`), and `<sync>` |
| `log.txt`, `messages.txt` | `git log` over the commits to cover, as a list and in full (ticket IDs come from `messages.txt`) |
| `diffstat.txt`, `diff.patch` | `git diff` and `git show` over those commits |
| `specs.txt` | the spec folders those commits added or changed (repo mode) |
| `backfill/`, `backfill.txt` | `git ls-tree` and `git show <rev>:<path>` for [backfill](#backfill): the merged spec folders, and each one's date and short rev |

The script reads settings from `.config/.gitconfig` when git config lacks them, so a fresh checkout works. The commits are already filtered as Step 3 describes, so use them as given.

## 1. Prerequisites

- **Git repo:** `git rev-parse --show-toplevel`.
- **Base branch (`<base-branch>`):** `git config codekit.basebranch`, else `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), else `main`.

With `--git-dir`, both come from `repo.txt`.

Linear mode also needs these. If either fails, stop and say why.

- **Linear API key:** `python3 <plugin>/skills/linear-docs/scripts/linear_docs.py --check`. With `--ci`, run it as written: the job passes the key in its environment, and the Action allows only commands that start with `python3`. Locally, run it the way [linear-docs](../linear-docs/SKILL.md) runs its script, so the profile's `LINEAR_API_KEY` is found: directly when the key is in the environment, else through `"$SHELL" -lic '…' </dev/null`. Run every `python3` command below the same way.
- **Project:** `git config codekit.linear-project` (with `--git-dir`, `linear-project=` in `repo.txt`). If it's missing, suggest `/codekit update`.

**Script (Linear mode):** `<plugin>/skills/linear-docs/scripts/project_docs.py` (`<script>` below), called by absolute path from the project root. It moves documents between Linear and disk without sending them through the model. Never read or write project docs with the Linear MCP: they're long, and every byte would go through the model.

## 2. Get the current docs

With `--git-dir`, the script already did this: read the docs in `<tmp>/docs/` and go to Step 3. Otherwise, work in the system temp folder, `${TMPDIR:-/tmp}/codekit/<repo>`, where `<repo>` is the name of the repo's top-level folder (`<tmp>` below). The OS clears it eventually. Locally, empty `<tmp>/docs/` first if an earlier run left it, so a doc that's gone isn't mistaken for current.

- **Linear:**
  ```bash
  python3 <script> pull --title "Product Map" --out <tmp>/docs/product-map.md
  python3 <script> pull --title "Glossary" --out <tmp>/docs/glossary.md
  python3 <script> pull --title "Decision Log" --out <tmp>/docs/decision-log.md
  ```
- **Repo:** copy whichever of `docs/project/product-map.md`, `glossary.md`, and `decision-log.md` exist to `<tmp>/docs/`.

A doc that doesn't exist yet is fine: its step starts it from the template.

## 3. Pick full or incremental

With `--git-dir`, `mode.txt` holds the result (`run=`, `since=`, `sync=`) and the commits are in `log.txt`: skip to the last paragraph. Otherwise, read the sync line at the bottom of the current map: `Synced to commit <sha> on <date>.` Rebuild in **full** if any of these is true:
- `--full` was passed
- there's no map yet, or no sync line
- the commit isn't in this history (`git merge-base --is-ancestor <sha> HEAD` fails, e.g. after a force-push)

Otherwise update **incrementally** from the commits in `<sha>..HEAD`. In repo mode, leave out the ones already on the base branch that changed `docs/project/`: each was covered by its own update. Always keep this branch's own commits (`origin/<base-branch>..HEAD`), because an amended PR commit can change code after its docs were updated. If the commits touch nothing a user could notice (only tests, CI config, docs, lockfiles, or formatting), skip Step 4, keep the map as it is, and only move the sync line.

**Sync commit (`<sync>`):** `HEAD` on the base branch (`git rev-parse --abbrev-ref HEAD`), otherwise `git merge-base HEAD origin/<base-branch>`. A branch's own commits get new hashes when a PR is squashed or rebased on merge, so syncing to one would force a full rebuild next time.

## 4. Write the map

Follow [resources/product-map.md](resources/product-map.md). These rules apply to full and incremental updates alike:

- **Organize by what users do, not by how the code is laid out.** Activities run in the order a user meets them. Under each activity, list the capabilities a user would name ("Cancel an order"), not the modules that implement them.
- **Name the what, not the how, and keep names stable.** A capability's name changes only when the user-facing thing changes, never because the code was refactored. Stable names keep the map readable from one version to the next, and they're what PMs search for and quote in tickets.
- **Product language.** Say "Customers can cancel an order until it ships," not "`OrderService.cancel()` checks `status != SHIPPED`."
- **Use glossary terms.** If the glossary names a thing, use that name. A new concept takes the clearest product name and goes to Step 6.
- **Every entry cites its source.** One or more repo paths after each entry. An entry you can't point at code doesn't go in.
- **Only what the code does today.** No roadmap, no intent taken from specs, no guesses. Half-built work and features behind an off flag go under Known limits.
- **Say what the data and interfaces support,** because that decides effort. For each core entity: its key attributes in business terms, cardinality ("an order has exactly one shipping address"), and lifecycle states. For each interface: what it exposes and who consumes it (the app's own UI, a mobile app, partners, webhooks). An interface outside parties depend on is a contract, so mark it.

**Full:** write a new map in `<tmp>/docs/product-map.new.md` from the sources below, without reading the old map, so stale entries can't carry over. Then compare it with the old one and keep each old capability's name wherever the new entry describes the same thing.

**Incremental:** read the commits from Step 3: `git log --oneline <sha>..HEAD` and `git diff <sha>..HEAD`, or in repo mode `git show` for each commit kept. Copy the old map to `<tmp>/docs/product-map.new.md` and change only what the commits touched: entries citing a changed or deleted path, and new user-facing behaviour the commits add. Leave every other entry exactly as it is.

**Sources,** for a full build or for whatever the commits touch. The code wins whenever a doc disagrees with it:
- the glossary
- technical docs: `docs/ARCHITECTURE.md`, `docs/architecture/`, `docs/FOUNDATIONS.md`, API and data-model docs, `README.md`
- `docs/decisions/` (ADRs), for limits that were chosen on purpose
- the code: routes, pages, views, and CLI commands (screens and activities); validation, permission checks, and state changes (rules); models and migrations (entities, cardinality, states); API routes, GraphQL schemas, webhooks, and their callers (interfaces); SDK clients and their env vars (integrations); feature flags, hard caps, and user-visible `TODO`s (limits)

**Verify** before going on: re-read every new or changed entry against the paths it cites, and fix or drop any the code doesn't support. Then set the sync line to `Synced to commit <sync> on <today>.`

## 5. Append to the Decision Log

Work on `<tmp>/docs/decision-log.md`. If there's none yet, start from [resources/decision-log.md](resources/decision-log.md) and [backfill](#backfill) it first.

1. **Find what shipped** in the commits from Step 3 (none when the map had no sync line). Skip any ticket or folder that already has an entry (an entry heading containing its ID or folder).
   - **Linear:** ticket identifiers in `git log --format=%B <sha>..HEAD`, from `[ENG-123]` subjects, `Linear:` lines (an ID or an issue URL), and `Fixes ENG-123`. Pull each ticket's spec documents with the issue script, [../linear-docs/scripts/linear_docs.py](../linear-docs/scripts/linear_docs.py): `python3 <linear_docs.py> --pull <tmp>/issues/<ID> --issue <ID>`. A ticket with no spec documents gets no entry. Say so in the summary.
   - **Repo:** the spec folders those commits added or changed under `specs/` and `openspec/changes/archive/` (`git show --name-only --format= <commit>`), read from the working tree.
2. **Write one entry per ticket or folder,** newest first, in the template's shape. Extract only real decisions, the ones someone changing this area later would need:
   - **Decided / Why / Rejected:** from `research.md`'s Decision / Rationale / Alternatives considered (SpecKit), `design.md` and `proposal.md` (OpenSpec), or the decisions in `plan.md` (no framework)
   - **Complexity accepted:** the rows of the plan's Complexity Tracking table
   - **Assumes:** the spec's Assumptions that a decision depends on

   Leave out restatements of the requirements, task lists, and anything the code makes obvious. If a decision replaces an earlier entry, write `Replaces <source>: <what>` in the new entry. Never edit old entries.

### Backfill

A new Decision Log starts with one entry per spec folder already merged, so specs written before codekit, or before `codekit init` stopped tracking `specs/`, aren't lost. Only these short entries are written. The specs themselves are never uploaded, and their full text stays in git history.

- **Read from git, not from disk,** so unmerged work stays out and it works on a clone without the files. `openspec/changes/archive/` comes from `origin/<base-branch>`. So does `specs/`, unless a commit removed it from there (`git log -1 --format=%H --diff-filter=D origin/<base-branch> -- specs` prints one): then read it from that commit's parent, `<hash>^`.
- **With `--git-dir`,** the script has already exported the folders to `backfill/`, so read them there and take each date and rev from `backfill.txt`. Otherwise:
- **Folders:** `git ls-tree -d --name-only <rev> specs/` (or `openspec/changes/archive/`). **Files:** `git show <rev>:<path>`. Extract each folder as in item 2 above.
- **Date** each entry by the first commit that touched its folder (the first line of `git log --reverse --format=%as <rev> -- <folder>`). Its source is the folder plus `<rev>`'s short hash, so a reader can find the full spec in history.

## 6. Append to the glossary

Work on `<tmp>/docs/glossary.md`. If there's none yet, start from [resources/glossary.md](resources/glossary.md).

- Append an entry for each term the new map uses that the glossary lacks, and each **Key Entity** in the specs read in Step 5 that the code confirms exists, with **Owner** left blank for the team.
- **Never edit or remove an existing entry.** When the map's wording looks like a synonym of a glossary term (the map says "basket", the glossary says "cart"), change the map.
- Note glossary entries whose **Code** names no longer exist in the codebase. Report them; don't fix them.

## 7. Publish

Compare `product-map.new.md` with the current map and count the capabilities added, changed, and removed, by activity. Every file keeps its template's `# ` title as its first heading (`# Product Map`, `# Glossary`, `# Decision Log`), because Linear matches documents by title.

- **Linear:** locally, show those counts and the changed entries, and ask before publishing. With `--ci`, publish without asking.
  ```bash
  python3 <script> push <tmp>/docs/product-map.new.md <tmp>/docs/glossary.md <tmp>/docs/decision-log.md
  ```
  If Linear fails, report the error and stop. Don't retry by pasting the documents through the MCP.
- **Repo:** `mkdir -p docs/project`, then copy `product-map.new.md` to `docs/project/product-map.md`, and `glossary.md` and `decision-log.md` into the same folder. Don't ask, because the diff shows every change, and don't commit. `sdd-push` amends them into its commit. Run by hand, tell the user to commit `docs/project/`.

## 8. Summary

- **Mode:** Linear or repo, full or incremental, and the commit range covered.
- **Product Map:** capabilities added, changed, and removed per activity, or "no user-facing changes" when only the sync line moved. These counts show how much the map drifted.
- **Decision Log:** entries added per ticket or folder, backfilled entries, and tickets skipped because their issue had no spec documents.
- **Glossary:** terms appended, plus the stale **Code** names from Step 6.
- **Where:** the project URL that `push` printed, or the files written.

In the Action, this summary goes to the job log.

With `--ci`, end the output with one fixed line, so the job log shows the outcome at a glance: `CODEKIT-RESULT: published <sync>` once `push` succeeded, else `CODEKIT-RESULT: blocked <reason>` with a one-line reason (a failed key check, a missing project, a failed push, missing git input). Never print `published` for a run that didn't publish.
