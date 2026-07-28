# From Loop Engineering to Graph Engineering: Agent Topology as a Review Surface

An agent system receives a research request and splits it across three workers.
Two return on time. The third finishes after the coordinator has already
started the merge. One timely result cites a document that belongs to another
tenant. The coordinator keeps the two timely results, calls a fallback for the
missing branch, and produces an answer from the material it has.

The runtime dashboard looks healthy: every worker ran, the merge completed, and
the answer arrived within the latency budget. A topology diagram shows the
expected diamond of one planner, three workers, and one merge.

The diagram cannot answer the incident questions.

Did the merge consume both timely results, or did it use only the fallback?
Which policy allowed the cross-tenant source to enter the route? Did the late
result update state after the answer had shipped? Which source supports the
relationship cited in the final answer? Can an auditor reconstruct the route
without retaining the user's private prompt?

Each question concerns an edge. To answer it, the incident review needs the
meaning, evidence, authority, and failure semantics of the dependency, not
merely a list of nodes and arrows.

Loop engineering can govern each worker, coordinator, and fallback as a bounded
process. It can define triggers, state, tools, budgets, retries, human gates,
and stop conditions. Those contracts still cannot answer the incident questions
because no single loop owns the dependencies between them.

This chapter calls that review layer **graph engineering**. It treats agent
topology as a set of contracts between bounded loops, durable knowledge,
authorization decisions, and outcomes. A practitioner repository read on July
25, 2026 distinguishes [knowledge
graphs](https://github.com/codejunkie99/graph-engineering/tree/cfacb56a05a31ba69bf84d0b8b00f5ce463127ef),
which represent what agents remember, from [task
graphs](https://github.com/codejunkie99/graph-engineering/blob/cfacb56a05a31ba69bf84d0b8b00f5ce463127ef/graph-engineering/references/task-graphs.md),
which represent how agents work. Its most useful operational instruction is
blunt: “delete fake edges: an arrow is real only when work flows through it.”
Under this review, an edge carries work only when downstream state depends on
an upstream result. The evidence must show that dependency.

The repository supplies a useful lens rather than an audit standard. The
protocol here combines provenance models, graph constraint validation,
distributed tracing, privacy controls, and ordinary software review. A verdict
covers only the declared checks and inspected executions; it does not certify
every run of the system.

## Move from loop contracts to system topology

Loop engineering begins with one bounded unit of work. Its contract states what
starts the loop, which state it reads and changes, which tools and data it may
use, how it handles budgets and approval, and which outcome closes it. A team
can test the contract without representing the whole system as a graph.

A system such as Amber, an open-source Hybrid GraphRAG service that ingests
documents into a tenant-scoped knowledge graph, contains many units that fit
this model. A chunk job can receive input, extract entities and relationships,
write accepted output, record an outcome, and stop. Once jobs run in parallel,
write shared knowledge, or feed later routes, the review crosses a boundary:
which result reached the shared graph, which source supports a persisted
relationship, which tenant policy authorized the action, and which consumer
used the result?

The transition occurs when independently governed loops exchange results,
mutate shared state, fan out and join, or rely on durable relationships. Every
loop may satisfy its own contract while the system ignores one branch, repeats
a write, accepts stale knowledge, or loses the source behind a decision.

Graph engineering works alongside loop engineering and requires no graph
database. It adds contracts at the boundaries:

```text
bounded loop
  -> execution edge
  -> bounded loop

source evidence
  -> knowledge edge
  -> durable claim

request
  -> authority and route
  -> output and recorded outcome
```

The unit of review changes at this boundary. Loop engineering asks whether one
process followed its contract. Graph engineering examines whether the
dependencies between contracts carry evidence, authority, provenance, and
failure semantics.

## Decide whether graph review belongs here

The transition depends on system behavior, not storage shape. A system can
use Neo4j, RDF, or a workflow canvas without needing graph engineering. Storage
shape alone says little about operational risk. Start with the decisions and
routes the system must support.

Use a topology review when at least one condition holds:

- more than one bounded loop exchanges results through shared or asynchronous
  state;
- a decision depends on a multi-hop traversal across durable knowledge;
- execution contains fan-out, joins, asynchronous branches, delegation,
  fallback, or independently failing work;
- a consequential result must be reconstructed across sources, execution, an
  authority decision, and an outcome.

A prospective design should also face a simpler baseline. Write the acceptance
cases before choosing the representation. Each case names the required query or
route, expected state transition, necessary source support, scale constraint,
and failure behavior. Then ask whether a table, queue, state machine, or
sequential trace passes the same cases.

If the simpler design passes them all, keep the simpler design. Count the
components, schemas, and failure modes that each option asks the team to
operate. Those counts explain the choice; they are not a universal cost model.

For an operating graph, discovering that a table could replace it supports a
simplification recommendation. The deployed graph still needs review because
its authority boundaries, retention rules, and failure paths remain active
until the team removes them.

This admission step catches graph theatre, in which a team redraws a sequence
as nodes and arrows without gaining a testable property. It also catches
premature graph infrastructure: schema migration, traversal, synchronization,
and observability costs accepted before the team can name a query that needs
them.

## Review three surfaces separately

Agent topology crosses three surfaces: knowledge relationships, execution
transitions, and decision lineage. They can share identifiers, but they do not
share one useful edge schema.

Decision lineage, the third surface, is more than a join across the other two.
The components that do the work write knowledge and execution records, keep
them for their own operational needs, and expose them mostly to operators. A
lineage record serves a later reader who must reconstruct one consequential
decision. It keeps only what that reconstruction requires and carries its own
purpose, access, and deletion rules. Even complete knowledge provenance and
execution traces may leave a decision opaque if no record connects the request
to its sources, authority, and outcome.

### Knowledge relationships

A knowledge edge connects durable claims, entities, sources, chunks, events, or
concepts. Its contract should say what the relationship means, where its support
comes from, how long it remains valid, who may read or change it, and who owns a
conflict.

The [W3C PROV Data Model](https://www.w3.org/TR/prov-dm/) gives this surface a
stable vocabulary. PROV distinguishes entities, activities, and agents, then
describes generation, use, derivation, attribution, and delegation among them.
Although it does not define this review, it shows why provenance requires more
than a `source` string attached to a node.

Consider:

```text
(ALICE)-[WORKS_FOR]->(ACME)
```

The edge may have come from a contract, an old directory, a model extraction,
or another graph. Those sources carry different authority and expiry rules. A
reviewer needs the source locator, assertion time, extraction activity, tenant,
confidence or assertion class, and conflict policy. Without them, the graph can
return a clean path whose facts no longer agree.

Knowledge constraints also need mechanical checks. [SHACL](https://www.w3.org/TR/shacl/)
defines shapes and validation reports for RDF graphs; a team can use it to
require properties, restrict edge types, or verify cardinality. A property
graph needs another validator, such as schema constraints and application
tests, because SHACL does not transfer unchanged to Neo4j. What transfers is
the discipline of declaring constraints and retaining a conformance report.

### Execution transitions

An execution edge says that one unit of work affects another. A parent span
alone does not establish that dependency. The downstream job must consume an
identifier, field, digest, state transition, or decision produced upstream.

For each execution edge, record:

- predecessor, consumer, and triggering condition;
- input and output state;
- consumed-result binding;
- timeout, cancellation, retry, and idempotency behavior;
- fallback and partial-result semantics;
- join owner;
- required authority and observed authorization evidence;
- trace or log locator.

The [OpenTelemetry Trace API, version
1.55.0](https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/specification/trace/api.md)
defines spans, parent contexts, links, events, and status. Those primitives can
show that work ran and how telemetry connected it, but they cannot prove that a
business result was correct or that a consumer used a predecessor's output.

That distinction catches fake edges. Suppose a research worker emits
`result_id=r-41`, while the merge span begins after the worker finishes. Timing
and parentage show correlation. A stronger record binds `r-41` or its digest to
the merge input. If the merge transforms the result, record the field mapping and the resulting
binding. A prose explanation supports a design review but cannot prove that the
inspected execution consumed the result.

### Decision lineage

Decision lineage connects a request to selected sources, authority, execution,
outcome, and retained evidence. A useful record answers:

```text
request
  -> evidence selected
  -> authorization decision and enforcement
  -> execution transitions
  -> decision or output
  -> recorded outcome
```

The authority hop needs instance-level data: principal or service identity,
policy decision and version, enforcement point, granted scope, and an
authorization-evidence locator. A field named `required_role` describes intent,
but does not show who permitted the inspected action.

Lineage can create its own privacy problem. Retaining every prompt, source
excerpt, tool output, and internal model trace may produce a detailed audit log
at the cost of building a second sensitive datastore. Keep the minimum
reconstruction record, with purpose, data classification, access scope,
retention, deletion, and redaction rules attached to each retained field.

The [NIST Privacy Framework
1.0](https://doi.org/10.6028/NIST.CSWP.01162020) treats privacy as a data
processing risk across a system lifecycle. That view fits all three surfaces:
knowledge items, execution telemetry, and lineage records can each contain
protected data. Applying controls only to the final decision record leaves the
other two exposed.

## Walk one route through its edges

A topology review should begin with one route, not with the entire system. Pick
one path that contains a dependency worth testing: a fan-out, join, fallback,
shared write, retrieval step, or authority boundary. State what the route should
do, what may fail, and which evidence would show that each dependency worked.

The review unit is a **declared check**. Each check connects one requirement to
one edge or route condition. A compact ledger needs five things:

| Field | Purpose |
|---|---|
| Requirement | What the dependency must guarantee |
| Target | The edge, route, or failure case under review |
| Evidence | The trace, record, source, or policy used to judge it |
| Status | Supported, partial, unsupported, inconclusive, or not applicable |
| Owner | Who resolves the gap |

*Table: Minimal reading view for a declared check.*

The status belongs to the check, not to a vague component called “the graph.”
One route may contain supported and unsupported dependencies at the same time,
as these two filled rows show:

| Requirement | Target | Evidence | Status | Owner |
|---|---|---|---|---|
| The merge consumes the first worker's result | `W-1 -> M-9` | `trace://t-18/span-m9#input.res-31` binds the result identifier to the merge input | Supported | research-platform |
| A late branch cannot mutate state after the join closes | `W-3 -> M-9` | Join closure is documented; no execution shows what happened to the late write | Unsupported | research-platform |

*Table: Two checks on the same route can reach different conclusions.*

The record from the executed path closes the first row by naming the consumed
result. The second stays open: its only evidence describes intent, and no
inspected run exercised the late branch.

Those five fields form the reading view. A machine-checkable packet also records
the applicability of each register row, the rows on which the check rests, the
rationale for the status, and a trust class for each piece of evidence. The
class distinguishes, for example, a trace from an independent collector from a
claim typed into a document.

Use the trust class to describe how the evidence was produced, not to automate
the verdict:

- `T1` is evidence collected independently from the component under review and
  protected by an integrity control, such as a trace from a separate collector
  with a recorded digest.
- `T2` is owner-produced evidence protected against later mutation or
  corroborated by another record. A reviewer must still decide whether it can
  support the specific check.
- `T3` is a design assertion, diagram, configuration claim, or uncorroborated
  owner statement. It can support a review of intent, but cannot by itself
  support an execution, authority, privacy, recovery, or consequential-outcome
  check.

The structural validator checks that the class and evidence references exist.
It does not decide whether an item is truthful or sufficient for the check.

Write a separate contract for each surface. For a knowledge edge, capture
meaning, provenance, a checked date, a validity rule, an authorization scope,
merge and conflict handling, and an owner. For an execution edge, capture the
predecessor, consumer, consumed-result evidence, failure semantics, required and
observed authorization, telemetry locator, and owner. A lineage link holds the
minimum identifiers connecting request, sources, authorization, route, output,
and outcome, along with the purpose, classification, retention, and deletion
rules for those identifiers.

Keep these contracts in a structured form that the team can validate. Automated
checks should catch missing fields, broken references, invalid edge types, and
incomplete coverage. This repository carries a worked version of that packet:
[`templates/topology-audit-schema.json`](../templates/topology-audit-schema.json)
declares the registers, evidence entries, and checks;
[`tools/topology_audit_validate.py`](../tools/topology_audit_validate.py) runs
the structural rules; and
[`evidence/topology-audit-positive.json`](../evidence/topology-audit-positive.json)
shows one route that passes, next to negative packets that fail on a missing
field, an invalid status, a duplicate identifier, a dangling reference, a route
gap, and an unmapped requirement. Human review still decides whether the
relationship means what the label claims, whether the source supports it,
whether the authority matches the action, and whether the retained data is
proportionate. The validator reports a structural `PASS` or `FAIL` on the packet
itself; the review verdict below is a separate judgment about the system.

Consider a research route:

```text
request
  -> retrieval and authorization
  -> parallel workers
  -> merge
  -> answer
```

The workers may all finish, yet the merge may consume only one result. Bind a
stable result identifier or digest from each worker to the merge input. If a
branch arrives after the join closes, the route must show whether the system
discarded it, cancelled it, or allowed it to mutate shared state.

Follow the same route across the knowledge surface. A cited relationship should
retain the document or chunk that supports it, the tenant or access scope, and
a rule for staleness or conflict. An answer-level citation cannot repair a graph
edge that lost its own provenance.

Then follow authority. A configuration field such as `tenant_scoped: true`
describes intended policy. Evidence from the enforcement point must identify
the identity, policy decision, granted scope, resource boundary, and outcome for
the inspected route. Returning the right data by accident proves nothing about
the authorization contract.

Record the outcome as complete, degraded, failed, cancelled, or skipped. A
generic success flag hides partial joins and fallback behavior.

### Keep the edge contracts small

The three contracts do not need one universal schema. They need enough structure
to expose the questions that each surface creates.

A knowledge relationship can remain compact:

```yaml
surface: knowledge
relationship_meaning: WORKS_FOR, as asserted by a signed contract
provenance_status: document/chunk identifier retained
checked_date: date the assertion was last confirmed
validity_rule: current, expired, or unknown
authorization_scope: tenant identifier
conflict_rule: preserve competing assertions
owner: knowledge-platform
```

An execution transition needs different fields:

```yaml
surface: execution
predecessor: research-worker
consumer: merge
consumed_result_evidence: trace locator binding the worker result identifier
failure_semantics: timeout, retry, cancellation, fallback
partial_result: mark output as degraded
required_authorization: tenant-read
observed_authorization: enforcement-point decision identifier
telemetry_locator: trace identifier
owner: research-platform
```

A lineage record connects the two without retaining every payload:

```yaml
surface: lineage
from_id: request identifier
to_id: output identifier
source_references: selected source identifiers
authorization_decision: decision identifier
execution_route: execution trace or route identifier
outcome: complete, degraded, failed, cancelled, or skipped
purpose: why the record is retained
retention_rule: how long each field survives
```

These examples describe contracts rather than mandatory storage schemas. They
use the field names from the packet schema in this repository, and each shows a
readable subset; the schema requires the remaining fields before a row counts
as complete. The records may live in JSON, relational tables, graph properties,
telemetry attributes, or several linked stores. The review concerns continuity
across their identifiers and the meaning assigned to each edge.

### Read the route from dependency to dependency

Start with the request boundary. Record the route class, data scope, and purpose
without copying a private prompt into every review artifact. The request should
carry an identifier that retrieval, authorization, workers, and outcome records
can reference.

At retrieval, temporal proximity is weak evidence. The query should bind the
request identifier, tenant or access filter, selected source identifiers, and
retrieval policy. Nearby events may still belong to different requests or
scopes.

At authorization, inspect the decision that the system enforced. A boolean such
as `authorized=true` hides the principal, policy version, resource boundary,
and granted scope. It also prevents reviewers from distinguishing a correct
decision from a permissive default or an unhandled error.

At fan-out, compare worker inputs as well as outputs. A parallel topology can
send the same material to every worker and pay for duplicate work while the
diagram still looks correct. Each worker should receive a bounded source set
and return a result identifier tied to it.

Give the join a named owner. Its contract states when the join closes, which
branches are required, how optional branches affect the outcome, and whether
late results can change shared state. If the merge uses a fallback, report that
fact in the outcome rather than an undifferentiated success.

Trace answer claims back through the knowledge surface. A final citation may
identify the chunk supporting a sentence even though the graph traversal that
selected the relationship has lost its source. Claim verification and edge
provenance answer different questions, so one cannot stand in for the other.

User feedback belongs after the outcome. It can reveal a bad answer or route,
but a positive rating cannot prove authorization, provenance, or result
consumption. It records the user's response, not the correctness of the
topology.

## Challenge the paths diagrams omit

Normal-path diagrams hide the conditions that break distributed agent systems.
Review at least the failure modes that the route can produce:

| Challenge | Contract question |
|---|---|
| Duplicate output | Which idempotency rule prevents a second effect? |
| Late result | Can it mutate state after the join or answer closes? |
| Partial join | Does the outcome report degraded completion? |
| Lost branch | Which fallback runs, and under which authority? |
| Retry | Can it duplicate a write, charge, or external action? |
| Cyclic dependency | Which rule detects the cycle before the route deadlocks or loops? |
| Out-of-order arrival | Does the route depend on wall-clock ordering across hosts? |
| Stale knowledge | Which validity rule rejects or labels the edge? |
| Contradictory source | Does the graph preserve both claims and provenance? |
| Schema migration | What happens to edges written under the previous contract? |
| Cross-tenant attempt | Which enforcement point denies access? |
| Deletion request | Which stored and derived copies disappear? |

*Table: Failure challenges expose contracts hidden by the normal path.*

Begin with existing traces, replay, or simulation before moving to fault
injection. Cross-tenant, destructive, and privacy tests belong in an isolated
environment with synthetic data. Derive expected behavior from a policy,
contract, or acceptance case. If the team has no agreed expectation, mark the
result inconclusive rather than inventing one after the test.

A concise verdict is enough. `PASS` means every declared check is supported or
not applicable. `CONDITIONAL` means bounded gaps remain with active mitigation
and an owner. `BLOCKED` means coverage is incomplete, evidence contradicts the
contract, authority remains unclear, or a material privacy or recovery gap stays
open.

Close a finding with new evidence from the changed route. A code change,
diagram, or configuration claim cannot close a missing consumed-result binding.
The producer must emit the result identifier, the consumer must bind it to its
input, and a later execution must show the connection. Provenance and
authorization gaps close the same way: with evidence from the path that
performs the action.

## Use Amber to trace the transition

Amber makes the transition concrete. Its public code combines bounded chunk
processing, parallel execution, tenant-scoped graph writes, persistent
knowledge relationships, and execution metrics. The observations below cover
only the inspected public paths.

### Start with a bounded chunk job

A chunk-processing job fits the loop-engineering model: it receives a chunk,
runs extraction, writes accepted entities and relationships, records timings or
errors, and stops. Its contract can define the input, tools, budgets, retry
behavior, terminal outcomes, and authority.

Amber's graph processor launches asynchronous work per chunk with
`asyncio.gather` and records extraction and write timings, entity and
relationship counts, cache hits, and errors. Those metrics show that the chunk
jobs ran, but not which result became which persisted relationship or whether a
later route consumed it.

### Follow the result into the knowledge graph

Amber's extraction prompt asks the model to preserve a text-unit identifier for
provenance. The structured relationship output contains source, target, type,
description, and weight, while the graph writer persists description, weight,
tenant, and creation time. The reviewed path does not attach the source document
or chunk to the relationship itself.

Provenance in that path stops one hop short. The writer connects each chunk to
the entities it mentions, so a reviewer can ask which chunk introduced an
entity. No equivalent link survives for the relationship between two entities,
which is the claim an answer usually cites.

The writer also merges each relationship onto a single edge per source, type,
and target. A later extraction updates the weight while leaving the first
description in place. Two disagreeing sources therefore collapse into one edge
instead of remaining separately inspectable.

That produces a small set of topology observations:

| Observation | Assessment |
|---|---|
| Relationship endpoints use tenant-scoped matches | Supported in the reviewed writer path |
| A relationship retains its source chunk | Not supported in the reviewed path |
| An entity retains the chunk that mentioned it | Supported |
| Relationship creation time is recorded | Supported |
| Conflicting source assertions remain distinguishable | Not supported in the reviewed path |

*Table: Amber graph-write observations from the inspected public path.*

The tenant-scoped writer supports endpoint isolation at that write step. Its
scope says nothing about extraction input, entity creation, retrieval, or later
traversal; those edges require their own contracts.

The creation timestamp also has a narrow meaning. It records when the system
created the relationship record. It does not say when the source published the
assertion, when the fact became true, or when someone last checked it. Staleness
decisions depend on keeping those meanings separate.

### Add the topology bindings

The processor metrics and writer statement reveal the boundary of loop-level
evidence. One record shows that work ran; another shows that an edge was
created. Neither binds one chunk result to one persisted relationship or proves
that a later route used it.

A topology-aware implementation would propagate source evidence through the
extraction result, retain it on the relationship, emit a stable result binding
for the write, and connect later retrieval or traversal to the relationships it
consumed. The chunk loop contract remains in place; these additions connect it
to the rest of the system.

## Keep graph engineering at the dependency boundary

Agent systems already need loop contracts, governed knowledge, context budgets,
and independent verification. Graph engineering connects those controls at
their dependency boundaries, leaving their full procedures with the systems
that own them.

The loop contract owns triggers, durable state, tool exposure, budgets, human
gates, and stop conditions. Graph engineering records execution edges between
loops, proves result consumption, and tests how failures propagate across them.

The governed knowledge layer owns ingestion, source lifecycle, access, merge
policy, and maintenance. Graph review picks up the durable relationships those
processes produce and checks whether each edge retains source support, validity,
authority, and an owner.

Context governance decides which material enters a model call. Graph
engineering records which selected context crossed an execution edge and
whether the downstream node consumed it; token measurement and route-specific
context budgets remain with context governance.

Independent verification checks claims, sources, leakage, and artifact quality.
Graph engineering attaches those results to edge and route checks, avoiding a
review in which one model grades its own execution.

This division keeps the review focused. Link edge contracts to existing loop
contracts, source records, context decisions, and verification results. Copying
all of them into one document only creates another artifact that ages faster
than the system.

## Common failure modes

### The diagram supplies the evidence

The team treats a Mermaid or architecture diagram as proof that dependencies
exist, although the diagram records only intent. Require a consumed-result
binding for execution and a source locator for knowledge.

### One edge schema covers every surface

A generic record with `from`, `to`, `type`, and `metadata` can store many
things, but cannot enforce the different review questions for provenance,
execution, and lineage. Keep separate registers even when the database uses one
physical edge model.

### Every span becomes a task dependency

Instrumentation often mirrors call structure, and a child span may exist only
for logging, prefetch, or an independent side operation. Draw a dependency edge
only after showing that downstream state used the result.

### The audit samples one happy path

A normal trace hides partial joins, retry effects, late results, and authority
changes inside fallback. Coverage remains open until failure and fallback
strata are included.

### The team scores maturity

Without a validated rubric and calibration set, a numerical maturity score
creates false precision. Findings with impact, owners, and closure evidence
give the team a clearer work queue.

### Lineage becomes surveillance

Under the label of traceability, an audit store can accumulate private prompts,
retrieved documents, and model internals. Apply purpose, minimization, access,
retention, redaction, and deletion to every retained surface.

### A graph hides a sequence

If every job waits for the previous job and consumes the full accumulated
state, one agent or a state machine may give the team a smaller failure surface.
The study [*Towards a Science of Scaling Agent
Systems*](https://arxiv.org/abs/2512.08296v3) (version 3, April 2026) evaluated
260 configurations across six agentic benchmarks, five architectures, and three
model families, and found that coordination effects depended on task structure.
Relative change against the single-agent baseline ranged from +80.8% on
decomposable financial reasoning to -70.0% on sequential planning. Treat those
results as evidence about the evaluated architectures and benchmarks, not as a
universal performance promise.

## A staged adoption path

Start with one bounded loop and one dependency that carries its output. Name the
producer result, bind it at the consumer, and inspect a normal path alongside
one fallback and one failure path. This small exercise often reveals fake edges
without introducing a graph database.

Add provenance to one durable relationship class next. Record source support,
validity, tenant or access scope, conflict handling, and an owner, then exercise
one stale or contradictory-source case.

Connect execution and knowledge with minimum decision lineage. Preserve the
identifiers that join request, selected sources, authorization, route, output,
and outcome. Set retention and access rules before collecting payloads.

Expand the review when the system adds a branch, changes join behavior, creates
a new relationship class, changes tenant policy, introduces a new store, or
reveals an unlisted failure path. Review the affected dependencies rather than
redrawing the whole architecture.

## Operating the system

In ordinary operation, a topology review covers one route at a time. The
declared checks sit beside existing loop contracts, source records, and
verification results. A change to a branch, join, or relationship class reopens
only the checks it touches, so the team revisits disturbed dependencies instead
of redrawing the architecture on every commit.

Edge contracts make that review possible. To answer an incident question, a
reviewer follows recorded identifiers from request to sources, authority,
execution, and outcome, then reads each check's status, evidence, and owner. An
open check has operational value because it names the dependency that no
inspected run has yet shown to work.

Redrawing a topology cannot close a missing consumed-result binding or recover
a lost source. Loop engineering shows whether each bounded process followed its
contract. When a team must trace a dependency from meaning to evidence,
authority to execution, and execution to outcome, a topology review adds the
edge contracts needed to challenge that dependency.

## Sources and verification snapshot

Verification date for the sources and code paths below: July 25, 2026. The
practitioner material is pinned to commit
`cfacb56a05a31ba69bf84d0b8b00f5ce463127ef`; the Amber observations are pinned
to commit `701e7406beb9987cf3b73b826ebfc98c277f8941`.

- [Graph Engineering practitioner repository](https://github.com/codejunkie99/graph-engineering/tree/cfacb56a05a31ba69bf84d0b8b00f5ce463127ef)
- [Task graphs and the fake-edge test](https://github.com/codejunkie99/graph-engineering/blob/cfacb56a05a31ba69bf84d0b8b00f5ce463127ef/graph-engineering/references/task-graphs.md)
- [W3C PROV Data Model](https://www.w3.org/TR/prov-dm/)
- [W3C Shapes Constraint Language](https://www.w3.org/TR/shacl/)
- [OpenTelemetry Trace API, version 1.55.0](https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/specification/trace/api.md)
- [Kim et al., *Towards a Science of Scaling Agent Systems*, version 3](https://arxiv.org/abs/2512.08296v3)
- [NIST Privacy Framework 1.0](https://doi.org/10.6028/NIST.CSWP.01162020)
- [Amber snapshot](https://github.com/yuzushi-dev/Amber/tree/701e7406beb9987cf3b73b826ebfc98c277f8941):
  graph processor
  (`src/core/graph/application/processor.py`), graph writer
  (`src/core/graph/application/writer.py`), extraction path
  (`src/core/ingestion/infrastructure/extraction/graph_extractor.py`), and
  extraction prompt
  (`src/core/generation/application/prompts/entity_extraction.py`)

The packet schema, validator, and example packets referenced above live in
[`templates/`](../templates/topology-audit-schema.json),
[`tools/`](../tools/topology_audit_validate.py), and
[`evidence/`](../evidence/topology-audit-positive.json) in this repository.

The review model in this chapter is an authorial synthesis rather than a formal
audit standard. Teams should adapt it to their architecture, risks, and
evidence.
