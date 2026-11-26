---
name: sdd-plan
description: 'Start feature work from a Linear or GitLab issue, a local spec file, or pasted ticket text. Picks up the issue (assigns it, moves it to In Progress), checks out its git branch, and hands the ticket to the active spec-driven-development framework (SpecKit or OpenSpec) to specify, clarify, and plan. Use when asked to: start ticket, pick up issue ENG-123 or #123, work on an issue, plan the ticket, spec the ticket, use spec FILE, grab my next issue.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[ENG-123 | #123 | issue-url | path/to/spec.md | next]"
---

# SDD Plan

Turns a ticket into a reviewed plan on a feature branch. The plan is the deliverable; no feature code is written here. That happens in `sdd-implement`.

## Workflow

**Tracker:** `git config codekit.tracker` names it. Read its file before Step 1 and use its calls wherever a step says *the tracker file*:

| `codekit.tracker` | Tracker file |
|-------------------|--------------|
| `linear` | [references/linear.md](references/linear.md) |
| `gitlab` | [references/gitlab.md](references/gitlab.md) |

With `none` there's no tracker: treat any identifier as plain text, take only a file or pasted text as input, and skip Steps 2, 3, and 7. The spec folder stays committed with the code, since it has no other home. If the key is unset, do the same and suggest `/codekit init`, which sets it.

### 1. Identify the input

Classify the request into exactly one source:

| Source | Detect by | `<ticket-id>` | `<branch-name>` |
|--------|-----------|---------------|-----------------|
| **Ticket reference** | An ID form from the tracker file's **IDs** (`ENG-123`, `#123`) | As the tracker file writes it | From the tracker file's **Branch** (Step 4) |
| **Ticket URL** | The tracker file's URL form | As the tracker file writes it | From the tracker file's **Branch** |
| **"next" / "my next issue"** | No ID, but asks for their next issue | Chosen in Step 2 | From the tracker file's **Branch** |
| **Local file** | A path that exists | A ticket reference found in the file, if any | `feature/<slug-of-filename>` |
| **Pasted text** | Ticket-like text in the message | A ticket reference found in the text, if any | `feature/<slug-of-title>` |

When a file or pasted text contains a ticket reference, treat it as the ticket path: the issue is the source of truth and the local text is extra context. If the tracker can't find it, it was only text shaped like an ID (`UTF-8`, `SHA-256`, "step #2"): say so and continue on the local path.

If none apply ("plan the ticket" with nothing else), ask: *"Which issue? Give me an issue ID or URL, a spec file path, paste the details, or say 'next' to pick from your assigned issues."* Stop until answered.

### 2. Choose an issue ("next" only)

Follow the tracker file's **Next**. Present up to 10 with ID, title, and what the tracker offers for urgency, most urgent first, and let the user pick. If nothing is returned, tell the user the queue is empty.

### 3. Fetch and start the issue (ticket path only)

1. **Fetch** it as the tracker file's **Fetch** says. Keep the title, description, URL, state, assignee, labels, and project or milestone, and read the comments too, because the discussion often holds requirements the description lacks.
2. **Start it** as the tracker file's **Start** says. If it's already started, skip the move. If it's closed, completed, or canceled, ask before reopening it. Assign it to the user if it's unassigned. If it's assigned to someone else, ask before reassigning.

If a tracker call fails with an auth or connection error, follow the tracker file's **Errors**. Do not silently continue on the non-ticket path.

### 4. Check out the feature branch

1. `git status --porcelain`. If the tree is dirty, ask whether to stash, commit, or carry the changes onto the new branch.
2. Resolve `<base-branch>` (see [Base branch](#base-branch)) and `git fetch origin <base-branch>`. With no `origin` remote, skip the fetch and use the local `<base-branch>` below.
3. If `<branch-name>` exists locally: `git checkout <branch-name>`. If it only exists on the remote: `git checkout --track origin/<branch-name>`. Otherwise: `git checkout --no-track -b <branch-name> origin/<base-branch>`. `--no-track` stops git from making the base branch its upstream; `sdd-push` sets the real one on the first push.

### 5. Build `<ticket-contents>`

For the ticket path, format the issue in memory:

```markdown
# <title>

**Ticket:** [<ticket-id>](<url>) | **Status:** <state> | **Assignee:** <assignee>
**Labels:** <labels> | **Project:** <project or milestone>

---

## Description

<description>

## Discussion

<comments, oldest first: author, date, body>
```

For a file or pasted text, use it as-is. Add a `# <title>` header if it has none.

### 6. Hand off to the SDD framework

Detect the framework from the repo root and use the first match:

| Framework | Detected by |
|-----------|-------------|
| SpecKit | `.specify/` directory |
| OpenSpec | `openspec/` directory (or `openspec/config.yaml`) |
| None | Neither |

In the plan phase, check every library, framework, SDK, or cloud API the plan relies on with Context7 (`resolve-library-id`, then `query-docs`) at the version the project pins.

Name the work `<feature-slug>`: a kebab-case slug of the title, prefixed with the ticket's `<ticket-slug>` from the tracker file when there is one (e.g. `eng-123-add-login`, `123-add-login`). Later skills find the ticket's files by that prefix, even after you've switched to another ticket and back.

**SpecKit**
1. **Already specified?** If `specs/<feature-slug>/spec.md` exists, `/speckit.specify` would replace it, so ask whether to start over or keep it. To keep it, point SpecKit at it the way `/speckit.specify` does, by writing `{"feature_directory": "specs/<feature-slug>"}` to `.specify/feature.json`, and skip to step 4.
2. Run `/speckit.specify` (or the `speckit-specify` skill) with `<ticket-contents>` as the feature description and `SPECIFY_FEATURE_DIRECTORY=specs/<feature-slug>`, so the folder is named for the ticket instead of numbered. SpecKit records it in `.specify/feature.json`.
3. **Branch guard:** if SpecKit's opt-in `git` extension checked out a numbered branch (e.g. `001-...`), run `git checkout <branch-name>` to switch back. Ask before deleting the extra branch. Suggest disabling that extension in [docs/extensions/speckit.md](../../docs/extensions/speckit.md).
4. Run `/speckit.clarify` and put its questions to the user. Wait for answers.
5. Once they're answered, don't summarize or ask whether to continue. Post the clarifications to the issue (Step 7), then run `/speckit.plan` yourself in the same turn. Stop there: don't run `/speckit.tasks`, and ignore SpecKit's own next-step suggestions. `sdd-implement` generates the tasks.

If a SpecKit command isn't installed, stop and suggest `/codekit update`, which installs and refreshes the framework's commands. Don't do the framework's work by hand.

**OpenSpec**
1. Run `/opsx:explore` with `<ticket-contents>` to surface open questions. Put them to the user and wait for answers.
2. Post the clarifications to the issue (Step 7).
3. Run `/opsx:propose <feature-slug>` with `<ticket-contents>` plus the answers. It drafts the proposal, spec deltas, design and tasks under `openspec/changes/<feature-slug>/`.

If the `/opsx:*` commands aren't installed, stop and suggest `/codekit update`, which installs and refreshes the framework's commands. Don't do the framework's work by hand.

**None (manual)**
1. Save `<ticket-contents>` to `specs/<feature-slug>/ticket.md`.
2. Read the ticket and the code it touches, then list what's unclear or undecided as questions, each with lettered options and a recommendation. Stop until the user answers.
3. Post the clarifications to the issue (Step 7).
4. Write `specs/<feature-slug>/plan.md`: the approach, the decisions from step 2 and why, the files to touch, risks, and how to test.

### 7. Post clarifications to the issue

Only on the ticket path, **and** when clarifications were asked and answered.

1. Read [resources/comment-template.md](resources/comment-template.md) and fill it in, one section per question, all in one comment.
2. Post it as the tracker file's **Comment** says. Send real newlines, not `\n` escapes.
3. If a requirement changed materially, offer to add it to the end of the issue description, as the tracker file's **Comment** says. Never replace the description outright.

### 8. Summary

One line each: the issue and its new state (or "local spec"), the branch, and the plan files' paths. Next is reviewing the plan here, then `/sdd-implement`. Name only `/sdd-implement` as the next step, never `/speckit.tasks`, `/speckit.analyze`, or other framework commands.

## Base branch

1. `git config codekit.basebranch`, if set.
2. `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`).
3. The first of `origin/main` or `origin/master` that exists.
4. `main`.

If it came from step 2–4, offer once to save it: `git config -f .config/.gitconfig codekit.basebranch <branch>` (`--local` if that file doesn't exist).
