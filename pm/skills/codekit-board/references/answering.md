# Answering questions

Read-only. Lead with the answer in one to three sentences, then the supporting list with links. Say what you checked, so a "nothing found" answer can be trusted. The tracker file names the calls for each step.

## Status and progress

Read states, cycles, and dates live. Never answer from an earlier turn if the user asks for "now" or "latest".

| Question | Read | Answer with |
|---|---|---|
| What's in this cycle or sprint? | The current cycle, then its tickets | The cycle's name and dates, counts by state, then the tickets grouped as in progress, not started, and done |
| How is the project going? Are we on track? | Project status (status updates, milestones, epics, or releases, depending on the tracker) and the board's tickets | Status and target date, the latest update in one line, milestones with due dates, counts by state, and the risks below |
| What's blocked? | Unfinished tickets in scope, then full details for in-progress ones to read their links (at most 10) | Each blocked ticket, what blocks it, and who owns the blocker |
| What shipped last week / since X? | Tickets completed in that window | The tickets, newest first, each with a one-line outcome in product language |
| Who is working on X? | A keyword search, then the assignee | Name, ticket, status |

**Risks worth calling out**, only when present:

- A milestone or target date that has passed, or falls within a week, with unfinished tickets
- Tickets blocked by unfinished work
- A cycle ending within 2 days with tickets not started
- A latest status update that is older than two weeks or says "at risk" or "off track"

## Product knowledge

Use the project docs (see SKILL.md, "Project docs").

- **What does it do / can it do X?** Find the activity and capability in the Product Map, and quote the capability and its rules.
  - If it isn't there, check Known limits, then say the map doesn't show it. Don't say the app can't do it: the map can lag.
  - Without a Product Map, use the profile's product context and say it is a summary.
- **What does this term mean?** Give the Glossary definition and its owner. If the term isn't in the Glossary, say so and give the closest entries.
- **Why does it work this way?** Find the Decision Log entry. Give the decision, the reason, and what was rejected, and link the source ticket. The entry is AI-extracted: when the answer will drive a decision, read the source ticket and confirm it.
- **How hard would X be?** Place the change on the Product Map's "How hard is a change?" ladder. Give the rung, which entity or interface it touches, and why. Always add that this is a starting point and a developer confirms it against the code.

## Ticket lookups

1. Run two or three keyword searches on the board, asking for only ID, title, status, assignee, labels or type, last update, and URL. Include the Glossary term and the user's own word when they differ.
2. Fetch full details for the top matches only (at most 3). Read comments only when the user asks for discussion, the latest status, or decisions made in comments.
3. Answer with ID, title, status, assignee, and last update, each linked, plus a one-line summary per ticket. When summarizing one ticket, cover what it delivers, where it stands, open questions in its comments, and what blocks it.

## When the answer points to work

If the answer shows a gap (no ticket exists, a bug in the docs, a capability that's missing), offer to create a ticket. If the user says yes, start `ticket-intake.md` and carry over everything already found, so the board review isn't repeated.
