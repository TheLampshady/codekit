# Board conventions

These are the defaults for any board. The board profile (SKILL.md) overrides any of them. Everything else comes from the live board, read every run, never from memory. The tracker file names the calls.

## Type

Every ticket is one of:

| Type | Use when |
|---|---|
| Feature | A new capability users didn't have before |
| Improvement | A change or polish to something that exists, including refactors and debt |
| Bug | Existing behavior is broken or wrong |

The Type picks the template (`template.md`). How it is recorded depends on the tracker:

- **Linear:** usually a Type label group
- **Jira:** the issue type. Story or Task for Feature and Improvement, Bug for Bug.
- **GitHub:** the organization's issue type, or a label

The profile's mapping wins.

## Labels and components

Ignore retired labels and any the profile retires.

- **Single-select groups:** some labels come in groups where a ticket gets at most one, such as Linear label groups or Jira components used as areas. For a group that classifies every ticket, such as Area, pick exactly one. For other groups, pick one only if it clearly applies.
- **Other labels:** add one only when the request clearly calls for it.
- **Two areas:** if the request spans two, pick the area where the user-facing change happens, and mention the other in Tech Notes.
- **Never create** labels or components, and never apply a label that marks epics.
- **Meaning:** use the profile's meanings first, then label descriptions. When a meaning is still unclear, look at how recent tickets use it.

## State

States fall into categories: not started, in progress, done, and canceled. Linear also has triage and backlog.

- **The ticket goes into a cycle:** use the first not-started state (usually Todo). The confirmation step is the review, so the ticket doesn't need triage.
- **The team doesn't use cycles:** use the backlog state, or the tracker's starting state.
- **Always show the state** in the confirmation. The user can change it.

For status questions, read the categories: not started, in progress, and done (shipped).

## Cycles

- Assign the current cycle.
- If it ends within 2 days, say so in the confirmation and offer the next cycle.
- If the team has no cycles, leave the cycle unset and don't mention cycles.

## Titles

Use the profile's format. Without one, look at the titles of the board's recent tickets (from intake step 2):

- If most follow a pattern, such as `[Topic] Few words`, follow it. Use a Glossary term or the Area as the topic.
- Otherwise, use a short sentence-case outcome.

Either way, use at most eight words after any prefix, and describe the outcome, not the task: "Bulk approve requests", not "Add bulk approve button".

## Epics and parents

Use the profile's epic rule. Without one, a ticket is an epic if any of these is true:

- It has the Epic type (Jira) or an epic label.
- It has a title prefix the board uses for epics, such as `[E12]`.
- Several stories in the area are its children or sub-issues.

Then:

- If an open epic covers the story's area and scope, propose it as the parent.
- If the matching epic is done, don't parent to it. List it under References and note that this extends completed work.
- If no epic fits, create the story without a parent.

## Fields left unset

Leave assignee, priority, and estimate empty unless the requester gives them.
