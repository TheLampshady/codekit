# Story sizing

Every ticket this skill creates is a story. A story-sized ticket:

- Delivers **one user-facing outcome** a PM could demo or a user would notice (or, for platform work, one capability another story builds on)
- Can be built, reviewed, and shipped **within one cycle**
- Is **independently testable**: QA can verify it without another unfinished ticket
- Lives mostly in **one area**

## Use the Product Map's effort ladder

When the Product Map is available, place the change on its "How hard is a change?" ladder:

| Rung | What it means for sizing |
|---|---|
| 1. No new data | Usually one story. If it is only copy or spacing, see "too small" below. |
| 2. A new attribute | Usually one story. |
| 3. Relaxes something the model assumes | Often more than one cycle. Look for a split: the model change, then the user-facing outcomes on top of it. |
| 4. A new entity or relationship | Usually needs a split. The entity is a shared dependency, so split it out as a platform story and link it with `blockedBy`. |
| 5. Changes an interface outside parties use | Flag it in the confirmation: it needs coordination beyond this team. Split out the interface change. |
| 6. A new third-party integration | Usually its own story first (connect and authenticate), then the stories that use it. |

The rung is a starting point, not an estimate. Record it in Tech Notes ("Product Map effort: rung 2, a new attribute on Request") so engineers can confirm or correct it.

## Signals a request is too big (recommend a split)

- It contains "and also", "plus", or more than one verb-object outcome ("add X and let admins Y")
- Goals would need more than 6 bullets, or Acceptance Criteria more than 5 scenarios
- It touches two or more Product Map activities with separate user flows
- It mixes new capability with a fix to existing behavior (split into a Feature or Improvement plus a Bug)
- It needs backend or data model work that other stories would also depend on (split that piece out and link it with `blockedBy`)
- It is rung 4 or above

## Signals a request is too small (fold it in)

- A single copy, color, or spacing tweak with no change in behavior. Suggest adding it to a related open ticket, or keep it as a small Improvement if nothing related is open.

## How to split

Split by user outcome, not by layer. "Bulk select requests" and "Bulk approve requests" are good stories. "Build bulk approve API" and "Build bulk approve UI" are not, unless the API is a real shared dependency.

Recommend two tickets where two cover it. Give each a title, a Type, and a one-line outcome, and say which comes first if order matters.
