# Templates: structure and fill rules

## Pick the template

Use the templates the board profile names. Without them, list the tracker's templates (see the tracker file) and pick by name:

- **Feature and Improvement:** the template whose name contains "feature" or "story"
- **Bug:** the one whose name contains "bug"
- **Skip** any template the profile or tracker file says doesn't work through the API, such as Linear form templates.

If no template matches, or the tracker has none (Jira), use the matching skeleton below.

**The live headings win.** Use them exactly, even when they contain typos: codekit, Spec Kit, and other tools read tickets by heading. Never rename, merge, or drop a heading. Fill any heading the live template has that isn't covered below, from what the request gives, using the closest rule here. Leave out instructional suffixes like "(Required)" or "(Optional)".

---

## Feature skeleton (Feature and Improvement)

```markdown
## Overview

## Goals

## Tech Notes

## Out of Scope

## References

## Acceptance Criteria

### Scenario 1

* Given:
* When:
* Then:

### Scenario 2

* Given:
* When:
* Then:
```

### Overview (for product and stakeholders)
Two to four sentences: what the story enables, for whom, and why it matters. Use Glossary terms and no component or API names. Someone who reads only this section should understand the value.

### Goals (for engineers)
Three to six bullets. Each is one capability or expected behavior, stated so it can be verified. Use sub-bullets for detail. Prefer "User can..." or "System..." phrasing. Avoid vague verbs like "support" or "handle" without the actual behavior. More than six bullets means the story should be split.

### Tech Notes
Only what is grounded in the request, the tickets, or the Product Map:

- Stated constraints
- Decisions recorded in related tickets
- Entities and rules from the Product Map, with their section
- The effort rung (`story-sizing.md`)

Don't invent architecture.

End with an **Assumptions** sub-list: anything defaulted instead of asked, and anything the PM skipped. One line each, phrased so an engineer can confirm or reject it. If there is nothing grounded and no assumptions, write `None at this time.`

### Out of Scope
Related work this story deliberately doesn't cover, each with a short reason. Always include any overlap from the context review, with the owning ticket's ID, and the sibling ticket if this came from a split. If nothing applies, write `None identified.`

### References
Related ticket IDs with titles, the parent epic, the Product Map or Glossary sections used, and links the PM gave (designs, docs, threads). If nothing applies, write `None.`

### Acceptance Criteria (for QA)
Two to five Given / When / Then scenarios. The main success path comes first, then at least one edge or error case (empty state, invalid input, permission, failed save). Each Then must be observable. Respect the Product Map's rules for the capability unless the ticket deliberately changes them.

---

## Bug skeleton

```markdown
## Expected behavior

* Given:
* When:
* Then:

## What actually happens

## Steps to reproduce

## Environment
```

When the live Bug template uses other headings for these, fill the same content under its headings.

### Expected behavior
One Given / When / Then describing correct behavior. Where the Product Map states the rule, cite it.

- **Given**: the starting state needed to reproduce (which screen or record, what data exists, the user's role)
- **When**: the exact action
- **Then**: what should happen, stated observably

### What actually happens
A plain description of the broken behavior, then whatever else is known and has no heading of its own:

- **Steps to reproduce** and **Environment**, if the template has no heading for them
- **Frequency**: always, intermittent, or once
- **Evidence**: screenshots, error text, links the reporter gave
- **Assumptions**: anything defaulted rather than confirmed

Leave out items that are unknown and not worth a question, rather than writing "unknown".

### Steps to reproduce
Numbered, concrete steps from a known starting state. If the reporter gave no steps you can reproduce, that is the first clarifying question.

### Environment
Browser, device, and deployed environment, if known.

### Title
A short description of the broken behavior, in the board's title format, for example `[Uploads] PDF upload never finishes`.
