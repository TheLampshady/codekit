# Product Map

What this app does today, in product language. It's generated from the code as changes ship, so don't edit it here: the next update overwrites hand edits. To change a name or a definition, edit the Glossary. To report something wrong, file a ticket. Each entry links the code it was read from.

**How hard is a change?** Find the rung it lands on, using Core entities and Interfaces below:

1. **No new data:** screens, copy, or a rule over data that already exists. Small.
2. **A new attribute** on an existing entity. Small to medium.
3. **Relaxes something the model assumes** (one becomes many, a new state). Medium to large.
4. **A new entity or relationship.** Large.
5. **Changes an interface outside parties use** (marked *contract*). Large, and needs coordination.
6. **A new third-party integration.** Varies, often large.

This is a starting point for prioritizing, not an estimate. A developer confirms it against the code.

## Who uses it

<!-- The kinds of users, in product terms, and what each is trying to get done. -->
- **<Role>** — <what they use the app for>.

## What users do

<!-- One section per activity, in the order a user meets them. Under each, the capabilities a user would name.
     Capability names describe the what, not the how, and stay the same across refactors. -->

### <Activity>

<one sentence on what the user is trying to get done here>

- **<Capability>** — <what the user can do>. Rules: <limits, permissions, state changes, as facts a PM could repeat to a customer>. Where: <screen or command>. (`<path>`)

## Core entities

<!-- The main things the app stores, in business terms. No column names or types. -->
- **<Entity>** — <what it is>. Has: <key attributes, in business terms>. <Cardinality, e.g. "Belongs to one Customer; has exactly one shipping address; has many Line items">. States: <a → b → c, or d>. (`<path>`)

## Interfaces

<!-- What the app exposes, grouped by capability, and who consumes each. Mark anything outside parties depend on as a contract. -->
- **<Interface>** — <what it exposes>. Used by: <own web app | mobile app | partners | webhooks>. <*contract* if outside parties depend on it>. (`<path>`)

## Integrations

<!-- Third-party services the app talks to and what it uses each one for. -->
- **<Service>** — <what for>. (`<path>`)

## Known limits

<!-- User-visible gaps: half-built features, flags that are off, hard caps, documented TODOs. -->
- <limit>. (`<path>`)

---

Synced to commit <sha> on <YYYY-MM-DD>.
