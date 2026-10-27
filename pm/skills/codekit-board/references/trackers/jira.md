# Jira

Connector: Atlassian (Rovo MCP). Search for "Jira" to load the tools. Jira calls tickets "work items" and projects "spaces", but the tool names still say Issue and Project. Older connector versions use other names, such as `getVisibleJiraProjects` for `listJiraProjects`. Match by purpose.

If the tools take a `cloudId`, get it first from `getAccessibleAtlassianResources`. If there are several sites, ask which one, unless the profile names it.

## Board

A Jira project, by key. Use `listJiraProjects`. Ticket IDs look like `KEY-123`.

## Calls

| Step | Call | Notes |
|---|---|---|
| Search tickets | `searchJiraIssuesUsingJql` | Always scope to `project = KEY`. Ask for only the fields you need (summary, status, assignee, issuetype, labels, components, parent, updated) and set a max result count. |
| Get one ticket | `getJiraIssue` | Includes issue links (blocks, is blocked by, relates to) and parent |
| Comments | `listJiraIssueComments` | |
| Types | `listJiraProjectIssueTypesMetadata` | Type is the issue type. Map Feature and Improvement to Story (or Task, per the profile), and Bug to Bug. Epic is a type: never create one. |
| Fields | `getJiraIssueTypeMetaWithFields` for the chosen type | Shows required fields, components (often used like Area), the sprint field, and parent or epic link |
| Labels | Labels seen on recent tickets | Jira labels are free text, so never invent one. Use only labels already in use. |
| States | `listJiraIssueTransitions` on a recent ticket | A status's category (To Do, In Progress, Done) says not started, in progress, or shipped |
| Current cycle | JQL `project = KEY AND sprint in openSprints()` | The open sprint's name and dates are on its tickets' sprint field. No results means no sprints are in use. |
| Templates | None in the API | Use the profile's template, else the skeletons in `template.md` |
| Project status | Open sprint, epics and their children, and fix versions | Jira has no project status updates. Treat fix versions with release dates as milestones. |
| Project docs | Claude Project files, then Confluence: `searchConfluence` with CQL `title = "Product Map"` (in the profile's space if it names one), then `getConfluenceContent` | codekit doesn't publish to Confluence. Teams copy the docs there or upload them to the Claude Project. If a GitHub connector is available, the repo's `docs/project/` folder also works. |

**Useful JQL:**

- In progress: `statusCategory = "In Progress"`
- Shipped in the last 7 days: `statusCategory = Done AND resolved >= -7d`
- Keyword search: `text ~ "term"`

## Create

1. `createJiraIssue` with:
   - the project key, issue type, and summary (the title)
   - the description as Markdown, unless the tool's schema asks for another format
   - components and labels
   - the parent epic, if confirmed
   - the sprint field, if the create schema accepts it
2. If the sprint wasn't set at create, or the state isn't the starting state from the profile: `transitionJiraIssue`, which moves status and assigns a sprint.
3. Each confirmed relation: `createJiraIssueLink`, with a type from `listJiraIssueLinkTypes` (usually Blocks or Relates).
