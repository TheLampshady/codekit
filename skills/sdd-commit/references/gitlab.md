# GitLab

Through the `glab` CLI, run from the repo root, so it works on the project the `origin` remote points at.

## Branch

The issue number that starts the branch name's last path segment, followed by `-`: `123-add-login` and `feature/123-add-login` → `#123`. A leading number alone proves little (`404-page`, `2-step-login`), so check it with `glab issue view <n> --output json`:
- The issue exists and the rest of the segment is the start of its title's slug (lowercase, other characters turned into `-`), which is how GitLab and `sdd-plan` name issue branches: keep it.
- The issue exists but its title doesn't match: ask whether `#<n>` ("<title>") is this branch's ticket.
- No such issue: there's no ID here.
- GitLab can't be reached: keep it and say it's unchecked.

A branch named for another project's issue (`app-123-add-login`) gives no ID here. It comes from the previous message or the conversation, as `group/app#123`.

## Link

The issue's `web_url` from `glab issue view <n> --output json` (add `-R <group/project>` for another project's issue).
