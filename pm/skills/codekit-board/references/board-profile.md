# Board profile

Use the codekit-board skill for anything about this board: status, sprints, tickets, how the product works, or creating a ticket.

<!-- Paste this into the Claude Project's instructions, or upload it as a project file.
     Fill in what your board decides and delete the rest. Anything left out is read from the live board
     or follows the skill's defaults. -->

## Board

- Tracker: <Linear | Jira | GitHub>
- Board: <Linear: team name (key `KEY`) and project | Jira: site and project key | GitHub: owner/repo, and the Project number if one is used>
- Also called: <code names or nicknames people use for the app>
- Feature and Improvement template: <template name or path>
- Bug template: <template name or path>
- Never use: <templates that don't work through the API, such as Linear form templates>
- Project docs: <where the Product Map, Glossary, and Decision Log live, if not the tracker's default>

## Product context

<Two to five sentences: what the app is and who it's for, its main objects and how they nest, and its main screens.
 The Product Map and Glossary win over this when they exist.>

## Types and labels

<How Type is recorded (label group, Jira issue type, GitHub issue type or label), and which value each of Feature, Improvement, and Bug maps to.
 For each label group or component list: its name, whether every ticket gets one, and each value with when to use it.>

Retired (don't use): <labels>

## New tickets

- State: <e.g. Todo>
- Cycle: <current | next | none>
- Leave unset: <e.g. priority, estimate, assignee>

## Titles

Format: <e.g. `[Topic] Few words title`, where the topic is the Area or the main object>

Examples:
- <a real title from the board>
- <another>

## Epics

<How epics are marked (label, issue type, title prefix, ticket range), and when a story gets one as its parent.>

## Notes

<Anything else the team wants followed: template quirks, required sections, extra headings.>
