# GitLab

Issues, merge requests, specs, and the project docs all live in the GitLab project the `origin` remote points at, through the `glab` CLI and the project's wiki. Any GitLab works: gitlab.com, a self-managed instance by domain or IP address, any tier, Community Edition included. GitLab issues need the code on GitLab too: if the code host is GitHub, say so and ask whether to pick another tracker.

## Checks

The host CLI row already checks `glab`. There's nothing else that's required.

**Optional:**

| Check | Command | If missing |
|-------|---------|------------|
| Wiki | `python3 <plugin>/skills/wiki-docs/scripts/wiki_docs.py check` from the repo root. It reaches the wiki through git, with the login that already reaches the code. | **Needed for SpecKit and no-framework projects**, where the wiki holds the spec, so flag it prominently: `sdd-push` uploads it at PR time, and the `codekit-docs` job reads it. Also used by `project-docs`. Pass on the script's message, which says what to check: the wiki turned on (**Settings → General → Visibility, project features, permissions → Wiki**), access to the code, or, for a wiki that has never had a page, creating its first one (**Plan → Wiki → Create your first page**). |

## Settings

None. The project, its board columns, and its branch name template come from GitLab on every run, so don't write the `team` or `project` keys.

## Project docs

Pages at the root of the wiki: **Product Map**, **Glossary**, and **Decision Log**, next to the issues, where PMs already work. The first build needs the wiki check above to pass.

The `codekit-docs` job keeps them current. On top of the Claude login, it needs a token that can push to the wiki, because a CI job's own token can't:

| Secret | How the user sets it |
|--------|----------------------|
| `CODEKIT_WIKI_TOKEN` | Create a project access token (**Settings → Access tokens**, role Developer, scope `write_repository`). On gitlab.com's Free tier, which has no project access tokens, use a personal access token with `write_repository`. Then `read -rs t && printf %s "$t" \| glab variable set CODEKIT_WIKI_TOKEN --masked --protected; unset t`, pasting the token when the cursor waits. |
