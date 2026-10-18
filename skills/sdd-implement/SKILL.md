---
name: sdd-implement
description: 'Implement a planned feature on its branch. Detects SpecKit or OpenSpec and runs its task generation and implementation (speckit tasks/implement/converge, OpenSpec apply), or follows the hand-written plan when there is no framework. Then runs the project''s tests and linters. Use when asked to: implement the feature, implement the plan, start implementation, build it, run implementation.'
user-invocable: true
disable-model-invocation: true
---

# SDD Implement

Runs the framework's implementation of the plan `sdd-plan` produced, then the project's checks. It doesn't commit.

## 1. Implement

| Framework | Detected by | Run |
|-----------|-------------|-----|
| SpecKit | `.specify/` | `/speckit.tasks` if there's no `tasks.md`, then `/speckit.implement`, then `/speckit.converge` |
| OpenSpec | `openspec/` | `/opsx:apply <change-id>` |
| None | neither | the plan in `specs/<ticket>/plan.md` |

- **SpecKit converge:** if converge appended a `Convergence` phase to `tasks.md`, run implement and converge again, at most two rounds. Anything still open is a gap. An older SpecKit without converge skips it.
- **OpenSpec change:** the one in `openspec/changes/` whose id contains the branch's ticket ID, or the only active one in `openspec list`. Ask if it's ambiguous. `sdd-pr` archives it.
- **None:** `<ticket>` is the folder under `specs/` matching the branch's ticket ID or slug. Implement in small steps, following the project's documented conventions (`docs/FOUNDATIONS.md`, `CONTRIBUTING.md`, `AGENTS.md`) and the code around each change.
- **A framework command is missing:** stop and suggest `/codekit update`. Don't do the framework's work by hand.

## 2. Validate

Run the project's own tests, linters, and type checks: whatever its `Makefile`, `justfile`, `package.json`, `pyproject.toml`, or CI config defines, plus `pre-commit run --files <changed files>` if it has a pre-commit config. Fix failures your change caused. Report failures that were already there (check with `git stash`) and leave them alone.

End with the check results (failure output verbatim) and any gaps. Next is `/sdd-commit`.
