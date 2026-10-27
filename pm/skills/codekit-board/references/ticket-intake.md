# Ticket intake

Turn a rough product request into a build-ready, story-sized ticket that engineers can pick up and that codekit's `sdd-plan` (and GitHub Spec Kit's `/specify`) can plan from. Close the gap between a short PM request and a buildable ticket, without inventing facts.

Read these before drafting:

- The board profile, if there is one (SKILL.md)
- The tracker file in `trackers/`: the calls for each step
- `board-conventions.md`: the defaults for types, labels, states, cycles, titles, and epics
- `story-sizing.md`: what a story-sized ticket is and when to split
- `template.md`: section-by-section fill rules, plus fallback skeletons

If the user says "dry run", "preview only", or "don't create it", do everything except creation.

## Offline mode (no tracker connected)

- Start the reply with the warning from SKILL.md. Add that the ticket was not checked against the board and was not created.
- Still do steps 1, 3, 4, and 5 using the skeletons in `template.md` and the board profile. Skip step 2, and say so in the warning. If the user pasted or attached the project docs, use them.
- Instead of creating the ticket, write it to a Markdown file named `<key>-draft-<short-slug>.md` (or `ticket-draft-<short-slug>.md` with no key), then present the file. Start it with a header block (title, suggested type and labels, "Cycle: current") followed by the description.

## 1. Read and size the request

Identify the actor, what they need to do, why it matters, and any constraints or examples. Decide the Type: Feature, Improvement, or Bug (see board conventions).

Then check the size against `story-sizing.md`. Every ticket this skill creates is one story: one user-facing outcome that can be built, tested, and shipped within one cycle.

- If the request bundles independent asks or is epic-sized, recommend a split. List the proposed tickets (working title, Type, one-line outcome each) and ask the user to confirm. Recommend two where two cover it.
- After the user confirms, run steps 2 to 7 for each ticket. Ask clarifying questions for all of them together, so the total stays within the 5-question budget. Show all confirmations together for one go-ahead.

## 2. Review the context

Fetch live board data every run, because labels, templates, and cycles change. Never rely only on the board profile.

**Board** (the tracker file names the calls):

1. Types and labels, ignoring retired ones
2. The current cycle, if the team uses cycles. If none is current, use the next one and tell the user.
3. States
4. The template you'll use (`template.md`)
5. Recent tickets on the board: up to 100, with only ID, title, status, labels or type, parent, and URL
6. Two or three keyword searches with the same fields, using the request's distinctive nouns and their Glossary terms
7. Full details for the top 3 candidates that look related only. Pulling every description wastes tokens and rarely changes the outcome.

**Project docs** (Product Map and Glossary; see SKILL.md):

- **Glossary**: map the user's words to the team's terms. A term that maps to two entries, or to none, is a candidate clarifying question.
- **Product Map**: find the activity and capability the request touches.
  - If the capability already exists as asked, the request is likely an Improvement or a Bug, or it isn't needed at all.
  - If a Known limit covers it, cite the limit.
  - If its Rules contradict the request, that is a conflict.
  - Place the change on the "How hard is a change?" ladder. The rung feeds sizing (`story-sizing.md`) and Tech Notes.

Don't read the Decision Log for intake. Prior decisions come from the tickets themselves.

Classify each relevant ticket:

- **Already exists**: the same outcome is already ticketed, in any status other than canceled. Stop and reply with the ticket's ID, title, status, and link, plus one sentence on how it matches. Offer a new ticket only if the user says the request is distinct. If the match is done, say the feature should already exist and suggest a Bug or Improvement instead.
- **Overlap**: shares scope. Narrow this ticket and list the overlap in Out of Scope with the owning ticket's ID.
- **Conflict**: contradicts a decision in another ticket, or a rule in the Product Map. Raise it as a clarifying question.
- **Dependency**: needs another ticket done first. Plan a "blocked by" link.
- **Parent epic**: an open epic covers this area (see board conventions). Plan to set it as the parent.
- **Related**: useful context. Plan a "related" link.

Keep a running **Shaped by** list of every ticket and doc section that informed the draft, and what each contributed (scope boundary, prior decision, terminology, existing rule, effort rung).

## 3. Draft the ticket

Fill every section of the chosen template following `template.md`.

- Never invent technical detail, metrics, designs, or decisions. Record anything unknown and not worth a question as an assumption, so it is visible and can be reviewed.
- Use Glossary terms throughout, and the title format from the profile or board conventions.
- Pick the type and labels per the profile and board conventions. This skill doesn't create epics. If the user asks for one, explain that and offer to break the work into stories.

## 4. Clarify (at most 5 questions)

Before asking, check whether the request, the board, the project docs, the profile, or a reasonable default already answers the gap. Rank the remaining gaps by how much the answer would change scope, acceptance criteria, labels, or size, and ask only the top ones. Five is a ceiling, not a target. Ask none if the request is clear.

Ask about gaps in this order:

1. Conflicts from step 2, with tickets or with Product Map rules
2. Size: anything that decides one story or two
3. Terminology: a term that maps to more than one Glossary entry, or to none
4. Who the actor is, if ambiguous (use the Product Map's "Who uses it" roles as options)
5. The scope boundary (in vs. out)
6. Expected behavior on success (for bugs: exact steps and what actually happens)
7. Edge cases or error behavior
8. Type or labels, if genuinely ambiguous

Give every question a recommended answer and a short reason, grounded in the docs or the board wherever possible ("Product Map: only Admins can archive a project. Keep that?"). If `ask_user_input_v0` is available, use it with 2 to 4 options per question, recommended option first. It takes at most 3 questions per call, so use two rounds for 4 or 5. Otherwise ask in a short numbered list.

If the user says "skip" or "use your judgment", or leaves a question unanswered, apply the recommended answer and record it as an assumption.

## 5. Confirm

Show one short confirmation before anything is written to the tracker. **Don't print the full description.** The PM is checking that the request was understood and what it commits the team to, not proofreading a ticket. Keep it to about 15 lines, in the PM's terms, in this order:

**What you're asking for**: two or three plain sentences. Who gets what, what changes for them, and what this ticket deliberately leaves out.

**Impact**: who is affected, what they can do afterward that they can't now, and which Product Map activities or capabilities it touches. Say if it changes an existing rule or Known limit.

**Effort**: the Product Map rung with a one-line reason, and whether it fits one cycle. This is a starting point a developer confirms, never an estimate in days or points.

**Risk**: only what is grounded in the board or docs, one line each:
- a conflict or overlap with another ticket or rule, with its ID
- a dependency or "blocked by" that could delay it
- rung 5 or 6: coordination outside the team, or a third-party integration
- an assumption whose answer would change scope

**Cost**: beyond build effort, only what the request or docs name, such as a paid third-party service, new infrastructure, or message volume. If nothing is named, write "No cost beyond build effort known". Never guess a dollar figure.

**Open assumptions**: defaults you applied instead of asking, each one line, so the PM can reject any.

**Ticket card**, one line each: title · Type and labels · cycle (name and dates), state, and board · parent and links with ID and title.

If any of Impact, Effort, Risk, or Cost has nothing grounded, say so in a few words instead of padding it.

Ask for a single go-ahead. With `ask_user_input_v0`, offer: Create it / Ask a question / Cancel. A question can be about the summary, the draft, or a change the PM wants. Answer it, apply any edit, re-show only what changed, and ask again. Never print the description in the confirmation, even on request: the PM reviews the real ticket in the tracker after it is created. Creating a ticket is visible to the whole team, so never skip this step.

When a split created several tickets, show one summary for the set, with a card line for each ticket, and add Impact, Effort, and Risk per ticket only where they differ. Ask once.

## 6. Create the ticket

Follow the tracker file's "Create" section. Pass:

- The board, title, and description (the completed template as Markdown)
- The type and labels
- The cycle and state, per the profile and board conventions
- The parent and links shown in the confirmation, and no others
- Leave assignee, priority, and estimate unset unless the user gave them

If the create call fails on a label, type, cycle, or state, refetch that list once, correct the value, and retry. If it fails again, report the error plainly and write the offline Markdown file, so the draft isn't lost.

If the ticket was created but a follow-up call failed (cycle, state, parent, or a link), don't create it again. Return the link, and say what is still missing so the user can set it in the tracker.

## 7. Return the link and what shaped it

Lead with the link and ask the PM to review the ticket in the tracker, then the essentials, then the Shaped by list:

> Created **ABC-123**: [Approvals] Bulk approve requests
> https://...
> Please review it in the tracker and edit anything that's off.
> Cycle 14 (Oct 20 to Nov 2) · Feature · Approvals · Parent: ABC-40
>
> **Shaped by**
> - [ABC-40](url) Approvals epic: set the parent and scope
> - [ABC-88](url) Approval notifications: owns email on approve, so it's out of scope here
> - Product Map, Approvals: "Approvers act only on their own team's requests" kept as a rule
> - Glossary: "request" means an Approval Request, not a Ticket

When a split created several tickets, list every link first, ask for the review once, then give one combined Shaped by list.
