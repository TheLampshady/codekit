# SDD Context: Constitution & OpenSpec Config

The procedure behind `/codekit init` Step 6, and the constitution re-sync in `/codekit update`. It gives the project's SDD framework the principles every spec, plan, and task is checked against.

| Framework | Target | Built from |
|-----------|--------|------------|
| SpecKit | `.specify/memory/constitution.md` | The full baseline plus Project Patterns |
| OpenSpec | `openspec/config.yaml` (`context` + `rules`) | A condensed baseline plus Project Patterns |
| Both present | Both targets | The config's context points at the constitution, so it isn't written twice |

## 1. Start from the baseline

The baseline is codekit's constitution, [../resources/principles.md](../resources/principles.md). Every project initialized with codekit starts from the same principles. Only Project Patterns and the filled-in placeholders differ.

Ask one question: **has the project shipped a production release?** If it has, drop *No Backwards Compatibility Before First Release* from the constitution, and its line from the OpenSpec context.

## 2. Check what exists (never overwrite)

| State of the target | Action |
|---------------------|--------|
| Missing | Generate it. |
| **Unfilled template.** SpecKit's constitution still has bracket placeholders (`[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). OpenSpec's config has no `context:` or an empty one. | Treat it as missing and generate it. |
| **Filled in** | Don't replace it. Compare its principles to the baseline by heading or meaning. Offer to **append** only the missing principles and, if there's none, a Project Patterns section. Show the exact text and wait for a yes. A SpecKit amendment bumps the MINOR version. |

## 3. Build Project Patterns

This is the project-specific part of the constitution: the "use X, never Y" rules for this codebase. Only include a pattern you can point to in real files. **An invented pattern is worse than a missing one.**

Sources, in priority order:

1. **`docs/FOUNDATIONS.md`** (from repokit's dockit). Each foundation becomes one pattern: its name, the paths it owns, its invariants, and the import or entry point to use.
2. **`docs/PRINCIPLES.md`, `docs/ARCHITECTURE.md`, `CLAUDE.md` / `AGENTS.md`**: rules already written down.
3. **The code.** Read it, don't guess. Look for:
   - **Shared clients / singletons** (database, storage, auth, LLM, HTTP). Rule: import the shared one, never instantiate your own.
   - **Configuration**: a settings module or class. Rule: read config through it, never the environment directly.
   - **Auth**: a decorator, middleware, or guard. Rule: protected endpoints use it, never custom checks.
   - **Async vs. sync data access**, if the codebase is consistent about it.
   - **Feature structure**: a repeated directory shape (e.g. every agent, route, or module has the same files).
   - **Deployment**: targets in the Makefile / justfile and their config files, and anything that behaves differently locally vs. in production.

Write each pattern as:

~~~~markdown
### <Short name>

<One MUST sentence.>

```<lang>
# CORRECT
<real import / usage from the codebase>

# WRONG
<the thing it replaces>
```

**Where:** `<path>` · **Rationale:** <one line, why it exists>
~~~~

Finish with a **Quick Reference** table (Import · Purpose) of the shared entry points. If nothing qualifies, write `_No project-specific patterns yet. Add them as the codebase establishes them._` rather than padding.

## 4. Fill the baseline placeholders

| Placeholder | Fill with |
|-------------|-----------|
| `PROJECT_NAME` | Repo or package name |
| `QUALITY_GATES` table | One row per hook in the pre-commit config (and its Makefile / `package.json` fix command). If there's no pre-commit config, list the project's lint, format, type-check and test commands. |
| `HOOK_CONFIG_PATH` | e.g. `.config/.pre-commit-config.yaml` |
| `PROJECT_PATTERNS` | Section 3 |
| `RATIFIED_DATE` | Today, `YYYY-MM-DD` |

Then adapt the content:
- **Translate the examples** to the project's primary language, so a Go repo gets Go examples. Keep each WRONG/CORRECT pair's point the same.
- **Drop what doesn't apply.** A repo with no UI drops the Components and Pages rows and the frontend half of Copy-Resilient Tests. A repo with no HTTP API drops the endpoint rows.
- **Name the real tools.** Replace the generic tool hints (network blocking, property-based testing) with what the project uses, or the standard choice for its stack.
- Remove the codekit HTML comment at the top.

## 5. Write it

**SpecKit**: run `/speckit.constitution` with the filled constitution as its input, and ask it to keep the text as given. It writes `.specify/memory/constitution.md` and a Sync Impact Report. If the command isn't available, write the file directly. Remind the user that the Sync Impact Report comment is scratch, to delete before committing.

**OpenSpec**: start from [../resources/openspec-config.yaml](../resources/openspec-config.yaml):
- `PROJECT_SUMMARY`: two or three lines on what the project is.
- `STACK_SUMMARY`: languages, frameworks, data stores, test tools, and deploy targets.
- `FULL_PRINCIPLES_POINTER`: if a constitution or `docs/PRINCIPLES.md` exists, `Full text with examples: <path>`. Otherwise delete the line.
- `QUALITY_GATES_SUMMARY`: the hook names, comma-separated.
- `PROJECT_PATTERNS`: each pattern from Section 3 as **one line** (`Use <x> from <path>; never <y>`). No code blocks: context is paid on every artifact.
- Keep `context` under roughly 8 KB. OpenSpec drops it entirely over 50 KB.

Then validate: `python3 -c "import yaml,sys; yaml.safe_load(open('openspec/config.yaml'))"` (or `openspec validate` if a change exists).

## 6. Report

Name the target file(s), the baseline used, how many project patterns were found and from which source, and anything dropped as not applicable. Suggest committing `.specify/memory/` or `openspec/config.yaml` so the team shares them.
