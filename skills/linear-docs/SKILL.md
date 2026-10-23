---
name: linear-docs
description: 'Keep a spec folder''s decision-bearing files (spec, plan, research; OpenSpec proposal, design) on its Linear issue as documents, the spec''s copy of record, since spec folders aren''t committed. Uploads or pulls without passing file text through the model, using a Linear API key, not the MCP. Use when asked to: sync, upload, push, publish, or refresh spec docs on a Linear issue, pull a spec back from its issue, resume a spec on another machine.'
user-invocable: true
disable-model-invocation: true
context: fork
agent: general-purpose
background: false
argument-hint: "[spec folder | ENG-123] [--pull] [--dry-run] [--prune] [--yes]"
---

# Linear Docs

Syncs a spec folder to its Linear issue with [scripts/linear_docs.py](scripts/linear_docs.py). In SpecKit and no-framework projects the spec folder is gitignored and stays local while you work. `sdd-push` uploads it at PR time, making the issue its copy of record, and the `codekit-docs` Action reads it after merge to build the Decision Log. The script reads the files from disk and calls Linear's GraphQL API itself. That keeps the documents identical to the files, and a sync costs a few hundred tokens instead of the size of the files. When this skill applies, never upload spec files through the Linear MCP (`save_document`): that sends every byte through the model.

**Script path:** `scripts/linear_docs.py` lives in this skill's directory, the folder containing this `SKILL.md`, not the user's project. Call it by absolute path and run it **from the project root**, because the script finds the project from the current git repo.

**Running it:** if `LINEAR_API_KEY` is already in the environment (`[ -n "${LINEAR_API_KEY:-}" ]` tests that without printing it), run `python3 <script> …` directly. Otherwise run `"$SHELL" -lic 'python3 <script> …' </dev/null`. That starts the user's own shell as a login, interactive shell, which reads the profile where the key is exported (`~/.zshrc`, `~/.bashrc`), so a key added after the session started is still found. `</dev/null` keeps a profile that waits for input from hanging. Ignore anything the profile prints before the script's own output.

## Input

`$ARGUMENTS` may name a spec folder, a number (`026` → `specs/026-*`), an issue (`ENG-123`), and flags. With no arguments, the script works out the folder and issue itself (see [Resolution](#resolution)).

## Decisions

This skill may run as an isolated subagent that can't talk to the user. When a step below needs the user's decision, **stop without writing anything** and end your reply with the question, the options, and the exact arguments for each option (e.g. `--issue ENG-123`, `--yes`). The caller asks the user and runs the skill again with the answer. When you *can* ask the user directly, ask, then continue.

## Steps

1. **Pick the folder and issue.**
   - **Folder:** the one named, or `specs/NNN-*` for a number. With nothing given, let the script resolve it.
   - **Issue:** the one named, else let the script resolve it. If the script reports no issue, find candidate issues whose title matches the spec (`list_issues` with `query`). This is a [decision](#decisions): return the candidates as `--issue` options. Never edit the spec files to add a `**Linear:**` line.
   - **Given only an issue:** find its folder by the `**Linear:**` line in `specs/*/spec.md` or `specs/*/ticket.md`, or by the identifier in an `openspec/changes/` or `specs/` folder name. If none or several match, it's a [decision](#decisions). For a pull with no local folder, offer `specs/<lowercased-id>-<slug-of-the-issue-title>` (e.g. `specs/eng-123-add-login`) as the default: it's the name `sdd-plan` gives, and later steps find the folder by the ID in it.

2. **Note the state of the docs, then keep going.** Report it in one line. Never stop or ask because of these, and never edit the files:
   - `git status --short <folder>`: whether the folder has uncommitted changes. That's fine, because the upload uses the files as they are on disk.
   - In `tasks.md`, how many tasks are still open (`- [ ]`). Open tasks are fine.

3. **Dry run**, always first, run as **Running it** above describes:

   ```bash
   python3 <skill-dir>/scripts/linear_docs.py [<folder>] [--issue ENG-123] --dry-run
   ```

   The output has one line per document: `create`, `update`, `unchanged`, or (with `--prune`) `delete`.

4. **Sync** with the same arguments minus `--dry-run`. Run it without asking again when the dry run shows only `create`, `update` and `unchanged`. If it would `delete` anything, that's a [decision](#decisions): list the titles to be deleted. Only pass `--yes` when the arguments already include it, meaning the user has approved those deletes.

5. **Report** the issue link and the counts, in one or two lines.

## Pull

`--pull <folder> --issue ENG-123` writes the issue's spec documents into `<folder>`, for example when resuming a spec on another machine. Files that already exist locally are kept, unless `--yes` is passed, which means the user approved overwriting them. If the script reports kept files, that's a [decision](#decisions): list them, with `--yes` as the option.

## Resolution

| What | Order |
|------|-------|
| Project root | The enclosing git repo of the current directory |
| Folder | Argument → the `openspec/changes/*` or `specs/*` folder whose name contains the branch's issue ID → `.specify/feature.json` (SpecKit's last-specified feature) |
| Issue | `--issue` → a `**Linear:** ENG-123` line in `spec.md`, `ticket.md`, or `proposal.md` → the ID in the folder name → the ID in the branch name |
| Team guard | `--team`, else `git config codekit.linear-team`, else that key in the committed `.config/.gitconfig`. When either is set, issues on other teams are refused. |

## What gets uploaded

- Only the files that record what was decided and why, each as one document titled with its file name: `spec.md`, `proposal.md`, `plan.md`, `design.md`, `research.md`.
- Everything else stays local: `tasks.md`, `data-model.md`, `contracts/`, `quickstart.md`, checklists, and a manual plan's `ticket.md` (which is the issue itself). Once the feature ships, the code supersedes them.
- Documents are matched by title. An existing title is overwritten only when its words differ. Linear rewrites markdown on save, so punctuation, bullets and links are ignored, and a formatting-only edit isn't uploaded. A new title creates a new document. Nothing is deleted unless `--prune` is passed. Prune also removes duplicate copies with the same title.

## Rules

- The script reads `LINEAR_API_KEY` from the environment. Never read, print, or ask for its value, and never write it to a file. If it's missing, tell the user to export it in their shell profile. In Linear, keys are under **Settings → Security & access → Personal API keys**.
- This skill only touches documents. It never changes the issue description, and never creates issues or sub-issues.
- When syncing several folders, run them one at a time, dry run first for each.
