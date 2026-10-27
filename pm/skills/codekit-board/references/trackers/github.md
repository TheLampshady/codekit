# GitHub

Connector: the GitHub MCP server (`https://api.githubcopilot.com/mcp/`), added in Claude.ai as a custom connector. Search for "GitHub issues" to load the tools. If the GitHub tools available can't search or create issues, say so, answer from any attached files, and use offline mode for tickets. Claude.ai's built-in GitHub integration attaches repo files to a chat, but isn't an issue connector.

## Board

A repo (`owner/repo`), and optionally a GitHub Project for status and iterations. Use the profile, or ask for the repo, and list the owner's Projects with `projects_list` (`list_projects`). Ticket IDs look like `#123`, or `owner/repo#123` across repos.

## Calls

| Step | Call | Notes |
|---|---|---|
| Search tickets | `search_issues` | Query like `repo:owner/repo is:issue <terms>`. Add `is:open`, `label:`, or `updated:>=YYYY-MM-DD` as needed. |
| List tickets | `list_issues` | Filter by `state`, `labels`, and `since` |
| Get one ticket | `issue_read` (`get`, `get_comments`, `get_sub_issues`, `get_parent`, `get_labels`) | |
| Types | `list_issue_types` | Organization issue types (such as Bug, Feature, Task). Without them, Type is a label. |
| Labels | `list_label` | |
| States | Open or closed, plus the Project's Status field (`projects_list` `list_project_fields`) | The Status field's options say not started, in progress, or done |
| Current cycle | The Project's iteration field (`list_project_fields`) | Use the iteration whose dates include today. No Project, or no iteration field, means no cycles. |
| Templates | `get_file_contents` on `.github/ISSUE_TEMPLATE/` | Markdown templates: use their headings. Issue forms (`.yml`): use each field's label as a `###` heading, which is how GitHub shows a submitted form. |
| Project status | `projects_list` (`list_project_items`, `list_project_status_updates`), and issues' milestones | |
| Project docs | `get_file_contents` on `docs/project/product-map.md`, `glossary.md`, and `decision-log.md` | Where codekit writes them when a repo doesn't use Linear |
| Create | `issue_write` (`create`), then follow-ups | See below |

## Create

1. `issue_write` with `method: create`:
   - owner, repo, title, and body (Markdown)
   - labels, the issue type if the org uses types, and a milestone if the profile asks for one
2. Parent epic: `sub_issue_write` (`add`) on the parent issue.
3. Cycle and state: `projects_write` (`add_project_item`), then `update_project_item` to set Status and the current iteration.
4. Relations: GitHub has no dependency call here. Put "Blocked by #12" and "Related to #34" under References in the body.
