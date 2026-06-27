# Governing Context Budgets in Private Agent Systems

A developer asks a coding agent a narrow design question. The agent opens
files, reads command output, loads project instructions, sees tool schemas,
scans memory, and pulls snippets from search. The answer may help. The run paid
for every chunk the agent packed into the prompt.

The visible cost is tokens, latency, and expensive retry loops. The harder
failure comes later. The agent starts carrying stale notes, duplicate
instructions, broad tool descriptions, and half-relevant code into tasks that
needed a small slice of the system.

Large context windows do not remove the runtime decision. A private agent still
needs a harness that decides what belongs in context, why it belongs there, and
which smaller path could have answered the same request.

This chapter treats context budget as a governance surface. The question is not
only "how many tokens did the stack save?" The better question is: which state,
memory, source files, and tool outputs entered the model call, and can an
operator inspect that choice after the fact?

## Context belongs in the runtime contract

Private agent systems already need runtime decisions around identity, data
classification, tool permissions, memory, retrieval, model routing,
observability, and approval policy. Context budget belongs in that same
contract.

Each extra token can carry data the model did not need. A stale memory can bias
the answer. A broad repository read can expose files outside the task. A plugin
instruction can expand the agent's authority. A noisy shell command can bury
the one line that showed the failure.

The harness should answer a small set of questions before the model call:

- Which state did the agent load?
- Which tool output entered the prompt?
- Which memory item affected the run?
- Which source files did the agent read?
- Which narrower context path could have answered the same question?

Those questions turn context packing from an invisible convenience into an
auditable runtime decision.

## Separate the evidence classes

Token-saving claims become misleading when they collapse different measurements
into one number. Separate them before comparing tools.

**Runtime-reported savings** come from a tool that records its own filtering
during normal work. These numbers carry operational weight because the tool saw
the commands or context operations as they happened.

**Static footprint avoided** estimates instruction mass kept outside the
always-on context. Skills, plugins, and project files can add large capability
surface. Progressive loading saves prompt space when the agent loads only the
skill a task triggers.

**Task-level A/B measurements** compare two workflows on the same task. One
path reads broad context. The other path searches, filters, or queries a
structured index before fetching detail. These tests need an acceptance check,
because a tiny prompt that misses the answer did not save useful context.

This split makes claims inspectable. A plugin README can claim savings. A local
audit can show what your stack saved on your tasks.

## Audit snapshot

The companion repository includes a dated, sanitized context-budget audit. One
local token-saving tool was excluded from the measurement set. The audit
snapshot was generated on 2026-06-26 and covers shell-output filtering, context
masking, progressive skill loading, external memory workflow tests, and
codebase graph queries.

RTK reported **23.8 million shell-output tokens saved**, a **63.70% reduction**,
across **22,909 observed commands**. This number captures command-output
filtering, not total agent cost. It changes as the local machine runs more
commands, so treat it as a dated runtime snapshot.

Claude Context Mode reported **1.10 million tokens saved** across **20
session-stat files**, with a **50.95% average reduction**. It also kept
**4,407,150 bytes** out of active context.

Progressive skill loading kept a large instruction surface out of the always-on
layer. The local Codex skill bodies measured about **151,339 estimated
tokens**. The Claude skill bodies measured about **170,589 estimated tokens**.
This is avoided always-on footprint, not a provider-billed runtime saving.

`claude-mem` passed a workflow benchmark with a caveat. The installed real
database had zero sessions, prompts, observations, and summaries at measurement
time. The benchmark used a deterministic synthetic corpus shaped like memory
observations. The baseline fetched full details for every search result. The
optimized workflow showed compact search rows first, then fetched selected
observation IDs. That path reduced the prompt from **6,762** estimated tokens
to **2,606**, saving **4,156 tokens**, or **61.46%**, while retrieving all six
relevant synthetic observations in the filtered set.

`codebase-memory-mcp` produced the clearest query-time result on one anonymous
private repository. The tool indexed **125 files**, **637,489 bytes** of
source, and built a graph with **1,450 nodes** and **6,055 edges**. The index
database measured **7,471,104 bytes** and took **1.75 seconds** to build on the
test machine.

The index used more disk than the source slice it indexed. The saving came at
query time. For one feature-area orientation task, the baseline path would have
loaded **44,917 estimated source-reading tokens**. A structured graph query
returned the needed orientation in **704 estimated tokens**. That avoided
**44,213 estimated prompt tokens**, a **98.43% reduction** for that step.

For an architecture overview, the baseline path would have loaded **159,372
estimated tokens** from the indexed source surface. The structured result used
**1,050 estimated tokens**, avoiding **158,322 tokens**, a **99.34% reduction**.

These numbers do not prove end-to-end task success. They show that structured
queries can answer orientation steps without dumping source files into the
model.

## Choose the tool by context problem

Different context-budget tools solve different problems. A governed stack can
use several of them, but each should have a narrow job.

| Tool or pattern | Best use | What it does not solve |
|---|---|---|
| RTK | Shell-heavy coding runs with noisy command output | Memory, source permissions, long-term state |
| Claude Context Mode | Keeping large tool outputs outside active context until needed | Data classification, approval policy |
| Progressive skill loading | Loading task-specific procedures instead of a full instruction library | Runtime proof that a task succeeded |
| `claude-mem` | Search, filter, fetch workflow for long-term memory records | Retention policy or privacy review by itself |
| `codebase-memory-mcp` | Source-code orientation before reading files | Disk footprint, index maintenance, final code review |
| Audit scripts and public tables | Publishing or comparing context-budget claims | Acceptance without task-specific checks |

: Context-budget tools by primary purpose

Use RTK when build logs, test output, search output, and command noise can
dwarf the relevant line. Use Context Mode when large tool outputs or file reads
should stay outside active context until the agent needs them. Use progressive
skill loading when a procedure, domain convention, or safety check belongs in a
task-specific file rather than in the always-on prompt.

Use `claude-mem` for past decisions, project observations, and user or team
preferences that need retrieval over time. The runtime should search compact
rows first, select records under policy, and fetch details only for records
that matter. Memory should not mean loading the past into every run.

Use `codebase-memory-mcp` for source-code orientation. It fits questions like
"where is this concept defined," "who calls it," and "which files matter." The
graph index costs disk and indexing time. It pays off when the agent can inspect
names, files, call paths, and architecture summaries before reading source.

## Record context decisions in traces

A private agent should record context decisions the same way it records tool
calls. A useful trace should show the request, data class, route, loaded state,
retrieved sources, tool outputs, token counts, and acceptance result. If a user
challenges the answer, the operator should see which memory item, file, or tool
output influenced it.

Context budget also belongs in approval policy. A repository query with bounded
read access may need no human approval. A broad scan across private files may
need a higher bar. A memory fetch that exposes user preference data needs a
policy decision. A plugin that adds write tools needs a capability review.

Cost and governance meet at the prompt builder. The prompt builder decides
whether the model sees a whole file, a snippet, a graph row, a memory summary,
or nothing. That decision affects billing, latency, privacy, and answer
quality.

## Run a local context-budget audit

The companion material gives you three small scripts:

- `tools/token_saving_audit.py` summarizes runtime-reported savings and static
  footprint. Its Markdown output redacts local details by default.
- `tools/claude_mem_ab_benchmark.py` tests a search, filter, fetch memory
  workflow against a synthetic corpus when the real memory database is empty.
- `tools/codebase_memory_mcp_benchmark.py` compares codebase graph outputs
  against source-reading baselines for orientation steps.

Start with one workflow. Measure the broad-context baseline. Measure the
structured path. Keep the acceptance test beside the token count. If the
smaller context produces the right answer, you have a saving worth discussing.

Do not publish raw generated reports unless you have reviewed them for local
paths, repository names, database labels, and private tool names. Publish the
sanitized table in `marketing/token-saving-public-results.md`, or regenerate a
redacted report from the scripts.

## Limits of the numbers

These measurements are not provider invoices. RTK and Context Mode reported
their own operational savings. Static skill counts use a chars-over-four
estimate. The repository measurements estimate prompt tokens avoided during
codebase orientation. The `claude-mem` result comes from a synthetic benchmark
until the real memory store has enough data from normal work.

The numbers remain useful because they separate claims. A tool can save tokens
in one part of the run and add risk somewhere else. A memory system can reduce
context load and require retention rules. A graph index can shrink prompts and
consume disk. A plugin can add capability and expand the supply-chain boundary.

Private agent design needs that accounting. You do not get a governed system by
buying a larger context window. You get one by deciding what enters the context,
proving why it entered, and testing whether a smaller packet would have done the
job.
