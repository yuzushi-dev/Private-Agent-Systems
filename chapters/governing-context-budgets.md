# Governing Context Budgets in Private Agent Systems

A developer asks a coding agent a narrow design question. The agent opens
files, reads command output, loads project instructions, sees tool schemas,
scans memory, and pulls snippets from search. The answer may help, but the run
still consumed every chunk the agent packed into the prompt.

The visible cost is tokens, latency, and expensive retry loops. The harder
failure comes later. The agent starts carrying stale notes, duplicate
instructions, broad tool descriptions, and half-relevant code into tasks that
needed a small slice of the system.

Large context windows do not remove the runtime decision. A private agent still
needs a harness that decides what enters context, why it enters, and which
narrower path could have answered the same request.

A private agent system is the runtime around the model: identity, tool access,
memory, retrieval, state, routing, approvals, and traces. For an auditable
private agent, the runtime records which state, memory, source material, and
tool outputs entered the model call. It also records the acceptance check that
made the smaller context path legitimate.

## Context belongs in the runtime contract

Private agent systems already make runtime decisions around identity, data
classification, tool permissions, memory, retrieval, model routing,
observability, and approval policy. Context budget belongs in that same
contract.

Each extra token can carry data the model did not need. A stale memory can bias
the answer. A broad source read can expose material outside the task. A plugin
instruction can expand the agent's authority. A noisy shell command can bury
the line that showed the failure.

The prompt builder should answer these questions before the model call:

- Which request and route produced this prompt?
- Which data class did the route permit?
- Which instructions were loaded because the task needed them?
- Which memory item affected the run?
- Which source material entered the prompt?
- Which tool output entered the prompt?
- Which narrower context path was available?
- Which acceptance check proves the smaller path did not change the result?

Together, the answers make context packing auditable.

The decision does not need a heavyweight policy engine. A private agent can
start with a small set of route rules. A shell-heavy coding route may allow
filtered command output and bounded file reads. A project-planning route may
allow durable memory and current project notes. A research route may allow
source documents with provenance. A write-capable route should demand a higher
bar, because the prompt can carry instructions that change the system.

Context policy should sit near the prompt builder rather than in an after-action
spreadsheet. Once the model has seen a broad packet, the privacy and reliability
decision has already happened. Logs can explain it later, but they cannot undo
it.

## Classify context before optimizing it

Token-saving claims matter only after you name what kind of context the tool
removed. A private agent usually carries six classes of prompt material.

| Context class | Examples | Main risk | Budget control |
|---|---|---|---|
| Task request | User prompt, route metadata, current objective | Ambiguous scope | Route-specific prompt template |
| Standing instructions | `AGENTS.md`, `CLAUDE.md`, policy text, skills | Excess authority or stale procedure | Progressive loading |
| Runtime state | Plan, current files, previous tool outputs | Lost boundaries between steps | Trace-linked state selection |
| Memory | Prior decisions, preferences, project observations | Stale or sensitive recall | Search first, fetch selected detail |
| Source material | Code, docs, notes, tickets, wiki pages | Overbroad disclosure | Narrow retrieval and claim locators |
| Tool schemas | Available tools, parameters, descriptions | Capability expansion | Route-specific tool exposure |

*Table: Prompt material should have a data class and a budget rule.*

The budget control differs by class. Instruction mass should not be loaded
because it exists. It should be loaded because the task triggered it. Memory
should not mean placing every prior observation in the prompt. It should mean
retrieving the records that can affect the answer, under retention and privacy
rules. Source material should enter through locators, summaries, snippets, or
structured orientation steps before the model reads whole files.

During review, the operator can ask whether the prompt lacked the right source,
loaded the wrong memory, or exposed an irrelevant tool. Without the class
boundary, every failure turns into a vague complaint that the model "lost
context."

## Define route budgets

A context budget becomes enforceable when it is attached to a route. The route
describes the kind of task, the context classes it may use, the tool surface it
may expose, and the acceptance check it needs to satisfy.

A coding investigation route might allow project instructions, filtered shell
output, source-code orientation, and bounded file reads. It may deny long-term
personal memory unless the request asks for prior decisions. A documentation
route might allow source excerpts, citation records, and style guidance. A
deployment route might expose infrastructure tools but require approval before
the model sees secrets, hostnames, or production logs.

The budget does not need to be a single number. It should name the shape of the
context packet:

```yaml
route_budget:
  route: coding_investigation
  allowed_context:
    - project_instructions
    - filtered_shell_output
    - source_orientation
    - bounded_file_reads
  denied_by_default:
    - unrelated_memory
    - broad_private_notes
    - write_tools
  max_broad_reads_before_orientation: 0
  acceptance_required: true
```

A route budget gives the agent a working rule and gives the operator a review
target. If the trace shows broad source reads before orientation, the route
failed. If unrelated memory entered the prompt, the route failed. If the agent
used a small packet and missed the answer, the acceptance check failed.

Route budgets also help multiple agents share a system. Claude Code, Codex, and
other clients can load different instruction formats, but they can still follow
the same runtime contract: classify the request, choose a route, select context,
record the decision, and verify the result.

The route should not pretend that small context is always better. Some tasks
need a whole document, a full diff, or a large source excerpt. The governed
decision is not "minimize every prompt." The governed decision is "load the
smallest packet that preserves the task result and respects the data class."

## Walk one request through the budget

Consider a routine coding request: "Why does the billing export fail after the
last change?" An unguided agent may load recent chat context, project memory,
test output, several source files, build logs, tool descriptions, and a broad
search result. The answer may be correct, but the operator cannot easily tell
which context mattered.

A governed route handles the same request in stages.

First, it classifies the task as a coding investigation. The route permits
project instructions, filtered command output, source orientation, and bounded
file reads. It does not load long-term personal memory, unrelated project notes,
or write-capable tools at the start.

Second, it asks for the smallest diagnostic packet. The shell output filter
keeps the command, exit status, failing test, file, line, assertion, and a short
surrounding excerpt. The model does not need the entire test log unless the
filtered packet fails acceptance.

Third, the source-code orientation layer identifies the likely files and
symbols. The model sees names and locations before it reads implementation
detail. If the orientation result points to the wrong area, the trace records
the miss and the route escalates to a broader read.

Fourth, the agent reads the bounded source excerpts and answers the question.
The trace records which files entered the prompt, which tool outputs were used,
and which context classes were denied. The acceptance check asks whether the
answer identifies the failing behavior, the relevant source location, and the
change needed to fix it.

The same pattern works for documentation. A request to update a chapter should
load the style reference, the target section, source locators, and the relevant
public evidence table. It should not load every draft, every unrelated note, or
private measurement material. The acceptance check asks whether the text
preserves the claim, cites the right source, and avoids exposing private system
details.

Ordinary tasks make context governance valuable because they repeat. A route
that trims one noisy command does not matter much. A route that trims, records,
and verifies hundreds of ordinary tasks changes the cost and auditability of
the whole system.

## Separate the evidence classes

Measurements become misleading when they collapse different savings into one
number. Separate the evidence before comparing tools.

**Runtime-reported savings** come from a tool that records its own filtering
during normal work. The numbers carry operational evidence because the tool saw
the commands or context operations as they happened.

**Static footprint avoided** estimates instruction mass kept outside the
always-on context. Skills, plugins, and project files can add a large
capability surface. Progressive loading saves prompt space when the agent loads
only the procedure a task triggers.

**Task-level measurements** compare two execution paths on the same task. One
path reads broad context. The other uses a structured route for the same
question. Task-level measurements need an acceptance check, because a tiny
prompt that misses the answer did not save context.

Do not average these categories together. A shell filter, a context mask, a
skill loader, a memory system, and a source-code graph each remove a different
kind of prompt material. A defensible claim says which layer avoided which class
of context, for which task, under which acceptance condition.

## Measurement method

The measurements below are not provider invoices and are not end-to-end success
benchmarks. They are context-selection measurements from a dated audit snapshot.

For each row, the audit records:

- the tool or runtime layer measured;
- the context class removed or kept outside the active prompt;
- the baseline path;
- the optimized path;
- the token estimation method;
- the acceptance check;
- the reviewer class for the acceptance decision;
- the checked date;
- the limit of the claim.

The broad path is the recorded or reconstructed route that would expose raw
command output, active tool output, always-on instructions, broad memory
context, or broad source context for that task class. The optimized path is the
narrower route actually measured for the same task class: filtered command
output, deferred active context, triggered skills, selected memory detail, or
structured source orientation.

For task-level source-orientation rows, the broad path is the source packet that
the unguided route would have loaded before the structured orientation step:
selected broad files, broad search output, or architecture material recorded in
the private trace. The public table reports the token count and scope, not the
private source content.

When token counts are estimated, the table marks them as estimates. When a
number is reported by a tool's own instrumentation, the table marks it as
runtime-reported. When a measurement covers only source-code orientation, memory
retrieval, or command-output filtering, the claim is limited to that step and
does not imply full task success or provider billing savings.

Token reduction never decides acceptance. The task owner or operator reviews the
result against the acceptance field recorded for that row.

The public snapshot reports accepted measurements only and should not be read as
an acceptance-rate report. Negative cases remain in the private audit log and
should be summarized separately when they change route design.

## Audit snapshot

The companion repository includes a dated, sanitized context-budget audit. The
published measurement set covers reusable layers of the stack: shell-output
filtering, context masking, progressive skill loading, memory retrieval, and
source-code orientation. The audit snapshot was generated on 2026-06-26. The
public table ID is `context-budget-public-results-2026-06-26`, published in the
companion repository under `marketing/token-saving-public-results.md`. The
source register records the checked date, table path, and checksum.

| Layer | Evidence type | Scope | Baseline path | Optimized path | Acceptance reviewer | Claim limit |
|---|---|---|---|---|---|---|
| RTK | Runtime-reported | Shell-output filtering | Raw command output | Filtered command output | n/a, runtime aggregate | Not total agent cost |
| Claude Context Mode | Runtime-reported | Active context pressure | Tool output in active context | Deferred or kept outside context | n/a, runtime aggregate | Not data classification |
| Progressive skill loading | Static footprint estimate | Always-on instruction mass | Full skill library loaded | Triggered skills only | operator review | Not billing saving |
| `claude-mem` | Task-level estimate | Memory retrieval | Broad memory context | Selected detail fetch | task owner/operator | Single task check |
| `codebase-memory-mcp` | Task-level estimate | Source-code orientation | Broad source prompt | Structured orientation | task owner/operator | Not end-to-end success |

*Table: Public context-budget evidence by layer and claim limit.*

RTK reported **23.8 million shell-output tokens saved**, a **63.70% reduction**,
across **22,909 observed commands**. The number captures command-output
filtering for supported shell output, not total agent cost or every agent tool
call. Treat it as a dated runtime snapshot because the aggregate changes as more
commands run.

Claude Context Mode reported **1.10 million tokens saved** across **20 recorded
sessions**, with a **50.95% average reduction**. It also kept **4,407,150
bytes** out of active context. It measures active prompt pressure: large outputs
can remain outside the model call until the agent needs them. The snapshot
applies only to the recorded sessions and the interception paths active in that
environment.

Progressive skill loading kept a large instruction surface out of the always-on
layer. The Codex skill bodies measured about **151,339 estimated tokens**. The
Claude skill bodies measured about **170,589 estimated tokens**. Report this as
avoided always-on footprint, not as provider-billed runtime saving.

`claude-mem` reduced one memory-retrieval task from **6,762** estimated tokens
to **2,606**, saving **4,156 tokens**, or about **61%**. The smaller path met the
same acceptance check for the task.

`codebase-memory-mcp` produced the largest accepted query-time reduction. For one
feature-area orientation task, the broad prompt path would have used **44,917
estimated tokens**. The structured orientation path used **704 estimated
tokens**. That avoided **44,213 estimated prompt tokens**, about **98%**
for that step.

For an architecture overview, the broad prompt path would have used **159,372
estimated tokens**. The structured result used **1,050 estimated tokens**,
avoiding **158,322 tokens**, about **99%**.

The numbers do not prove end-to-end task success. They show that a structured
orientation step can answer the question without loading broad source context
into the model. Do not generalize the 98-99% orientation reductions to every
repository, task, or agent run.

## Choose the tool by context problem

Different context-budget tools solve different problems. A governed stack can
use several of them, but each should have a narrow job.

| Runtime control | Best use | What it does not solve |
|---|---|---|
| RTK | Shell-heavy coding runs with noisy command output | Memory, source permissions, long-term state |
| Claude Context Mode | Keeping large tool outputs outside active context until needed | Data classification, approval policy |
| Progressive skill loading | Loading task-specific procedures instead of a full instruction library | Runtime proof that a task succeeded |
| `claude-mem` | Long-term memory retrieval with selected detail fetches | Retention policy or privacy review by itself |
| `codebase-memory-mcp` | Source-code orientation before reading files | Index maintenance, final code review |

*Table: Context-budget tools by primary purpose.*

Use RTK when build logs, test output, search output, and command noise can
dwarf the relevant line. A shell command can produce thousands of lines while
only one assertion failure matters. The shell filter belongs before the model
call, not after the model has paid to read the noise. Treat RTK as command-output
filtering, not as coverage for every built-in file or search tool.

Use Claude Context Mode when a session produces large tool outputs or file
reads that should stay outside active context until the agent asks for them.
It fits long-running investigations where many observations are available but
only a few need to enter the next prompt. Review the actual interception path
before claiming uniform coverage.

Use progressive skill loading when a procedure, domain convention, or safety
check belongs in a task-specific file rather than in the always-on prompt. A
skills directory can be large. Loading all of it makes the prompt longer and
can give the model irrelevant instructions. Loading the triggered skill keeps
capability without turning every run into a manual dump.

Use `claude-mem` for past decisions, project observations, and user or team
preferences that need retrieval over time. The runtime should retrieve selected
detail under policy. Memory should not mean loading the past into every run.

Use `codebase-memory-mcp` for source-code orientation. It fits questions like
"where is this concept defined," "who calls it," and "which files matter." The
agent can inspect names, files, call paths, and architecture summaries before
reading source.

Use the public evidence table when publishing claims. The table is not a
runtime control. It is a reporting artifact that separates result class, scope,
acceptance, and limits.

## Build a public evidence table

Public context-budget claims need a table because prose blurs categories. The
table names the layer, best use, evidence type, baseline, optimized path, saved
tokens, reduction, acceptance scope, and publication status.

The evidence type protects the claim. A runtime aggregate can show what a tool
reported during ordinary operation. It cannot prove that every downstream task
became cheaper. A static footprint estimate can show how much instruction mass
stays outside the always-on prompt. It cannot prove that a task used fewer
provider-billed tokens. A task-level same-task estimate can show that a
structured path answered a narrow question with less prompt material. It cannot
claim end-to-end task success unless the end-to-end task was actually tested.

The acceptance column protects the reader. If a row says "orientation answer
accepted," the reader knows the number applies to an orientation step. If a row
says "memory retrieval acceptance check passed," the reader knows the number
applies to selecting memory, not to the whole user request. That boundary
separates a measurement from a marketing number.

Keep private infrastructure out of the table. A public claim does not need
private system identifiers, internal measurement artifacts, trace payloads, or
implementation files. It needs enough information to show the measurement class
and the limit of the claim.

When updating a public evidence table, apply the same discipline used for a
source register. Keep the original checked date. Add later changes as dated
updates. If a tool changes its measurement method, record the change instead of
silently replacing the old row. A context-budget number is temporal. It belongs
to a stack, a date, a route, and an acceptance condition.

## Design the acceptance check before the measurement

A context-budget result matters only if the smaller context still supports the
task. For private agents, the acceptance check should be written before the
measurement, beside the route that selects context.

For a shell-output task, acceptance may be: identify the failing test name, file,
line, and assertion from filtered output. For a memory task, acceptance may be:
retrieve the prior decision that changes the answer, cite its identifier, and
avoid unrelated preferences. For a source-code orientation task, acceptance may
be: identify the relevant symbols and files before reading implementation
detail. For a documentation task, acceptance may be: preserve each cited claim
and its source locator.

Acceptance checks should stay narrow. Do not claim an end-to-end success result
when the measurement covered only orientation. Do not claim provider billing
savings when the measurement used estimated prompt tokens. Do not claim privacy
improvement when the tool only removed noise. Each claim should name the task
surface it actually measured.

A compact acceptance record can look like this:

```yaml
context_decision:
  request_class: source_code_orientation
  context_class:
    - standing_instructions
    - source_orientation
  broad_path_est_tokens: 44917
  structured_path_est_tokens: 704
  acceptance:
    required_result: identify_feature_area_files_and_symbols
    result_status: accepted
  limits:
    - not_end_to_end_task_success
    - not_provider_invoice
```

The record omits private source material while preserving enough structure for
review.

Acceptance also needs a negative control. If the smaller path fails to identify
the needed source, memory item, or failing command, the result should stay in
the audit record. The failure tells the operator where the runtime needs better
retrieval, a larger context packet, or a different route. A system that records
only wins will teach the team to over-trim.

For some tasks, the broad path is correct. Legal review, safety analysis, API
contract migration, and release-note generation can require a full document or
complete diff. The context-budget decision records why the broader packet was
necessary. Governance makes the prompt choice inspectable; it does not force the
smallest prompt.

## Record context decisions in traces

A private agent records context decisions the same way it records tool calls. A
trace shows the request, data class, route, loaded state, retrieved sources,
tool outputs, token counts, and acceptance result. If a user challenges the
answer, the operator can see which memory item, file, or tool output influenced
it.

The trace also shows rejected context. If the route chose a summary over a full
file, record that choice. If the memory search returned many candidates but only
one entered the prompt, record the selection. If a tool schema was not available
on the route, record the route boundary.

Trace review should answer four questions:

- Did the prompt contain enough information to solve the task?
- Did it contain information outside the task boundary?
- Did a narrower path exist and pass acceptance?
- Did the route expose tools or memory the task did not need?

The answers connect cost, privacy, and reliability. A low-cost prompt that
misses the relevant source is not governed. A rich prompt that includes unneeded
private memory is not governed either.

## Put context budget in approval policy

Approval policy usually focuses on side effects: writing files, running
commands, calling external services, or changing infrastructure. Context
selection deserves the same treatment, because the prompt is where data and
authority meet the model.

A narrow source-code query with bounded read access may need no human approval.
A broad scan across sensitive material may need explicit approval. A memory
fetch that exposes preferences or personnel data should follow retention and
privacy rules. A plugin that adds write tools should require a capability
review before the tool schema enters the route.

The policy defines escalation by data class, not by token count alone.
Ten tokens can be sensitive. Ten thousand tokens can be harmless build noise.
Budget accounting helps the operator see scale, but the data class decides the
privacy boundary.

## Review prompt changes like runtime changes

A prompt builder is runtime code. Changing what it loads can alter privacy,
cost, latency, and task quality even when no application code changed. Treat
context selection changes the way you treat tool permissions or model routes.

Review is needed when a route adds a new memory source, exposes a new tool,
loads a new instruction file, changes retrieval ranking, or relaxes a source
read boundary. The change may be small in code and large in behavior: one
instruction can give the model a new procedure, one memory source can carry
stale preference data, and one broad read rule can turn a narrow investigation
into private-data exposure.

A route change review includes:

- The context class added or removed.
- The data class of the new material.
- The task class that needs it.
- The acceptance check that failed without it.
- The expected token impact.
- The trace field that will record the decision.

Route review prevents "helpful" prompt growth. Teams often add context after one
bad answer and never remove it. Route review forces the team to ask whether the
fix belongs in retrieval, a skill, a source locator, or an acceptance check
instead.

The rollback path must be explicit. If a route change increases cost or
introduces stale context, the operator needs a way to remove it without
rewriting the rest of the agent. Keep context rules modular: global instructions
stay small, route templates stay separate, skills carry task-specific
procedure, and memory retrieval remains policy-bound.

## Common failure modes

**The agent loads the instruction library by default.** The model sees
procedures, examples, and constraints unrelated to the task. Use progressive
loading and record which skill triggered.

**The memory layer behaves like a transcript dump.** Prior decisions, personal
preferences, and stale observations enter the prompt together. Use search,
selection, retention rules, and explicit fetches.

**The source route starts with whole files.** The agent reads implementation
detail before it knows which files matter. Use orientation steps and bounded
source reads.

**The shell route forwards raw command noise.** Test runs and build logs can
dominate the prompt. Use output filtering that preserves the failing line,
status, and relevant context.

**The audit number loses its scope.** A task-level orientation saving becomes a
claim about full task success, or a static footprint estimate becomes a billing
claim. Keep each number attached to its evidence class.

**The trace records only what the model saw.** The operator cannot inspect
which candidates were rejected or why a narrower route was chosen. Record the
selection decision, not just the final packet.

**The public artifact exposes the private measurement path.** A chapter or
companion repository can publish too much by naming internal artifacts or
describing private setup. Keep public evidence and private measurement artifacts
separate.

**The route hides behind tool branding.** A team says "we use memory" or "we
use a graph" without describing when the runtime selects those layers. Tool
choice is not a policy. The policy is the route that decides when the tool
contributes context.

**The context budget ignores tool schemas.** The model may see tools it does
not need for the task. A tool schema is prompt material and capability surface.
Route-specific tool exposure belongs in the same budget as files and memory.

## A staged adoption path

Start with shell output. It is visible, noisy, and easy to measure. Put a
filter in front of command output and record what it removed. Verify that
failures still include the command, exit status, failing test, file, line, and
short surrounding context.

Next, move task-specific procedures out of the always-on prompt. Keep global
instructions small. Load detailed procedures only when the task triggers them.
Measure the static footprint avoided, and review whether the skill boundary is
clear enough for another agent to use.

Then add memory selection. Do not start by preserving everything. Define which
observations are durable, which expire, and which should never enter a shared
trace. Measure one retrieval task at a time, with acceptance tied to a decision
or observation that changes the answer.

After that, add source-code orientation. The agent should read the right files
after it knows why they matter. Use structured orientation for names, call
paths, and architecture before reading implementation detail.

Finally, publish only sanitized results. Public claims should show the layer,
best use, evidence type, scope, acceptance condition, and limits. Keep internal
measurement artifacts under the access policy that matches their data class.

The staged path gives teams a review order. Shell filtering is usually low risk.
Instruction loading affects every task. Memory selection carries privacy and
retention questions. Source-code orientation affects correctness and developer
trust. Public evidence touches reputation, so produce it after internal review.

## Operating the system

Context budget belongs in ordinary agent operations. During planning, the agent
names the route and context classes. During execution, the runtime records
loaded instructions, retrieved memory, source locators, tool outputs, and token
estimates. During review, the operator compares the accepted result against the
narrower path. During publication, the team removes data that identifies private
systems, projects, people, or local state.

The operator also reviews negative cases. A failed smaller path marks a boundary
where the route needs more source material, a better retrieval index, or a
stronger acceptance check. A governance system that records only savings will
teach the team to over-trim.

Context-budget review belongs near other release checks:

- Did the claim name the evidence class?
- Did the claim keep its task scope?
- Did the acceptance check pass?
- Did the public artifact omit private system identifiers?
- Did the text avoid implying provider invoice savings where the number is an
  estimate?
- Did the result table explain which tool fits which problem?

Review prevents a private agent chapter, article, or companion repository from
publishing the operational details the runtime was supposed to govern.

## Sources and verification snapshot

The companion source register records this chapter as a dated snapshot. The
context-budget rows were checked on 2026-06-26 and cite the sanitized public
result table as the publication source:
`context-budget-public-results-2026-06-26`, at
`marketing/token-saving-public-results.md`.

Read the measurements with these limits:

- RTK and Claude Context Mode report operational savings from their own
  instrumentation. Treat them as dated runtime snapshots.
- Progressive skill loading reports static instruction footprint avoided. Treat
  it as always-on prompt mass, not provider billing.
- `claude-mem` reports a task-level memory retrieval measurement. Treat it as a
  prompt-token estimate tied to an acceptance check.
- `codebase-memory-mcp` reports source-code orientation savings. Treat it as a
  query-time result, not end-to-end task success.
- Bytes-over-four estimates are prompt-token approximations, not tokenizer or
  invoice records.

Private agent design needs this accounting. Larger context windows can carry
more material, but they do not decide what belongs in the prompt. The runtime
does. A governed agent records that decision, tests the smaller path, and keeps
public claims attached to the evidence that supports them.
