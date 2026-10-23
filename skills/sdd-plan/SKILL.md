---
name: sdd-plan
description: 'Start feature work from a Linear issue, a local spec file, or pasted ticket text. Picks up the issue in Linear (assigns it, moves it to In Progress), checks out the issue''s git branch, and hands the ticket to the active spec-driven-development framework (SpecKit or OpenSpec) to specify, clarify, and plan. Use when asked to: start ticket, pick up issue ENG-123, work on a Linear issue, plan the ticket, spec the ticket, use spec <file>, grab my next issue.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[ENG-123 | linear-url | path/to/spec.md | next]"
---

# SDD Plan

Turns a ticket into a reviewed plan on a feature branch. The plan is the deliverable; no feature code is written here. That happens in `sdd-implement`.

## Workflow

**Linear off:** if `git config codekit.linear` is `false`, the repo doesn't use Linear. Treat any identifier as plain text, take only a file or pasted text as input, and skip Steps 2, 3, and 7. The spec folder stays committed with the code, since it has no other home.

### 1. Identify the input

Classify the request into exactly one source:

| Source | Detect by | `<ticket-id>` | `<branch-name>` |
|--------|-----------|---------------|-----------------|
| **Linear identifier** | Matches `[A-Za-z][A-Za-z0-9]+-\d+` (e.g. `ENG-123`, `eng-123`) | The identifier, uppercased | Issue's `gitBranchName` (Step 3) |
| **Linear URL** | `linear.app/<workspace>/issue/<ID>/...` | The `<ID>` path segment | Issue's `gitBranchName` |
| **"next" / "my next issue"** | No ID, but asks for their next issue | Chosen in Step 2 | Issue's `gitBranchName` |
| **Local file** | A path that exists | A Linear identifier found in the file, if any | `feature/<slug-of-filename>` |
| **Pasted text** | Ticket-like text in the message | A Linear identifier found in the text, if any | `feature/<slug-of-title>` |

When a file or pasted text contains a Linear identifier, treat it as the Linear path: the issue in Linear is the source of truth and the local text is extra context. If `get_issue` can't find it, it was only text shaped like an ID (`UTF-8`, `SHA-256`): say so and continue on the local path.

If none apply ("plan the ticket" with nothing else), ask: *"Which issue? Give me a Linear ID or URL, a spec file path, paste the details, or say 'next' to pick from your assigned issues."* Stop until answered.

### 2. Choose an issue ("next" only)

Call the Linear MCP `list_issues` with `assignee: "me"`, `state: "unstarted"`, and `fields: ["title", "priority", "status"]`, so descriptions aren't fetched for every issue. If `git config codekit.linear-team` is set, pass it as `team`. If `git config codekit.linear-project` is set, pass it as `project`. Present up to 10 with identifier, title and priority, Urgent first and No priority last (Linear numbers it 0), and let the user pick. If nothing is returned, retry with `state: "backlog"` before telling the user the queue is empty.

### 3. Fetch and start the Linear issue (Linear path only)

1. Call `get_issue` with the `<ticket-id>`. Keep `title`, `description`, `url`, `gitBranchName`, `status`, `team`, `assignee`, `labels`, `project`, and `attachments`. Call `list_comments` for the issue as well, because the discussion often holds requirements the description lacks.
2. **Start it.** If the issue is already in a `started`-type state, skip the move. If it's `completed` or `canceled`, ask before reopening it. Otherwise call `list_issue_statuses` for the issue's team and take the first state whose type is `started`, which is "In Progress" on most teams.
3. Call `save_issue` with `id: <ticket-id>`, `state: <that state>`, and `assignee: "me"` if it is unassigned. If it's assigned to someone else, ask before reassigning.
4. If `git config codekit.linear-team` is unset, offer to save the issue's team key: `git config -f .config/.gitconfig codekit.linear-team <team-key>`, so the team shares it (`--local` if that file doesn't exist). The `next` flow uses it.

If any Linear call fails with an auth or connection error, follow [Linear MCP errors](#linear-mcp-errors). Do not silently continue on the non-Linear path.

### 4. Check out the feature branch

1. `git status --porcelain`. If the tree is dirty, ask whether to stash, commit, or carry the changes onto the new branch.
2. Resolve `<base-branch>` (see [Base branch](#base-branch)) and `git fetch origin <base-branch>`. With no `origin` remote, skip the fetch and use the local `<base-branch>` below.
3. If `<branch-name>` exists locally: `git checkout <branch-name>`. If it only exists on the remote: `git checkout --track origin/<branch-name>`. Otherwise: `git checkout --no-track -b <branch-name> origin/<base-branch>`. `--no-track` stops git from making the base branch its upstream; `sdd-pr` sets the real one on the first push.

Using Linear's `gitBranchName` verbatim is deliberate: Linear's GitHub integration links any branch or PR that contains the identifier, and it moves the issue through its workflow automatically.

### 5. Build `<ticket-contents>`

For the Linear path, format the issue in memory:

```markdown
# <title>

**Linear:** [<ticket-id>](<url>) | **Status:** <state> | **Assignee:** <assignee>
**Labels:** <labels> | **Project:** <project>

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

Name the work `<feature-slug>`: a kebab-case slug of the title, prefixed with the lowercased ticket ID when there is one (e.g. `eng-123-add-login`). Later skills find the ticket's files by the ID in that name, even after you've switched to another ticket and back.

**SpecKit**
1. **Already specified?** If `specs/<feature-slug>/spec.md` exists, `/speckit.specify` would replace it, so ask whether to start over or keep it. To keep it, point SpecKit at it the way `/speckit.specify` does, by writing `{"feature_directory": "specs/<feature-slug>"}` to `.specify/feature.json`, and skip to step 4.
2. Run `/speckit.specify` (or the `speckit-specify` skill) with `<ticket-contents>` as the feature description and `SPECIFY_FEATURE_DIRECTORY=specs/<feature-slug>`, so the folder is named for the ticket instead of numbered. SpecKit records it in `.specify/feature.json`.
3. **Branch guard:** if SpecKit's opt-in `git` extension checked out a numbered branch (e.g. `001-...`), run `git checkout <branch-name>` to switch back. Ask before deleting the extra branch. Suggest disabling that extension in [docs/extensions/speckit.md](../../docs/extensions/speckit.md).
4. Run `/speckit.clarify` and put its questions to the user. Wait for answers.
5. Post the clarifications to Linear (Step 7), then run `/speckit.plan`.

If a SpecKit command isn't installed, stop and suggest `/codekit update`, which installs and refreshes the framework's commands. Don't do the framework's work by hand.

**OpenSpec**
1. Run `/opsx:explore` with `<ticket-contents>` to surface open questions. Put them to the user and wait for answers.
2. Post the clarifications to Linear (Step 7).
3. Run `/opsx:propose <feature-slug>` with `<ticket-contents>` plus the answers. It drafts the proposal, spec deltas, design and tasks under `openspec/changes/<feature-slug>/`.

If the `/opsx:*` commands aren't installed, stop and suggest `/codekit update`, which installs and refreshes the framework's commands. Don't do the framework's work by hand.

**None (manual)**
1. Save `<ticket-contents>` to `specs/<feature-slug>/ticket.md`.
2. Read the ticket and the code it touches, then list what's unclear or undecided as questions, each with lettered options and a recommendation. Stop until the user answers.
3. Post the clarifications to Linear (Step 7).
4. Write `specs/<feature-slug>/plan.md`: the approach, the decisions from step 2 and why, the files to touch, risks, and how to test.

### 7. Post clarifications to Linear

Only if this is a Linear issue **and** clarifications were asked and answered.

1. Read [resources/comment-template.md](resources/comment-template.md) and fill it in, one section per question, all in one comment.
2. Call `save_comment` with `issueId: <ticket-id>` and the filled template as `body`. Send real newlines, not `\n` escapes.
3. If a requirement changed materially, offer to update the issue description with `save_issue` (`patch` with `append`). Never replace the description outright.

### 8. Summary

One line each: the issue and its new state (or "local spec"), the branch, and the plan files' paths. Next is reviewing the plan here, then `/sdd-implement`.

## Base branch

1. `git config codekit.basebranch`, if set.
2. `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`).
3. The first of `origin/main` or `origin/master` that exists.
4. `main`.

If it came from step 2–4, offer once to save it: `git config -f .config/.gitconfig codekit.basebranch <branch>` (`--local` if that file doesn't exist).

## Linear MCP errors

The plugin ships the Linear MCP server (`https://mcp.linear.app/mcp`) with OAuth.

- **Not connected or tools missing:** in Claude Code, have the user run `/mcp` and authenticate `linear`. In Antigravity, have them open the MCP servers panel and sign in to `linear`.
- **401 / expired:** re-authenticate the same way.
- **Issue not found:** confirm the identifier and that the user's workspace can see the team.

After telling the user, stop and offer to continue on the local path with pasted ticket text instead.
