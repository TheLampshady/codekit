---
name: wiki-docs
description: 'Upload a spec folder''s spec, plan, and research to the GitLab project''s wiki, or pull a ticket''s spec back, through git. Started by sdd-push. Run it only when another codekit skill calls for it or the user names wiki-docs.'
user-invocable: true
disable-model-invocation: false
context: fork
agent: general-purpose
background: false
argument-hint: "[spec folder] [--pull <folder> --issue <#123>] [--dry-run] [--prune] [--yes]"
---

# Wiki Docs

Syncs a spec folder to the GitLab project's wiki with [scripts/wiki_docs.py](scripts/wiki_docs.py). With GitLab issues, the spec folder is gitignored and stays local while you work. `sdd-push` uploads it at PR time to `specs/<folder>/` in the wiki, the spec's copy of record, and the `codekit-docs` CI job reads it after merge to build the Decision Log. The wiki is a git repo next to the code, so the script clones it into the system temp folder and pushes one commit. The files never pass through the model.

**Script path:** `scripts/wiki_docs.py` lives in this skill's directory, the folder containing this `SKILL.md`, not the user's project. Call it by absolute path and run it **from the project root**: the script finds the wiki from the repo's `origin` remote, on any GitLab host. It uses git's own login for that host, so there's no key to set up.

## Input

`$ARGUMENTS` may name a spec folder, a number (`026` → `specs/026-*`), and flags. With no folder, use the `openspec/changes/*` or `specs/*` folder named for the branch's ticket (its name starts with the branch's leading number and a `-`, e.g. `123-add-login`), else the folder `.specify/feature.json` names.

## Decisions

This skill may run as an isolated subagent that can't talk to the user. When a step below needs the user's decision, **stop without writing anything** and end your reply with the question, the options, and the exact arguments for each option (e.g. `--yes`). The caller asks the user and runs the skill again with the answer. When you *can* ask the user directly, ask, then continue.

## Steps

1. **Pick the folder** as [Input](#input) says. If none or several match, that's a [decision](#decisions): list the candidates as folder arguments.
2. **Note the state of the docs, then keep going.** Report it in one line. Never stop or ask because of these, and never edit the files:
   - `git status --short <folder>`: whether the folder has uncommitted changes. That's fine, because the upload uses the files as they are on disk.
   - In `tasks.md`, how many tasks are still open (`- [ ]`). Open tasks are fine.
3. **Dry run**, always first:

   ```bash
   python3 <skill-dir>/scripts/wiki_docs.py push <folder> --dry-run
   ```

   The output has one line per page: `create`, `update`, `unchanged`, or (with `--prune`) `delete`.
4. **Sync** with the same arguments minus `--dry-run`. Run it without asking again when the dry run shows only `create`, `update` and `unchanged`. If it would `delete` anything, that's a [decision](#decisions): list the pages to be deleted. Only pass `--yes` when the arguments already include it, meaning the user has approved those deletes.
5. **Report** the wiki link and the counts, in one or two lines.

If the script can't reach the wiki, report its message as it is: it says what to check (the wiki turned on, access to the code, or a first page for a brand-new wiki).

## Pull

`--pull <folder> --issue <ref>` runs `python3 <script> pull <folder> --issue <ref>`, which writes the ticket's spec pages into `<folder>`, for example when resuming a spec on another machine. `<ref>` is `#123`, `group/app#123`, or the issue URL. Files that already exist locally are kept, unless `--yes` is passed, which means the user approved overwriting them. If the script reports kept files, that's a [decision](#decisions): list them, with `--yes` as the option.

## What gets uploaded

- Only the files that record what was decided and why: `spec.md`, `proposal.md`, `plan.md`, `design.md`, `research.md`. Each becomes a page under `specs/<folder>/`. An OpenSpec archive folder drops its date, so `openspec/changes/archive/2026-11-26-123-add-login/` lands in `specs/123-add-login/`.
- Everything else stays local: `tasks.md`, `data-model.md`, `contracts/`, `quickstart.md`, checklists, and a manual plan's `ticket.md` (which is the issue itself). Once the feature ships, the code supersedes them.
- A page is rewritten only when its file changed. Nothing is deleted unless `--prune` is passed.

## Rules

- In CI, the script authenticates with `CODEKIT_WIKI_TOKEN` from the environment. Never read, print, or ask for its value.
- This skill only touches wiki pages. It never changes the issue, and never creates issues.
- When syncing several folders, run them one at a time, dry run first for each.
