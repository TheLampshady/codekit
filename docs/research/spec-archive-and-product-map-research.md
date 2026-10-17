# Spec Archive, ADRs, and a Generated Product Map — Research

**Written:** 2026-10-17
**Original request:** What artifacts to keep after SpecKit work and where to store them, so that devs keep decision history (complexity, architecture choices) and non-technical PMs get an accurate, askable picture of the app and can create tickets, given that the code is on GitHub with few seats and the team already uses Linear.
**Provenance:** Sourced claims cite primary sources inline; everything under Hypotheses is unmeasured. This doc stands alone.

## Summary

### Goal

Pick the post-merge artifacts (what's kept, what's thrown away, where each one lives) so engineers keep the "why" behind architecture choices and PMs can ask about the app and file tickets without GitHub seats. For a mostly single-repo setup that sometimes spans two.

### Claims

14 findings, 4 hypotheses

**Spec lifecycle and ADRs.** What happens to spec, plan, and task files once a feature ships, and how teams record the reasoning behind a technical choice in a short, permanent note.

*Findings (sourced):*
- [Spec Kit leaves artifact lifecycle to the team, and its "living spec" model risks losing rationale](#f-speckit-lifecycle)
- [OpenSpec keeps "how it behaves today" separate from in-flight changes, and archiving merges one into the other](#f-openspec-archive)
- [ADRs are small, immutable decision files kept next to the code, with later decisions superseding earlier ones](#f-adr-format)

*Hypotheses (unsourced):*
- [**H1**](#h1): After merge, only the reasoning is worth keeping. A short decision record pulled out at merge time keeps it, and the spec, plan, and tasks can go.

**PM access without GitHub seats.** How people who don't work in the code can read about the app, ask questions, and file work without each needing a paid GitHub account.

*Findings (sourced):*
- [Anyone with access to a private org repo uses a paid GitHub seat, read-only included](#f-github-seats)
- [Claude Projects' GitHub sync depends on each user's own repo access and syncs manually](#f-claude-project-github)
- [Linear Code Intelligence answers code questions in Linear and can be opened to members without GitHub access](#f-code-intelligence)
- [Linear Agent reads workspace documents and creates issues from chat](#f-linear-agent)
- [Linear pricing: Free has unlimited members and caps issues; Business ($16) unlocks Code Intelligence](#f-linear-pricing)
- [DeepWiki generates a steerable repo wiki, but it's a separate tool and its summaries can be wrong at the edges](#f-deepwiki)

*Hypotheses (unsourced):*
- [**H2**](#h2): PMs need a curated list of what the product does, alongside a chat that can answer questions about the code.

**Product map generation and drift.** Keeping a plain-language description of the app in step with the code automatically, and noticing when the code and the recorded intent disagree.

*Findings (sourced):*
- [claude-code-action runs prompt-driven automation from any workflow event](#f-cca-automation)
- [Updating docs from the merged diff works and costs little, but misses implied changes](#f-diff-on-merge)
- [Agent-written docs should land as a reviewable PR, checked by a second pass](#f-reviewable-pr)
- [Code-coupled docs can be checked in CI and sorted into up to date, out of sync, and outdated](#f-swimm-states)
- [No published pipeline opens an issue when docs and code disagree; they open PRs or fail the build](#f-no-issue-pipeline)

*Hypotheses (unsourced):*
- [**H3**](#h3): A map generated only from code can't really drift. The only disagreement worth a person's attention is between the code and a recorded decision.
- [**H4**](#h4): Updating from each diff slowly falls behind, so a full rebuild is needed now and then.

## Key findings

- <a id="f-speckit-lifecycle"></a>**Spec Kit leaves artifact lifecycle to the team, and its "living spec" model risks losing rationale** ([Spec Kit: Spec Persistence Models](https://github.github.com/spec-kit/concepts/spec-persistence.html)): Spec Kit names three models: *flow-back* (all artifacts stay editable; risk is "silent divergence"), *flow-forward* (completed feature dirs are "treated as immutable"; risk is fragmented context), and *living spec* (`spec.md` is the contract, and plan/tasks are "disposable derivations rather than permanent sources of truth"; risk is "losing useful implementation rationale if derived artifacts are discarded"). The page calls the choice "a team convention, not a CLI setting." Spec Kit has no archive command.
- <a id="f-openspec-archive"></a>**OpenSpec keeps "how it behaves today" separate from in-flight changes, and archiving merges one into the other** ([OpenSpec glossary](https://openspec.dev/docs/glossary)): `openspec/specs/<capability>/spec.md` describes "how one capability behaves today"; a change is a folder under `openspec/changes/<name>/` with delta specs (`ADDED`/`MODIFIED`/`REMOVED`/`RENAMED`). Archive means "merge its deltas into the main specs and move its folder to `openspec/changes/archive/`." The archive keeps every planning artifact. Nothing is distilled.
- <a id="f-adr-format"></a>**ADRs are small, immutable decision files kept next to the code, with later decisions superseding earlier ones** ([Red Hat: Architecture decision records](https://redhat.com/en/blog/architecture-decision-records)): The format goes back to Michael Nygard's 2011 "Documenting architecture decisions" (Title, Status, Context, Decision, Consequences). Records are stored as text files in version control. An accepted record isn't edited; a changed decision gets a new record that references the old one. *Secondhand account of Nygard's post; the original article was not fetched here.*
- <a id="f-github-seats"></a>**Anyone with access to a private org repo uses a paid GitHub seat, read-only included** ([GitHub Docs: GitHub license users](https://docs.github.com/en/billing/reference/github-license-users)): On Team, "Outside collaborators on private repositories owned by your organization, excluding forks" consume a license, as do all org members. On Enterprise Cloud, internal repos count as well. The docs list no exemption for read-only permission.
- <a id="f-claude-project-github"></a>**Claude Projects' GitHub sync depends on each user's own repo access and syncs manually** ([Claude Help: Using the GitHub integration](https://support.claude.com/en/articles/10167454-using-the-github-integration)): Adding a private repo needs the user's GitHub auth (or an org-admin approval of their request), and a user who loses repo access can no longer view its contents in the project. Sync happens through a "Sync" / "Sync now" button. The article doesn't describe automatic sync. It only syncs file contents, not PRs or history.
- <a id="f-code-intelligence"></a>**Linear Code Intelligence answers code questions in Linear and can be opened to members without GitHub access** ([Linear Docs: Code Intelligence](https://linear.app/docs/code-intelligence)): It "lets Linear Agent answer questions about your codebase" (⌘/Ctrl+J). Setup is the GitHub integration with code access, then enabling it in Settings › AI & Agents. It's permission-aware by default, and admins can "Extend access to all members" so people without GitHub access can use it, scoped to all or selected repos. It's available on Business and Enterprise and "not available to guest users." The docs page says nothing about data handling. The [changelog (2026-05-14)](https://linear.app/changelog/2026-05-14-code-intelligence) describes it as public beta and free during the beta, *per a search summary of the changelog; not fetched directly.*
- <a id="f-linear-agent"></a>**Linear Agent reads workspace documents and creates issues from chat** ([Linear Docs: Linear Agent](https://linear.app/docs/linear-agent)): It works over "your existing workspace data," including "documents," and can "Create and update work like issues, projects, milestones and initiatives." It's on by default, limited to what the user can already see, and reachable in Slack and Teams. Plan coverage ("all plans include an amount of Agent usage") comes from the [launch changelog](https://linear.app/changelog/2026-03-24-introducing-linear-agent), *via search summary; not fetched directly.*
- <a id="f-linear-pricing"></a>**Linear pricing: Free has unlimited members and caps issues; Business ($16) unlocks Code Intelligence** ([Linear pricing](https://linear.app/pricing)): Free is unlimited members, 2 teams, and 250 issues. Basic is $10 and Business is $16 per user/month, billed yearly. Business adds guests, Linear Asks, and Code Intelligence. Whether Free includes API access isn't legible on the page.
- <a id="f-deepwiki"></a>**DeepWiki generates a steerable repo wiki, but it's a separate tool and its summaries can be wrong at the edges** ([Devin Docs: DeepWiki](https://docs.devin.ai/work-with-devin/deepwiki)): Wikis are generated when repos are connected to Devin, and a `.devin/wiki.json` (`repo_notes`, `pages`) replaces the default page planning with exactly the pages you list. Higher effort levels need a subscription or credits. A [2026 third-party guide](https://mcp.directory/blog/deepwiki-mcp-complete-guide-2026) says summaries "can be wrong on the edges" and the index lags commits. *That guide is a secondary source.*
- <a id="f-cca-automation"></a>**claude-code-action runs prompt-driven automation from any workflow event** ([anthropics/claude-code-action](https://github.com/anthropics/claude-code-action)): It detects "executing automation tasks with explicit prompts" alongside @claude mentions, configured through `prompt` and `claude_args` inputs. Patterns live in its [custom automations guide](https://github.com/anthropics/claude-code-action/blob/main/docs/custom-automations.md).
- <a id="f-diff-on-merge"></a>**Updating docs from the merged diff works and costs little, but misses implied changes** ([Doc Drift Detection in CI, 2026-03-06](https://understandingdata.com/posts/doc-drift-detection-ci/)): This is Dosu's production workflow. On a merged PR it feeds the diff, `docs/`, and a code-to-docs mapping to claude-code-action, which opens a follow-up docs PR or logs why none is needed. Stated limits: "It catches what is explicit and misses what is implied"; each run "starts fresh"; it costs "roughly $0.50 to $2.00" per run. The team removed path filters because they skipped config/template changes that affected docs. *Practitioner write-up; the numbers are theirs.*
- <a id="f-reviewable-pr"></a>**Agent-written docs should land as a reviewable PR, checked by a second pass** ([Agent Patterns: Continuous Documentation](https://agentpatterns.ai/workflows/continuous-documentation/)): "The output must be a reviewable PR rather than an autonomous update." It recommends a generator–verifier split and warns that "a plausible-looking PR that aligns with the wrong mental model is worse than acknowledged drift." Other risks it names: review fatigue, churn between equivalent phrasings, and style erosion. *Practitioner pattern catalogue, not measured.*
- <a id="f-swimm-states"></a>**Code-coupled docs can be checked in CI and sorted into up to date, out of sync, and outdated** ([Swimm: benefits of code-coupled documentation](https://docs.swimm.io/new-to-swimm/benefits-of-code-coupled-documentation)): Docs reference specific snippets and paths. A CI check runs per commit. Trivial changes auto-sync, and substantial ones fail the check and are flagged for a person. *Vendor documentation.* This is the precedent for keeping "can be auto-fixed" separate from "needs a human."
- <a id="f-no-issue-pipeline"></a>**No published pipeline opens an issue when docs and code disagree; they open PRs or fail the build** *(absence claim)*: I searched for LLM doc-drift CI that files issues. Docverity fails the build, the Dosu workflow and agentpatterns.ai open PRs, and DriftGuard is a hackathon dashboard. None file tickets.

## Hypotheses

<a id="h1"></a>**H1: After a feature merges, the only durable value in its spec/plan/tasks/research is the decision rationale, and a short decision record extracted at merge time captures enough of it that the rest can be deleted without anyone later needing it** · *open* · added 2026-10-17
- **Builds on:** [Spec Kit's rationale-loss risk](#f-speckit-lifecycle), [ADR format](#f-adr-format)
- **Cuts against:** [OpenSpec archive](#f-openspec-archive), which keeps every artifact, on the assumption that the full record is worth its weight.
- **Unsourced because:** I searched for studies on whether archived SDD specs get re-read after merge and found none. The ADR literature argues for recording "why" but doesn't test whether that's enough without the surrounding plan.
- **Check:** For three months, log every time someone (human or agent) goes looking for why something was built a certain way. Tally how many the ADRs answered, how many needed git history or the deleted spec, and how many went unanswered. Refuted if more than about 1 in 5 needed the deleted artifacts.

<a id="h2"></a>**H2: Chat-style Q&A over a codebase answers point questions well but can't reliably list everything the product does (all screens, all integrations, all business rules), so PMs also need a curated, code-derived inventory written in product vocabulary** · *open* · added 2026-10-17
- **Builds on:** [Code Intelligence](#f-code-intelligence), [Linear Agent reads documents](#f-linear-agent)
- **Unsourced because:** I searched for evaluations of DeepWiki, Code Intelligence, or similar tools on enumeration tasks and found none. The DeepWiki guide's "wiki-first is good at orientation" is close, but it's a different claim.
- **Check:** Write 10 inventory questions ("list every user-facing screen," "every third-party integration," "every rule that blocks checkout") and hand-build the true answers. Ask Linear Agent each one twice: once with Code Intelligence only, and once with the product map published as a Linear document. Validated if the map-backed answers are clearly more complete. Refuted if Code Intelligence alone matches them.

<a id="h3"></a>**H3: A product map that is only ever produced from code cannot meaningfully drift from it; regenerating is the fix. The drift worth a person's attention is between the code and recorded intent (an accepted decision record), because only a person can say which side is wrong** · *open* · added 2026-10-17
- **Builds on:** [diff-on-merge updates](#f-diff-on-merge), [Swimm's auto-sync vs. flagged split](#f-swimm-states)
- **Cuts against:** [the absence of issue-filing pipelines](#f-no-issue-pipeline). Every published workflow assumes the code is right and fixes the doc, which this position says is wrong for decision conflicts.
- **Unsourced because:** I searched for CI that tells "regenerate the doc" apart from "escalate a decision conflict" and found nothing beyond Swimm's snippet-level split.
- **Check:** Run the map workflow for 30 merges. Classify every item it flags as either (a) the map was simply out of date or (b) code contradicts an ADR. Validated if (b) items are rare and each one actually needed a decision. Refuted if (b) items are mostly false alarms, or if (a) items keep surviving regeneration.

<a id="h4"></a>**H4: A map maintained only by per-merge diff updates accumulates implied drift (changes no single diff mentions), so a periodic full regeneration from the whole codebase is needed to keep it accurate** · *open* · added 2026-10-17
- **Builds on:** [diff-on-merge "misses what is implied"](#f-diff-on-merge)
- **Unsourced because:** Dosu states the limitation but doesn't measure how fast it builds up. I found no measurements.
- **Check:** After four weeks of diff-only updates, run a full regeneration and diff it against the maintained map. Validated if there are substantive differences (features, rules, or integrations added, missing, or wrong, not just wording). Refuted if the differences are only phrasing.

## How this applies to your request

**What to keep.** Your instinct to not archive every spec lines up with Spec Kit's own framing ([lifecycle](#f-speckit-lifecycle)): plan and tasks are derivations, and the one thing you lose by discarding them is rationale. [H1](#h1) is the bet that an ADR pulled out at merge captures that rationale and that nothing else is worth keeping. It's cheap to try, because the spec is still in git history if the bet turns out wrong. OpenSpec's model ([archive](#f-openspec-archive)) is the alternative: keep everything and also maintain a hand-curated "how it behaves today" spec. That's close to a product map, but it's written by devs in requirement language, and it's exactly the kind of doc you've seen go stale.

**Where PMs live: easiest and best supported.** The seat constraint rules out anything that reads GitHub as the PM ([seats](#f-github-seats), [Claude Projects](#f-claude-project-github)). Linear is the strongest fit because it already does all three things you listed: PMs create tickets there, [Code Intelligence](#f-code-intelligence) answers questions about the code with no GitHub account needed (when "Extend access to all members" is on), and [Linear Agent](#f-linear-agent) reads Linear documents and can turn a conversation into an issue. That makes the product map an *addition* to Linear's code Q&A rather than the only way PMs see the code. [H2](#h2) is why the map is still worth building, and also the test that would tell you to skip it. The catch is cost: Code Intelligence needs Business ([pricing](#f-linear-pricing)), which is $16 per Linear member. That's usually cheaper than GitHub seats for every PM, but check it against your headcount. Google Drive or DeepWiki would add a tool PMs don't otherwise open ([DeepWiki](#f-deepwiki)).

**Drift, which you asked me to dig into.** Your instinct ("detect drift on update and use it to update the map") is what the published workflows do ([diff-on-merge](#f-diff-on-merge)). For the map itself, drift and updating are the same step: every merge feeds the diff to Claude, and Claude edits the map. [H3](#h3) narrows the "drift check" idea from the earlier summary you pasted: there's no point filing a ticket because the map is stale, since the next run fixes it. The only conflict worth a ticket is code contradicting an accepted ADR, because the workflow can't tell whether the code or the decision is wrong. Everything else is just a map update. Two guardrails come from practitioners ([reviewable PR](#f-reviewable-pr)): the map change goes through a PR that someone glances at, because a confidently wrong map is worse for PMs than a stale one, and diff-only updates miss implied changes, which is why [H4](#h4) adds a periodic full rebuild.

**Scale.** At one repo, occasionally two, and roughly $0.50–$2 per run ([diff-on-merge](#f-diff-on-merge)), running per merge is affordable without batching. For the two-repo case, each repo can keep its own map file and publish to the same Linear project. How to merge them is an open question, not something the research settled.

## Actions

- **A1: Extract an ADR at PR time in `skills/sdd-pr/SKILL.md`.** Add a step before the PR opens: read the feature's `spec.md` / `plan.md` / `research.md` (or OpenSpec `proposal.md` / `design.md`), and write the architecture or complexity choices to `docs/decisions/NNNN-<slug>.md` in Nygard format (Title, Status, Context, Decision, Consequences). Supersede rather than edit any earlier ADR it reverses. Skip it when there's no decision worth recording, and say so in the PR body. Add the template under `skills/sdd-pr/resources/`. · *proposed*
  **Because:** [H1](#h1), [ADR format](#f-adr-format)
- **A2: Delete the feature's spec folder after merge** (`specs/<feature>/` for SpecKit; for OpenSpec, archive as usual). Do this in the same PR as A1 or in a follow-up cleanup step in `sdd-pr`, so only the ADR remains on `main`. Stop treating Linear issue documents (`skills/linear-docs`) as the long-term spec archive: they stay as in-flight working copies on the issue. · *proposed*
  **Because:** [H1](#h1), [Spec Kit lifecycle](#f-speckit-lifecycle)
- **A3: Turn on Linear Code Intelligence for PMs.** Move to (or confirm) Linear Business, connect the GitHub integration with code access, enable Settings › AI & Agents › Code Intelligence, turn on "Extend access to all members," and scope it to the product repo(s). PMs must be members, not guests. Document the setup in `docs/SETUP.md`. · *proposed*
  **Because:** [Code Intelligence](#f-code-intelligence), [GitHub seats](#f-github-seats), [Claude Projects needs per-user access](#f-claude-project-github), [Linear pricing](#f-linear-pricing)
- **A4: Add a `product-map` workflow** (a template under `docs/extensions/` or a new `skills/codekit/resources/` file that `codekit init` installs into the target repo at `.github/workflows/product-map.yml`). It triggers on `pull_request: closed` when merged to `main`, skips bot PRs, PRs with a `skip-product-map` label, and its own map PRs, and has no path filter. It runs `anthropics/claude-code-action` with a prompt that reads the diff, `docs/product-map.md`, and `docs/decisions/`. It updates `docs/product-map.md` (sections: features, screens, user flows, business rules, integrations, known limits, each entry linked to source paths and written in product language), runs a second verification pass against the code, and opens a PR on `docs/product-map-from-pr-<N>`. If `codekit init` installs it, `update` Step 5 must re-sync it too. · *proposed*
  **Because:** [H2](#h2), [H3](#h3), [claude-code-action automation](#f-cca-automation), [diff-on-merge](#f-diff-on-merge), [reviewable PR](#f-reviewable-pr)
- **A5: Add a project target to `skills/linear-docs/scripts/linear_docs.py`.** Add `--project <id-or-slug>` alongside `--issue`, creating or updating documents with `projectId`, still matched by title and skipped when the words are unchanged. Add a workflow step that runs on push to `main` touching `docs/product-map.md` or `docs/decisions/**` and publishes the map, plus a single "Decision log" document rolling up the ADRs, to one Linear project. · *proposed*
  **Because:** [H2](#h2), [Linear Agent reads documents](#f-linear-agent)
- **A6: Escalate ADR conflicts in the A4 prompt as Linear issues, never as edits.** When the diff contradicts an *accepted* ADR, Claude doesn't touch the ADR. It lists the conflict under "Decision conflicts" in the map PR body and creates one Linear issue per conflict (label `decision-drift`, links to the ADR and the merged PR), checking for an existing open issue first. Map staleness never files an issue. · *proposed*
  **Because:** [H3](#h3), [Swimm's auto-fix vs. flag split](#f-swimm-states), [no issue-filing precedent](#f-no-issue-pipeline)
- **A7: Add a scheduled full regeneration** in the same workflow file (`schedule:` weekly). Regenerate `docs/product-map.md` from the whole codebase, ignoring the current map, and open a PR only if the result differs substantively. Record the size of each diff as the data for H4's check. · *proposed*
  **Because:** [H4](#h4)

## Decisions (deliberately not doing)

- **Archiving every spec, plan, and task list.** The user doesn't think it helps PMs, and Spec Kit treats plan/tasks as disposable. The rationale those files carry is what A1 extracts ([H1](#h1)).
- **Claude Projects as the PM home.** Private-repo sync needs each user's own GitHub access, and syncing is manual, so it fails the seat constraint.
- **Giving PMs GitHub read access.** Read-only outside collaborators on private repos still use a paid seat.
- **DeepWiki or Google Drive as the primary PM surface.** Each adds a tool PMs don't otherwise use. Linear already does Q&A, documents, and ticket creation in one place.
- **Auto-fix PRs for decision conflicts.** They assume the code is right. A conflict with an accepted ADR is a judgment call ([H3](#h3)).
- **Filing tickets because the map is stale.** The next regeneration fixes the map, so a ticket would just be noise ([H3](#h3)).

## Sources

| Source | Type | Why it matters |
|--------|------|----------------|
| [Spec Kit: Spec Persistence Models](https://github.github.com/spec-kit/concepts/spec-persistence.html) | Official docs | Three lifecycle models; plan/tasks disposable; rationale-loss risk; no archive command |
| [OpenSpec glossary](https://openspec.dev/docs/glossary) | Official docs | Current specs vs. changes; archive merges deltas and keeps all artifacts |
| [Red Hat: Architecture decision records](https://redhat.com/en/blog/architecture-decision-records) | Practitioner blog | ADR origin (Nygard 2011), format, immutability, superseding |
| [GitHub Docs: GitHub license users](https://docs.github.com/en/billing/reference/github-license-users) | Official docs | Who uses a paid seat; the reason PMs can't read GitHub |
| [Claude Help: Using the GitHub integration](https://support.claude.com/en/articles/10167454-using-the-github-integration) | Official docs | Projects' repo sync is per-user access and manual |
| [Linear Docs: Code Intelligence](https://linear.app/docs/code-intelligence) | Official docs | Code Q&A in Linear; "Extend access to all members"; Business+ |
| [Linear changelog: Code Intelligence (2026-05-14)](https://linear.app/changelog/2026-05-14-code-intelligence) | Official changelog | Beta and free-during-beta status (via search summary) |
| [Linear Docs: Linear Agent](https://linear.app/docs/linear-agent) | Official docs | Reads documents, creates issues, permission-scoped |
| [Linear changelog: Introducing Linear Agent (2026-03-24)](https://linear.app/changelog/2026-03-24-introducing-linear-agent) | Official changelog | Agent usage included on all plans (via search summary) |
| [Linear pricing](https://linear.app/pricing) | Official pricing | Plan limits and the tier Code Intelligence requires |
| [Devin Docs: DeepWiki](https://docs.devin.ai/work-with-devin/deepwiki) | Official docs | Alternative repo wiki; `.devin/wiki.json` steering |
| [DeepWiki MCP guide (2026)](https://mcp.directory/blog/deepwiki-mcp-complete-guide-2026) | Third-party guide | Accuracy and lag caveats for generated wikis |
| [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action) | Official repo | Prompt-driven automation mode for A4 |
| [Doc Drift Detection in CI (2026-03-06)](https://understandingdata.com/posts/doc-drift-detection-ci/) | Practitioner write-up (Dosu workflow) | Merge-triggered diff→docs PR; limits; per-run cost |
| [Agent Patterns: Continuous Documentation](https://agentpatterns.ai/workflows/continuous-documentation/) | Pattern catalogue | Reviewable-PR rule, generator/verifier, hallucination risk |
| [Swimm: code-coupled documentation](https://docs.swimm.io/new-to-swimm/benefits-of-code-coupled-documentation) | Vendor docs | CI drift states; auto-fix vs. flag split |

## Open questions

- **Code Intelligence data handling and post-beta pricing.** The docs page says nothing about either. Find out before turning it on for client code.
- **Linear Agent quotas on non-Business plans.** "An amount of Agent usage" is unquantified.
- **`documentUpdate` input shape for project documents.** I couldn't verify it against Linear's API reference. Confirm it in the schema before building A5.
- **Two-repo maps.** Should each repo's map stay a separate Linear document under one project, or should a combined map be generated? I have no position yet.
- **OpenSpec as an alternative to a generated map.** OpenSpec's `specs/` is a human-maintained "how it behaves today" ([OpenSpec archive](#f-openspec-archive)). If the team switched frameworks, would that make the generated map unnecessary, or would it go stale the way `spec.md` did? Untested here.
- **Current Linear plan.** If you're on Free, the 250-issue cap and the move to Business for A3 are both budget decisions.
