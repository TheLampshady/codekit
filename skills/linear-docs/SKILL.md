---
name: linear-docs
description: 'Upload a spec folder (SpecKit specs/NNN-name, OpenSpec openspec/changes/<id>, or specs/<id>) to its Linear issue as documents, one per file, adding new ones and overwriting ones with the same title, without passing file text through the model. Uses a Linear API key, not the MCP. Use when asked to: sync, upload, push, publish, or refresh spec docs on a Linear issue, or after a spec, plan, design, or tasks file changes and the issue should match.'
user-invocable: true
disable-model-invocation: true
context: fork
agent: general-purpose
background: false
argument-hint: "[spec folder | ENG-123] [--dry-run] [--prune] [--yes]"
---

# Linear Docs

Syncs a spec folder to its Linear issue with [scripts/linear_docs.py](scripts/linear_docs.py). The script reads the files from disk and calls Linear's GraphQL API itself. That keeps the documents identical to the files, and a sync costs a few hundred tokens instead of the size of the files. When this skill applies, never upload spec files through the Linear MCP (`save_document`): that sends every byte through the model.

**Script path:** `scripts/linear_docs.py` lives in this skill's directory, the folder containing this `SKILL.md`, not the user's project. Call it by absolute path and run it **from the project root**, because the script finds the project from the current git repo.

## Input

`$ARGUMENTS` may name a spec folder, a number (`026` → `specs/026-*`), an issue (`ENG-123`), and flags. With no arguments, the script works out the folder and issue itself (see [Resolution](#resolution)).

## Decisions

This skill may run as an isolated subagent that can't talk to the user. When a step below needs the user's decision, **stop without writing anything** and end your reply with the question, the options, and the exact arguments for each option (e.g. `--issue ENG-123`, `--yes`). The caller asks the user and runs the skill again with the answer. When you *can* ask the user directly, ask, then continue.

## Steps

1. **Pick the folder and issue.**
   - **Folder:** the one named, or `specs/NNN-*` for a number. With nothing given, let the script resolve it.
   - **Issue:** the one named, else let the script resolve it. If the script reports no issue, find candidate issues whose title matches the spec (`list_issues` with `query`). This is a [decision](#decisions): return the candidates as `--issue` options. Never edit the spec files to add a `**Linear:**` line.
   - **Given only an issue:** find its folder by the `**Linear:**` line in `specs/*/spec.md` or `*/ticket.md`, or by the identifier in an `openspec/changes/` or `specs/` folder name. If none or several match, it's a [decision](#decisions).

2. **Note the state of the docs, then keep going.** Report it in one line. Never stop or ask because of these, and never edit the files:
   - `git status --short <folder>`: whether the folder has uncommitted changes. That's fine, because the upload uses the files as they are on disk.
   - In `tasks.md`, how many tasks are still open (`- [ ]`). Open tasks are fine.

3. **Dry run**, always first:

   ```bash
   bash -lc 'python3 <skill-dir>/scripts/linear_docs.py [<folder>] [--issue ENG-123] --dry-run'
   ```

   `bash -lc` loads the user's shell profile, where `LINEAR_API_KEY` is exported, so a key added after the session started is still found. The output has one line per document: `create`, `update`, `unchanged`, or (with `--prune`) `delete`.

4. **Sync** with the same arguments minus `--dry-run`. Run it without asking again when the dry run shows only `create`, `update` and `unchanged`. If it would `delete` anything, that's a [decision](#decisions): list the titles to be deleted. Only pass `--yes` when the arguments already include it, meaning the user has approved those deletes.

5. **Report** the issue link and the counts, in one or two lines.

## Resolution

| What | Order |
|------|-------|
| Project root | The enclosing git repo of the current directory |
| Folder | Argument → `.specify/feature.json` (SpecKit) → the `openspec/changes/*` or `specs/*` folder whose name contains the branch's issue ID |
| Issue | `--issue` → a `**Linear:** ENG-123` line in `spec.md`, `ticket.md`, or `proposal.md` → the ID in the folder name → the ID in the branch name |
| Team guard | `--team`, else `git config codekit.linear-team`. When either is set, issues on other teams are refused. |

## What gets uploaded

- One document per top-level `.md` file, titled with the file name, in reading order: `spec.md`, `proposal.md`, `plan.md`, `design.md`, `research.md`, `data-model.md`, `tasks.md`, then any others alphabetically.
- One `contracts` document joining `contracts/*.md` (SpecKit), and one `specs` document joining `specs/**/*.md` (OpenSpec spec deltas). Each part is headed with its path.
- Skipped: `ticket.md` (it's the issue itself), `quickstart.md`, and `checklists/`.
- Documents are matched by title. An existing title is overwritten only when its words differ. Linear rewrites markdown on save, so punctuation, bullets and links are ignored, and a formatting-only edit isn't uploaded. A new title creates a new document. Nothing is deleted unless `--prune` is passed. Prune also removes duplicate copies with the same title.

## Rules

- The script reads `LINEAR_API_KEY` from the environment. Never read, print, or ask for its value, and never write it to a file. If it's missing, tell the user to export it in their shell profile. In Linear, keys are under **Settings → Security & access → Personal API keys**.
- This skill only touches documents. It never changes the issue description, and never creates issues or sub-issues.
- When syncing several folders, run them one at a time, dry run first for each.
