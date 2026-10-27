# Linear

Connector: Linear (hosted Linear MCP). Search for "Linear" to load the tools.

## Board

A team plus a project. Use `list_teams`; if there is one team, use it. Then `list_projects` for that team. Ticket IDs look like `ABC-123`.

## Calls

| Step | Call | Notes |
|---|---|---|
| Search tickets | `list_issues` | Filter with `query`, `team`, `project`, `cycle`, `state`, `assignee`, `label`, `updatedAt`. Pass `fields` (e.g. `["id","title","status","assignee","labels","parentId","updatedAt","url"]`) and `limit`. |
| Get one ticket | `get_issue` | Includes relations (blocks, blocked by, related) and parent |
| Comments | `list_comments` | |
| Types and labels | `list_issue_labels` with `includeGroups: true` | Ignore anything with `retiredAt`. Type is usually a label group; groups are single-select. |
| States | `list_issue_statuses` | Each state has a type: `triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled` |
| Current cycle | `list_cycles` with `type: current` (or `next`) | No cycles returned means the team doesn't use them |
| Templates | `list_templates`, then `get_template` | Skip form templates: their fields can't be filled through the API, so they create empty tickets. |
| Project status | `get_project`, `get_status_updates`, `list_milestones` | |
| Project docs | `list_documents` for the project, then `get_document` | codekit publishes the Product Map, Glossary, and Decision Log here by default |
| Create | `save_issue` | One call. See below. |

## Create

`save_issue` with:

- `team` and `project`
- `title`, and `description` (Markdown)
- `labels`, `cycle` (the number), and `state` (the name)
- `parentId`, `blockedBy`, and `relatedTo`, as confirmed

Don't pass `template` together with `description`. The description replaces the template body anyway, and the template would reset the state to Triage.
