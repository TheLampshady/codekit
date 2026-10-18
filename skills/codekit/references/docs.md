# codekit docs

Keeps three documents in the app's Linear project current. They live only in Linear, not in the repo. PMs read them there, ask Linear Agent about them, and file tickets in the same project.

- **Product Map**: what the app does today, in product language, including what its data and interfaces support (the basis for effort questions). It's generated, so this mode rewrites it and hand edits don't survive.
- **Decision Log**: what was decided and why, one entry per shipped ticket, pulled from the spec documents on each ticket's Linear issue. It's a reference for people looking up why something was built a certain way. Nothing in codekit feeds it to an agent: it's AI-extracted and grows with every ticket, so as planning context it would be bloated and sometimes wrong. Each entry links its ticket, which is the source.
- **Glossary**: the shared vocabulary. It belongs to the team, so PMs edit it in Linear, and this mode only appends terms to it.

Usually this runs in the `codekit-docs` GitHub Action after every merge (see init Step 7). Run it locally for the first build, or to check a change before it merges.

## Flags

| Flag | Effect |
|------|--------|
| `--ci` | Non-interactive. Never ask; take the default at every decision, and put anything a person should look at in the summary. The Action passes this. |
| `--full` | Rebuild the map from the whole codebase instead of updating it from the commits since the last sync. |

## 1. Prerequisites

From [SKILL.md](../SKILL.md#prerequisites), run only the Git repo check and the Linear API key check, and both are **required** here. Also required:

- **Linear:** `codekit.linear` isn't `false`. This mode only works with Linear, because the documents live there. Without it, stop and say so.
- **Project:** `git config codekit.linear-project`, or the same key in `.config/.gitconfig`. If it's missing, stop and suggest `/codekit update`.

**Script:** `<plugin>/skills/linear-docs/scripts/project_docs.py`, called by absolute path from the project root. It moves documents between Linear and disk without sending them through the model. Never read or write these documents with the Linear MCP: they're long, and every byte would go through the model.

## 2. Pull the current documents

Work in the system temp folder, `${TMPDIR:-/tmp}/codekit/<repo>`, where `<repo>` is the name of the repo's top-level folder (`<tmp>` below), never in the repo. The OS clears it eventually, so nothing needs cleaning up.

```bash
python3 <script> pull --title "Product Map" --out <tmp>/docs/product-map.md
python3 <script> pull --title "Glossary" --out <tmp>/docs/glossary.md
python3 <script> pull --title "Decision Log" --out <tmp>/docs/decision-log.md
```

Locally, run each command through `bash -lc '...'` so the shell profile's `LINEAR_API_KEY` is loaded.

## 3. Pick full or incremental

Read the sync line at the bottom of the pulled map: `Synced to commit <sha> on <date>.` Rebuild in **full** if any of these is true:
- `--full` was passed
- there's no map yet, or no sync line
- the commit isn't in this history (`git merge-base --is-ancestor <sha> HEAD` fails, e.g. after a force-push)

Otherwise update **incrementally** from `<sha>..HEAD`. If `git diff --stat <sha>..HEAD` touches nothing a user could notice (only tests, CI config, docs, lockfiles, or formatting), skip Step 4, keep the map as it is, and only move the sync line to `HEAD`.

## 4. Write the map

Follow [../resources/product-map.md](../resources/product-map.md). These rules apply in both modes:

- **Organize by what users do, not by how the code is laid out.** Activities run in the order a user meets them. Under each activity, list the capabilities a user would name ("Cancel an order"), not the modules that implement them.
- **Name the what, not the how, and keep names stable.** A capability's name changes only when the user-facing thing changes, never because the code was refactored. Stable names keep the map readable from one version to the next, and they're what PMs search for and quote in tickets.
- **Product language.** Say "Customers can cancel an order until it ships," not "`OrderService.cancel()` checks `status != SHIPPED`."
- **Use glossary terms.** If the glossary names a thing, use that name. A new concept takes the clearest product name and goes to Step 5.
- **Every entry cites its source.** One or more repo paths after each entry. An entry you can't point at code doesn't go in.
- **Only what the code does today.** No roadmap, no intent taken from specs, no guesses. Half-built work and features behind an off flag go under Known limits.
- **Say what the data and interfaces support,** because that decides effort. For each core entity: its key attributes in business terms, cardinality ("an order has exactly one shipping address"), and lifecycle states. For each interface: what it exposes and who consumes it (the app's own UI, a mobile app, partners, webhooks). An interface outside parties depend on is a contract, so mark it.

**Full:** write a new map in `<tmp>/docs/product-map.new.md` from the sources below, without reading the old map, so stale entries can't carry over. Then compare it with the old one and keep each old capability's name wherever the new entry describes the same thing.

**Incremental:** read `git log --oneline <sha>..HEAD` and `git diff <sha>..HEAD`. Copy the old map to `<tmp>/docs/product-map.new.md` and change only what the commits touched: entries citing a changed or deleted path, and new user-facing behaviour the diff adds. Leave every other entry exactly as it is.

**Sources,** for a full build or for whatever a diff touches. The code wins whenever a doc disagrees with it:
- the glossary
- technical docs: `docs/ARCHITECTURE.md`, `docs/architecture/`, `docs/FOUNDATIONS.md`, API and data-model docs, `README.md`
- `docs/decisions/` (ADRs), for limits that were chosen on purpose
- the code: routes, pages, views, and CLI commands (screens and activities); validation, permission checks, and state changes (rules); models and migrations (entities, cardinality, states); API routes, GraphQL schemas, webhooks, and their callers (interfaces); SDK clients and their env vars (integrations); feature flags, hard caps, and user-visible `TODO`s (limits)

**Verify** before going on: re-read every new or changed entry against the paths it cites, and fix or drop any the code doesn't support. Then set the sync line to `Synced to commit <HEAD sha> on <today>.`

## 5. Append to the Decision Log

Work on `<tmp>/docs/decision-log.md`. If the pull found none, start from [../resources/decision-log.md](../resources/decision-log.md).

1. **Find the shipped tickets** in the range from Step 3: Linear identifiers in `git log --format=%B <sha>..HEAD`, from `Linear: ENG-123` lines, `[ENG-123]` subjects, and `Fixes ENG-123`. With no sync line (a first run), don't backfill history: the log starts with the next merge. Skip any ticket that already has an entry (an entry heading containing its ID).
2. **Pull each ticket's spec documents** with the issue script, [../../linear-docs/scripts/linear_docs.py](../../linear-docs/scripts/linear_docs.py): `python3 <linear_docs.py> --pull <tmp>/issues/<ID> --issue <ID>`. A ticket with no spec documents gets no entry. Say so in the summary.
3. **Write one entry per ticket,** newest first, in the template's shape. Extract only real decisions, the ones someone changing this area later would need:
   - **Decided / Why / Rejected:** from `research.md`'s Decision / Rationale / Alternatives considered (SpecKit), or `design.md` and `proposal.md` (OpenSpec)
   - **Complexity accepted:** the rows of the plan's Complexity Tracking table
   - **Assumes:** the spec's Assumptions that a decision depends on

   Leave out restatements of the requirements, task lists, and anything the code makes obvious. If a decision replaces an earlier entry, write `Replaces <ID>: <what>` in the new entry. Never edit old entries.

## 6. Append to the glossary

Work on `<tmp>/docs/glossary.md`. If the pull found no glossary, start from [../resources/glossary.md](../resources/glossary.md).

- Append an entry for each term the new map uses that the glossary lacks, and each **Key Entity** in the pulled tickets' `spec.md` that the code confirms exists, with **Owner** left blank for the team.
- **Never edit or remove an existing entry.** When the map's wording looks like a synonym of a glossary term (the map says "basket", the glossary says "cart"), change the map.
- Note glossary entries whose **Code** names no longer exist in the codebase. Report them; don't fix them.

## 7. Publish

Compare `product-map.new.md` with the pulled map and count the capabilities added, changed, and removed, by activity.

- **Local:** show those counts and the changed entries, and ask before publishing.
- **`--ci`:** publish without asking.

```bash
python3 <script> push <tmp>/docs/product-map.new.md <tmp>/docs/glossary.md <tmp>/docs/decision-log.md
```

Documents are matched by their `# ` title, so the files must keep `# Product Map`, `# Glossary`, and `# Decision Log` as their first headings. If Linear fails, report the error and stop. Don't retry by pasting the documents through the MCP.

## 8. Summary

- **Mode:** full or incremental, and the commit range covered.
- **Product Map:** capabilities added, changed, and removed per activity, or "no user-facing changes" when only the sync line moved. These counts show how much the map drifted.
- **Decision Log:** entries added per ticket, and tickets skipped because their issue had no spec documents.
- **Glossary:** terms appended, plus the stale **Code** names from Step 6.
- **Links:** the project URL that `push` printed.

In the Action, this summary goes to the job log.
