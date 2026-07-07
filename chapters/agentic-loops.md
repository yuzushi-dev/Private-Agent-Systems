# Agentic Loops in Private Agent Systems

Two contemporary practitioner essays report the same description of the shift,
attributed to Boris Cherny, Head of Claude Code at Anthropic: "I don't prompt
Claude anymore. I have loops running that prompt Claude and figuring out what to
do. My job is to write loops."

The line matters because it names a different engineering surface. A developer
can still ask an agent to inspect a file, draft a patch, or explain a design.
That interaction stays inside a conversation. A loop moves part of the work
outside the conversation. It decides when to run, what state to load, which
tools to expose, when to ask another agent to verify the result, and when to
stop.

That shift changes the governance problem. A private agent system cannot treat
an agentic loop as a long prompt with a timer attached. The loop is a runtime
contract. It carries identity, state, memory, retrieval, tool permissions,
context selection, verification, and human approval across more than one model
call.

Start with the decisions the loop may make without a human, the evidence it
must record, and the boundary that stops the loop before it turns a small local
error into a system-level failure.

This chapter treats loop engineering as an operations problem. It asks when a
loop is worth building, what contract it needs, and how a private agent system
keeps the loop small enough to review.

In this chapter, PAS means private agent system: an agent runtime that operates
over private data, private tools, private memory, private identity, or private
approval boundaries. Private includes more than local or self-hosted deployment.
A loop is private when it can touch non-public source code, internal documents,
customer tickets, logs, persistent memory, company identities, private
repositories, production-adjacent tools, publishing channels, or decisions with
human accountability.

A bad model answer is only the visible failure. The larger risk is that
a recurring runtime carries a bad assumption, stale state, excessive authority,
or private material across runs.

## The prompt moved into the runtime

A prompt is a local instruction. It tells the model what the user wants now. A
loop is a recurring control structure. It packages intent, timing, memory,
tools, checks, and stop conditions so that an agent can keep working after the
first turn.

In a simple coding session, the developer supplies context by hand. The agent
reads a file, runs a test, proposes an edit, and waits. In a loop, the harness
does more of that selection work. It may inspect yesterday's CI failures, open
an isolated worktree, call a triage skill, assign a sub-agent, run tests, write
a report, and decide whether a fresh checker has enough evidence to approve the
result.

The model still matters, but the system around the model now determines much of
the behavior. A weak loop can turn a capable model into a noisy operator. A
well-governed loop can keep a capable model inside a narrow task with visible
state and reviewable evidence.

For private agent systems, the same model call can be low risk or high risk
depending on what the loop placed around it. A daily report loop that reads
public issues and writes a summary has a different risk profile from a
remediation loop that can inspect private logs, edit code, open a pull request,
and notify a team.

The loop should inherit the same discipline as any other runtime route. A route
is the runtime path that binds task class, data class, tool surface, memory
scope, context budget, and approval policy. Before the loop runs, classify the
task, classify the data, select the smallest useful context, expose only the
needed tools, record the trace, and make the approval boundary explicit.

## A loop is an operating contract

Treat an agentic loop as an operating contract before treating it as
automation. The contract should answer five questions.

First, what wakes the loop? A schedule, webhook, manual command, issue label,
failed check, or human request each implies a different expectation. A scheduled
loop needs quiet no-op behavior. A failed-check loop needs a narrow diagnostic
route. A manually started publication loop can ask for missing brief fields
before drafting.

Second, what state may it trust? Loops need durable state outside the model
context. A state file, issue board, database row, or wiki page can tell the loop
what happened before, which assumptions are still active, and which items remain
blocked. The loop must also know which state is stale, provisional, or
human-owned.

Third, which tools may it call? A read-only triage loop and a write-capable fix
loop need different tool surfaces. Tool exposure is an authorization surface.
Even when invocation still requires a per-call gate, exposing a tool makes that
tool part of the route's possible action space.

Fourth, what proves progress? A loop needs acceptance checks before it starts.
The check can be a test suite, a schema validator, a source-register row, a
leakage scan, a reviewer report, or a human gate. A loop without a progress
signal tends to substitute motion for completion.

Fifth, what stops it? The stop condition should be inspectable. A loop may stop
because the acceptance check passed, the budget expired, the same blocker
repeated, a policy gate failed, or a human decision is required. "The agent says
it is done" is not a stop condition for a private system.

The operating contract can fit in a small record:

```yaml
agentic_loop:
  name: dependency_sweeper
  trigger: daily_schedule
  route: code_maintenance
  level: L2_assisted_fix
  allowed_context:
    - project_instructions
    - dependency_manifest
    - failing_check_excerpt
    - bounded_source_reads
  denied_by_default:
    - production_secrets
    - unrelated_memory
    - broad_private_notes
  writable_surfaces:
    - isolated_worktree
    - draft_pull_request
  verifier:
    type: separate_checker
    required_evidence:
      - test_output
      - diff_summary
      - risk_notes
  human_gates:
    - merge
    - dependency_major_version_change
    - security_exception
  stop_condition:
    pass: tests_green_and_checker_approve
    pause: human_gate_required
    fail: budget_or_repeated_blocker
```

This record is more useful than a clever prompt. It tells an engineer what the
loop may do, what it must record, and where human ownership remains.

## When a loop is the wrong tool

Not every repeated agent task deserves a loop.

A one-off design question should stay a prompt. A deterministic file rewrite may
belong in a script. A fixed sequence of steps may fit a workflow. A human
decision with weak evidence should stay a review checklist until the team can
describe the acceptance check.

Use a loop when the task needs repeated judgement under a stable contract. The
loop should earn its complexity by handling recurrence, state, uncertainty, and
verification better than a prompt or script would.

The decision can be direct:

| Situation | Better first tool | Why |
|---|---|---|
| One question, no recurrence | Prompt | No durable state or trigger needed |
| Exact transformation | Script | Deterministic code is easier to test |
| Fixed handoff sequence | Workflow | The path does not need agent judgement |
| Weak acceptance criteria | Human checklist | The loop cannot prove completion |
| Repeated task with changing inputs | Loop | State, retrieval, and verification matter |
| Repeated task with write authority | Governed loop | Tool scope, checker, and gates become part of the design |

*Table: Choose the lighter tool before building a loop.*

That decision table keeps the route from absorbing work that belongs in a
prompt, script, workflow, or human checklist. Build a loop when the runtime must
handle recurrence, state, uncertainty, and verification under one contract.

## Run the loop admission test

Before writing a route card, test the candidate task.

Grant runtime authority only when the work recurs, an external check can reject
a bad result, the budget can tolerate retries, and the agent can inspect the
environment it changes. Code loops need tests, type checks, builds, logs, or
a reproduction path. Publishing loops need source rows, leakage scans, style
checks, and a human release gate. Operational loops need scoped connectors,
audit logs, and rollback or escalation paths.

Add two stop conditions before scheduling. First, set a hard budget: time,
tokens, iterations, or repeated blocker count. Second, name the human gate for
irreversible actions such as merge, deployment, customer contact, ticket
closure, or publication. Without those boundaries, the loop turns missing
evidence into repeated work.

If the task does not pass this admission test, keep the work manual. Use a
one-shot prompt, checklist, or fixed workflow. A private agent system gains
little from a loop that cannot prove progress or stop cleanly.

## Classify the loop before automating it

Loop engineering often starts with a convenience problem: the user does not
want to triage issues, reread logs, chase flaky tests, or draft the same release
notes every week. Convenience is not enough to choose the loop's authority.

Classify the loop by the artifact it may affect.

| Loop class | Typical job | Allowed first level | Required control |
|---|---|---|---|
| Report loop | Triage issues, summarize changes, inspect logs | L1 report-only | Source links and no writes outside state |
| Draft loop | Prepare release notes, articles, migration plans | L1 or L2 assisted draft | Evidence pack and human publish gate |
| Patch loop | Update dependencies, fix narrow CI failures | L2 assisted fix | Worktree isolation, tests, checker |
| Operational loop | Touch tickets, alerts, customer records, deploy paths | L1 first | Approval policy and scoped connectors |
| Research loop | Explore options, benchmark, compare designs | L1 report or L2 experiment | Method notes and reproducible artifacts |

*Table: Loop classes by artifact, first level, and required control.*

The first release of a loop should usually be lower authority than the final
ambition. Start report-only when the failure cost is unclear. Move to assisted
fixes after the trace shows that the loop classifies work correctly, reads the
right evidence, and stops at the right boundary. Reserve unattended action for
domains where the acceptance check is strong and the rollback path is already
tested.

The classification should also name the data class. A loop that reads public
release notes can run with broad retrieval. A loop that reads customer tickets
needs redaction, least-privilege connectors, retention rules, and trace review.
A loop that builds a public article from private working notes needs a leakage
review before any material leaves the private workspace.

## Name the loop threat model

Controls make more sense after the loop names the failure classes it must
contain. An agentic loop does not fail only when the model gives a wrong answer.
It can fail through the runtime that keeps invoking the model.

For a private loop, review these threats before granting write authority:

| Threat | Loop failure | Control |
|---|---|---|
| Prompt or goal injection | Untrusted input changes the loop's objective or tool use. | Separate trusted instructions from retrieved content and bind tools to the route. |
| Sensitive information disclosure | The loop moves private material into a public artifact, log, or external tool call. | Data classification, leakage scan, and human release gate. |
| Excessive agency | The loop can perform more actions than the task requires. | Least-privilege tool scope and per-route approval policy. |
| Supply-chain compromise | A plugin, MCP server, prompt template, tool description, dependency, or sub-agent contract changes the loop's behavior. | Version pinning, provenance, and review for natural-language tool descriptions. |
| Session context contamination | Retrieved text, stale state, or prior tool output pollutes later decisions. | Context provenance, bounded state, and source separation. |
| Inter-agent trust escalation | A sub-agent claims authority or status that the orchestrator accepts without proof. | Verified agent identity and checker independence. |
| Human-gate bypass | The loop decomposes a consequential action into small approvals that hide the real decision. | Gate compound actions, approval summaries from tool calls, and consent-fatigue monitoring. |
| Memory poisoning | A provisional or adversarial claim becomes durable loop memory. | Separate durable facts from run state and require provenance for memory promotion. |

*Table: Loop threat model by failure class and control.*

Modern loops also treat natural-language tool descriptions as part of the
instruction surface. A plugin, MCP server, connector, sub-agent contract, or
tool schema can tell the model what actions are available and how to interpret
them. Review those descriptions with the same care as code permissions, because
a stale or overbroad description can expand the loop's effective authority.

OWASP's 2025 LLM Top 10 gives the broad application-security categories:
prompt injection, sensitive information disclosure, supply chain, excessive
agency, system prompt leakage, vector and embedding weaknesses, misinformation,
and unbounded consumption. Microsoft's agentic AI failure taxonomy adds
agent-specific failures such as goal hijacking, inter-agent trust escalation,
session context contamination, MCP/plugin abuse, and human-in-the-loop bypass.
NIST's Generative AI Profile gives the risk-management frame: choose controls
that fit organizational goals, legal requirements, risk tolerance, and the AI
lifecycle.

The threat model should not become a compliance theater. Use it as a design
review: can this failure occur in this loop, under what condition, and which
control detects or prevents it?

## Write the PAS route card

After classification, write the route card that a private agent system can
enforce. The route card turns a loop idea into a reviewable runtime rule.

```yaml
route_card:
  route: code_maintenance_loop
  loop_class: patch_loop
  data_class: internal_source
  identity:
    actor: maintenance_agent
    owner: platform_team
    reviewer: code_owner
  allowed_memory:
    - project_state
    - dependency_policy
    - prior_blockers_for_this_route
  denied_memory:
    - unrelated_project_notes
    - personal_memory
    - customer_records
  retrieval_scope:
    - package_manifest
    - lockfile
    - failing_check_excerpt
    - changed_files_from_current_branch
  tool_scope:
    read:
      - git_status
      - test_output
      - bounded_file_reads
    write:
      - isolated_worktree
      - draft_branch
  approval_policy:
    auto_continue_when:
      - tests_pass
      - checker_approves
      - no_policy_gate_triggered
    human_required_when:
      - major_version_change
      - production_secret_needed
      - public_release
      - repeated_blocker
  trace_required: true
```

The route card should live near the loop, not in a retrospective document. If a
loop cannot name its data class, memory scope, tool scope, reviewer, and
approval policy, it is not ready for write authority.

Route cards also prevent accidental expansion. When a team adds a connector,
memory source, or write surface, the route card changes. Review that change as a
runtime permission change.

## Keep the loop package small

A loop should start as a small package of files and checks. The package gives a
human enough material to review the loop without reading every chat transcript
that produced it.

A minimal private-agent loop package contains:

| Artifact | Purpose |
|---|---|
| `LOOP.md` | Entry point, trigger, level, stop rules, and run command |
| `STATE.md` | Current objective, blockers, decisions, prior run summary |
| `route-card.yaml` | Data class, memory scope, tool scope, approval policy |
| `budget.md` | Token, time, iteration, and review limits |
| `run-log.md` | Append-only run summaries and gate outcomes |
| `checks/maker-packet.md` | What the maker changed or produced, with evidence |
| `checks/checker-report.md` | Independent decision with line or command evidence |

*Table: Minimal private-agent loop package.*

For the first implementation, compress the package to four decisions: one
trigger, one instruction contract, one state file, and one gate. Run the task by
hand until the packet is reliable. Then wrap it in a loop and schedule it.
Scheduling a weak manual run only makes the weakness recur.

This package can live in a repository, private vault, ticket system, or agent
workspace. The storage location matters less than the contract. A reviewer
should be able to answer three questions from the package: what woke the loop,
what authority did it have, and why did it stop?

## State is the spine of the loop

An agent conversation forgets. A loop must remember.

State gives the loop continuity without forcing the model to reread every prior
conversation. It records the current objective, known blockers, prior attempts,
accepted facts, open risks, and pending human decisions. It also protects the
human from a false sense of continuity. If the loop cannot point to durable
state, it is probably reconstructing history from whatever context happened to
be loaded.

A useful state file separates at least four things:

- **Durable facts:** source-backed information the loop may reuse.
- **Run state:** what happened in the current or previous run.
- **Decisions:** human-approved choices, dates, and owners.
- **Blocked items:** facts the loop could not determine or actions it must not
  take.

Do not let operational state become a knowledge base by accident. "The current
draft failed the leakage scan" belongs in run state. "Public artifacts must not
expose local paths or private repository identifiers" belongs in the loop
contract. "This vendor policy said X on a checked date" belongs in a source
register or wiki page with provenance.

State also gives the loop a way to stop. A loop that repeats the same failed
test, missing credential, unclear requirement, or policy block should write the
blocker and hand off. Without that rule, the loop may spend tokens proving the
same absence again.

## Use maker/checker where authority exists

A loop that can write, publish, update records, open pull requests, touch
operational systems, or influence costly human decisions needs a maker/checker
split. Self-approval is a weak control when the loop has authority outside its
own report.

The maker's job is to produce the artifact: patch, report, draft chapter,
evidence table, migration plan, or release note. The checker's job is to decide
whether that artifact satisfies the contract. The checker should read the
acceptance criteria, inspect the output, cite line evidence, and return a clear
decision such as `APPROVE`, `REVISE`, or `ESCALATE`.

The checker can be another model call, another agent profile, a deterministic
script, a human reviewer, or a combination. The important property is
separation. The same instruction packet that helped the maker finish the task
should not be the only source of approval.

Low-risk report-only loops can start with deterministic validation and periodic
human review. The maker/checker split becomes non-negotiable when the loop's
output can change code, records, external systems, public artifacts, or human
decisions.

For code, the checker may require test output, diff review, dependency risk,
and rollback notes. For a public chapter, it may require source rows,
public/private scrub evidence, forbidden-term scans, and a style pass against
the book contract. For an operational workflow, it may require a policy gate
before tickets, customer records, or deployment systems change.

Line evidence matters. A checker report that says "looks good" is a second
opinion, not a control. A checker report that cites the artifact, the passing
test, the missing claim source, or the exact leakage line gives the loop a
reviewable stop condition.

## Context budgets belong inside the loop

Agentic loops can burn context because they run more than once. Each iteration
can reload instructions, source files, memory, tool output, and prior state. A
loop that saves a human from repeated prompting can still waste money and
increase exposure if it loads broad context on every cycle.

The context budget should be part of the loop contract. The route should decide
which context classes may enter the model call:

- task request and route metadata;
- standing instructions triggered by the task;
- current run state and bounded previous state;
- retrieved memory or wiki pages selected by query;
- source excerpts or code symbols selected by orientation;
- tool schemas needed for the route.

The loop should start with orientation before broad reads. A code loop can ask a
source graph, failing test, or changed-file list where to look before reading
whole files. A publishing loop can load the style contract, target section, and
source rows before loading every prior draft. A support loop can retrieve the
customer record fields allowed by policy rather than dumping the entire account
history into the prompt.

Budgeting does not mean starving the model. Some tasks need a full document,
large diff, or long evidence packet. The loop should record why the larger
packet was necessary and which acceptance check made the result valid.

## Record the loop trace

A loop report should show what it produced and how it reached the output.

At minimum, record:

- trigger and route;
- run identity and owner;
- data class;
- context classes loaded;
- memory records used;
- tools exposed and tools called;
- files or external records read;
- files or external records changed;
- acceptance checks run;
- checker decision;
- human gates reached;
- budget consumed;
- stop reason.

A trace record can stay compact:

```yaml
loop_trace:
  run_id: dep-sweeper-2026-06-28-01
  route: code_maintenance_loop
  trigger: daily_schedule
  data_class: internal_source
  context_loaded:
    - project_instructions
    - dependency_policy
    - failing_check_excerpt
    - package_manifest
  memory_used:
    - prior_blocker: "major versions require human review"
  tools_exposed:
    - git
    - test_runner
    - bounded_file_read
  tools_called:
    - git_status
    - npm_test
  artifacts_changed:
    - package-lock.json
  checks:
    - npm_test: PASS
    - checker_report: APPROVE
  gates:
    - merge: HUMAN_REQUIRED
  budget:
    iterations: 1
    stop_reason: human_gate_required
```

The trace is not paperwork. It is the audit surface. Without it, the team must
read the whole conversation to understand whether the loop respected its
contract.

## Human gates define the release boundary

Human gates should appear inside the loop design, not at the end as a vague
reminder to be careful.

The gate names the decision that a person owns. A loop may draft a patch, but a
human may own merge. A loop may prepare a public article, but a human may own
publication. A loop may summarize alerts, but a human may own customer contact.
A loop may propose a dependency upgrade, but a human may own major-version
acceptance.

The gate should include the evidence a reviewer needs:

```yaml
human_gate:
  decision: public_release
  owner: author_or_editor
  required_packet:
    - final_markdown
    - source_register_rows
    - leakage_review
    - checker_report
    - open_risks
  forbidden_without_approval:
    - publish_to_public_repo
    - post_to_social_channel
    - mirror_private_notes
```

This structure reduces ambiguity. The loop can work up to the gate, prepare the
packet, and stop. The human can review a bounded set of evidence rather than a
long conversation.

## Add a kill switch and downgrade path

A loop also needs a way to lose authority.

Disable or downgrade the loop when the trace shows one of these conditions:

- the same blocker repeats across runs;
- the checker rejects the same class of output more than once;
- the loop reaches a human gate too often to justify its cadence;
- the loop loads broader context than the route allows;
- the loop creates review work faster than reviewers can clear it;
- the loop touches a data class that the route card did not permit;
- the cost per accepted artifact exceeds the agreed budget;
- the rollback path is unclear for the action it proposes.

Downgrading is not failure. A loop can move from L2 assisted fix back to L1
report-only while the team improves the route card, tests, checker, or source
boundaries. Keeping that path explicit prevents the worst loop failure: a system
that keeps running because no one named the condition that should stop it.

## Walk one report-only request through the loop

Start with a lower-authority example. A weekly release-awareness loop reads
public vendor release notes, internal issue labels, and the current source
register. It writes a candidate release summary for the editor.

The route is report-only. The loop may read public sources, issue metadata, and
approved project state. It may not post to a public channel, edit the release
page, or update the source register without review. The trace records sources
checked, rows that may need revalidation, ignored items, and open questions.

The output is a packet: summary, source links, stale rows, and editorial gate.
If the editor approves, a person updates the public artifact. If the loop finds
no relevant changes, it records a no-op run and stops.

## Walk one maintenance request through the loop

Consider a dependency-maintenance loop. The team wants the agent to inspect a
project each morning, identify low-risk dependency updates, prepare draft
changes, and stop before merge.

First, the route classifies the task as `patch_loop` with internal source data.
The loop may read the manifest, lockfile, dependency policy, and failing check
excerpt. It may not read customer tickets, production logs, personal memory, or
unrelated project notes.

Second, the loop loads state. The state says major-version upgrades require
human review and one package is pinned because a prior upgrade broke a platform
integration. The loop does not need the whole conversation that produced those
decisions. It needs the dated decision rows.

Third, the maker works inside an isolated worktree. It updates a narrow package
set, runs the test command, records the diff summary, and writes rollback notes.
If tests fail, the loop records the failure and either revises once or stops at
the repeated-blocker rule.

Fourth, the checker reviews the packet. It verifies the tests, scans the diff,
checks that no major version slipped through, and confirms that the loop stayed
inside the route's tool and data scope. The checker cites file and command
evidence.

Fifth, the loop reaches the human gate. It may open or update a draft pull
request with the packet, but merge remains human-owned. If the checker rejects
the packet or the route hits a major-version gate, the loop downgrades to a
report.

The draft change matters. The bounded artifact package matters more: diff,
tests, policy check, checker report, trace, and explicit gate. A reviewer can
approve, reject, or tune the loop without rereading a long agent transcript.

## Common failure modes

Agentic loops fail in recognizable ways.

| Failure | What happens | Control |
|---|---|---|
| Prompt loop disguised as system | The loop repeats a long prompt without state, budget, or stop condition. | Write an operating contract before scheduling. |
| State drift | The loop treats old assumptions as current facts. | Date state entries and separate facts, decisions, and run notes. |
| Tool overexposure | The route exposes connectors or write tools that the task did not need. | Bind tools to route class and data class. |
| Checker capture | The verifier shares the maker's blind spots or approves without evidence. | Require independent instructions and line evidence. |
| Context creep | Each iteration loads more memory, source, and logs than the task needs. | Add context budgets and orientation before broad reads. |
| Silent public leakage | A publishable artifact includes local paths, private identifiers, raw measurements, or revealing caveats. | Run a public/private scrub before release review. |
| Comprehension debt | The loop produces artifacts faster than the team can understand them. | Cap authority, require summaries, and keep review queues small. |
| Cost runaway | The loop keeps retrying without a stronger signal. | Set token, time, iteration, and repeated-blocker limits. |
| Premature completion | The loop stops because the maker claims success rather than because an external gate proved completion. | Let tests, build output, source review, release gates, or the checker own completion. |

*Table: Agentic loop failure modes and controls.*

Treat premature completion as a separate failure mode. The run can exit cleanly
while the artifact remains half done if the stop rule accepts a maker's
completion claim as proof. Give completion to an external gate.

These failures are governance failures before they are model failures. Better
models can reduce some mistakes, but they do not remove the need for state,
scope, evidence, and approval.

## A staged adoption path

Adopt loops in stages.

**Stage 1: report-only.** Start with a loop that reads a bounded surface and
writes a report. Examples include daily issue triage, dependency risk summary,
release note candidate list, or source-update watch. The loop should record
what it read, what it ignored, and which human decision it needs.

**Stage 2: assisted drafts.** Let the loop produce artifacts in a private
workspace: draft pull requests, draft chapters, migration plans, incident
summaries, or benchmark packets. Require maker/checker separation and keep
publishing, merging, customer contact, and deployment behind human gates.

**Stage 3: narrow write authority.** Allow writes only where the acceptance
check is strong. A formatting fix, generated changelog, or minor dependency
patch may qualify if tests, diffs, rollback notes, and review policy are clear.
Use worktrees or sandboxes so parallel loops cannot collide.

**Stage 4: unattended action for reversible paths.** Reserve this stage for
tasks with low blast radius, strong observability, tested rollback, and clear
ownership. Even then, the loop should leave a trace that a human can audit.

The staged path prevents a common mistake: building the loop at the authority
level the team wants someday rather than the evidence level the team has today.

## Operating the system

A production loop needs routine maintenance.

Review the state file. Remove stale blockers, expired assumptions, and completed
items. If the loop keeps rediscovering the same fact, promote the fact to a
durable knowledge page or contract. If the loop keeps making the same mistake,
change the contract or checker instead of adding another warning sentence to
the prompt.

Review the tool surface. Connectors, plugins, MCP servers, and shell commands
change the loop's authority. When a route gains a new tool, treat that change
like a runtime permission change. Record why the loop needs it and which gate
contains the risk.

Review the budget. Token cost, latency, retries, and human review time all
belong in the budget. A loop that saves prompting time but creates a larger
review queue may still be a poor system.

Review the trace. The trace should answer what triggered the run, which context
entered the model call, which tools ran, which files changed, which checks
passed, which gates blocked release, and who approved the next step.

Track a small set of operating metrics:

- accepted artifacts;
- checker rejection rate;
- human gate rate;
- repeated blocker rate;
- leakage findings;
- cost per accepted artifact;
- review time per accepted artifact;
- rollback count;
- percentage of runs ending in no-op.

These metrics do not prove that the loop is good. They tell the owner where to
look. A high no-op rate may mean the cadence is too aggressive. A rising checker
rejection rate may mean the route card is weak or the maker has too much
authority. A rising human gate rate may mean the loop should run as a report
instead of an assisted fix.

Use cost per accepted artifact as the control metric. It groups token spend,
tool time, failed attempts, and reviewer time around the outcome the loop was
built to produce. Tokens per run and scheduled runs are secondary signals; they
reward activity even when the review queue grows.

The practical work is narrow: write the route card, keep state clean, expose
fewer tools than the model could use, require evidence, and stop at the gate.
That is enough. A private agent system does not need a grand theory of work to
use loops well. It needs contracts that a reviewer can inspect.

## Sources and verification snapshot

This chapter uses a dated source snapshot rather than treating loop engineering
as a settled standard.

| Claim area | Source | Source status | Checked on | Use in this chapter |
|---|---|---|---:|---|
| Boris Cherny role | [Anthropic webinar page](https://www.anthropic.com/webinars/claude-code-for-financial-services-boris-cherny) naming Boris Cherny as Head of Claude Code | primary organizational source | 2026-06-28 | Verify the role attribution. |
| Boris Cherny loop quote and practitioner framing | Addy Osmani, ["Loop Engineering"](https://addyosmani.com/blog/loop-engineering/); Armin Ronacher, ["The Coming Loop"](https://lucumr.pocoo.org/2026/6/23/the-coming-loop/) | contemporary secondary sources | 2026-06-28 | Attribute the quote and frame loop engineering as an emerging practitioner pattern. Primary recording or original post not included in this snapshot. |
| Workflow and agent distinction | Anthropic, ["Building effective agents"](https://www.anthropic.com/engineering/building-effective-agents) | primary practitioner guidance | 2026-06-28 | Support the distinction between predefined workflows, more dynamic agents, checks, guardrails, and cost/error tradeoffs. |
| LLM application security risks | [OWASP GenAI Security Project: Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) | risk framework | 2026-06-28 | Anchor prompt injection, sensitive information disclosure, supply chain, excessive agency, and related LLM application risks. |
| Generative AI risk management | [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) and [NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1) | risk framework | 2026-06-28 | Anchor risk tolerance, lifecycle, legal/regulatory context, and control selection. |
| Agentic AI failure modes | [Microsoft AI Red Team taxonomy v2.0](https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/bade/documents/products-and-services/en-us/security/Taxonomy-of-Failure-Modes-in-Agentic-AI-Systems-v2-0.pdf) and [Microsoft Security Blog summary](https://www.microsoft.com/en-us/security/blog/2026/06/04/updating-taxonomy-failure-modes-agentic-ai-systems-year-red-teaming-taught-us/) | threat-modeling reference | 2026-06-28 | Anchor agentic supply chain compromise, goal hijacking, inter-agent trust escalation, session context contamination, MCP/plugin abuse, and human-in-the-loop bypass. |
| Loop-engineering reference implementation and vocabulary | [`cobusgreyling/loop-engineering`](https://github.com/cobusgreyling/loop-engineering) public repository | reference implementation | 2026-06-28 | Treat patterns, readiness levels, state, budget, and maker/checker language as reference vocabulary, not as a required framework. |

*Table: Dated source snapshot for this chapter.*

The sources support the shape of the pattern. They do not prove that any
specific loop improves quality, reduces cost, or should run unattended in a
given organization. Those claims require local measurement and acceptance
checks.
