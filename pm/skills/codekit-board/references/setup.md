# Board setup

Run this when there is no board profile, or when the user asks to set up a board or create or update a profile. The goal is a filled-in profile and a Claude Project the team uses, with as few questions as possible. Read the board instead of asking.

## 1. Tracker and board

Pick the tracker as SKILL.md describes. Then find the board, using the tracker file's "Board" section:

- List the choices from the live tracker.
- Ask in one round, recommending the most recently active choice. Use `ask_user_input_v0` if it is available.
- Ask at most 2 questions in this step.

## 2. Read the board

Use the tracker file's calls:

- **Types and labels:** ticket types and labels, or Jira issue types and components, with their descriptions.
- **Workflow:** the states, and whether the team uses cycles and how long they run.
- **Templates:** the ticket templates.
- **Recent tickets:** the 30 most recent. Note:
  - the title pattern
  - which labels or types every ticket gets
  - how epics and parents are used
  - which fields stay blank, such as priority or estimate
- **Project docs:** where they are, in the order from SKILL.md. Note it if they're missing.

## 3. Fill the gaps (at most 3 questions)

Ask only what the board can't show, each with a recommended answer:

- **Starting state:** the state new tickets start in. Recommend the first not-started state when the team uses cycles.
- **Product context:** one or two sentences on what the app is and who uses it, only when there is no Product Map. With a Map, summarize its "Who uses it" and "What users do" sections instead.
- **Inconsistencies from step 2:** for example, two title patterns, or a label group used unevenly.

## 4. Draft the profile

Fill in `board-profile.md`:

- Mark anything inferred from a handful of tickets "(inferred)".
- Delete sections the board doesn't use.
- Record meanings and conventions, not IDs or anything the skill reads live anyway.
- Keep it under about 80 lines.

## 5. Recommend a Claude Project

Show the profile in one code block so it's easy to copy. Then:

> To use this board every time:
> 1. Create a Claude Project named "<board name>".
> 2. Paste the profile into the Project's instructions, or upload it as a file.
> 3. Share the Project with the team, and add example prompts to its description: "What's in this sprint?", "Why does X work this way?", "Make a ticket: …"
>
> Chats in that Project use this board without asking.

You can't create the Project yourself, so don't offer to. If the chat is already in a Claude Project that has no profile, say to paste it into this Project's instructions instead.

## 6. Continue

Use the draft profile for the rest of the conversation, and pick up the request that started setup.

## Update a profile

Do this when the profile doesn't match the live board, for example a missing label or a renamed template, or when the user asks:

1. Re-read the parts of the board that changed.
2. Show only the lines that change.
3. Give the full updated profile to paste.
