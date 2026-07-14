# How to Trust a Liar: Verifying Model Claims in Private Agent Systems

A reviewer asks an agent whether the release is ready. The agent answers in a
calm, complete paragraph: the tests pass, the changelog is updated, the cited
benchmark shows a thirty percent improvement, and the source for that number is
a file in the repository. Every sentence reads like the truth. One test was
never run. The changelog line was invented. The benchmark exists, but it
measured something else. The file the agent cited is not in the repository at
all.

Nothing in that answer looks wrong, which makes the failure hard to catch. A
language model does not signal the difference between a fact it retrieved and a
fact it produced to fit the shape of the sentence. The same fluent register
carries both. A careful reader may detect the seam in prose. An agentic system
can hide it inside file changes, tool calls, and status reports that appear
complete.

This chapter is about working with a component that can produce a confident
falsehood at any moment, and building a system whose claims a reviewer can still
trust after the run is over. The goal is not to assume that a production model
will never confabulate. No current system should be trusted on that basis. The
goal is a runtime that assumes confabulation is always possible and refuses to
let an unverified claim pass as a verified one.

## Confabulation is not lying

The title uses a metaphor that needs a clear boundary. In system-design terms,
the model is an unreliable witness rather than a malicious actor. Those failure
modes require different defenses. You do not interrogate a witness for motive;
you corroborate the testimony against independent evidence.

A lie needs intent and a model of the truth the speaker chooses to hide. A
deployed language model should not be treated as possessing human intent or a
reliable, persistent model of truth. It predicts plausible continuations. When
the training distribution and the prompt make a false statement the most
plausible continuation, the model can produce it with the same confident
register it gives a true one. The word for that is confabulation, not deception:
a fluent, coherent account that fills a gap with invention rather than fact.

This distinction changes the engineering response. You cannot appeal to the
model's honesty, because there is no dishonesty to correct. You cannot rely on
it to identify every part it invented: a base model does not maintain a
dependable provenance ledger for each claim it emits. The runtime must create
and preserve provenance outside the model. A model asked "are you sure?" may
revise a correct answer into an incorrect one when it reads the follow-up as
evidence that the previous answer was unwelcome. A follow-up prompt produces
another continuation shaped by the conversation, not a dependable provenance
check.

An agentic system cannot derive trust from the model's account of itself. Trust
has to come from the runtime around the model: the components that check claims,
preserve evidence, and block release. A private agent system already owns
identity, tool access, memory, retrieval, state, routing, and approvals.
Verification belongs in that runtime as a first-class control rather than a
polite request added to the prompt.

## Why a model cannot grade its own work

A common verification design is also an insufficient one: ask the model to
review its own output. It is cheap, it requires no new infrastructure, and it
often produces a reassuring second paragraph that says the work is fine. As the
sole verification control, it fails for a structural reason rather than a
quality reason.

A model that confabulated a claim has no separate, dependable record of having
done so. When it re-reads its output, the confabulated claim appears as ordinary
text, indistinguishable from the rest. The same process that produced the error
now has to find it, using many of the signals that made the error plausible. A
self-review can catch formatting slips, internal contradictions, and some
reasoning errors. It should not serve as the only verification of factual
claims.

Research on intrinsic self-correction is mixed. Huang and colleagues found that
models often struggle to improve reasoning without external feedback and can
degrade their answers. Liu and colleagues reported intrinsic self-correction
under more constrained conditions, including unbiased prompts and zero
temperature. That disagreement supports the operational conclusion used here:
self-review may help, but it should not be the only process allowed to verify
the maker's claims.

Separate the party that makes a claim from the party that checks it. Give the
checker evidence the maker cannot influence: an independent process, a different
context, a deterministic test, or a human with the authority to reject. The
maker produces the artifact; the checker decides whether it passes. The maker
cannot approve its own output, and the checker has no stake in the output
passing.

Five controls apply this split to common failure modes. Each control names the
failure, the mechanism that catches it, and the evidence a reviewer can inspect.

## Separate the author from the verifier

Every later control depends on a separate verifier. If the maker can approve its
own work, it can route around the remaining checks. The verifier therefore needs
an execution boundary the model cannot modify.

The checker is a distinct step, not a prompt that asks the model to grade
itself. It reads the produced artifacts and applies fixed rules. It checks
whether every required file exists, whether the artifacts agree, and whether the
output stays inside its declared boundaries. The checker emits a scope decision
and lists the artifacts it inspected. A decision without an inspection list is
an opinion, not a verification. Mechanical checks must also remain separate from
release approval. A compact report makes that boundary visible:

```yaml
checker_report:
  scope_decision: MECHANICAL_PASS
  release_status: BLOCKED_PENDING_HUMAN_REVIEW
  scope:
    - structure
    - integrity
    - consistency
    - leakage
  inspected:
    - article.md
    - source-register.json
    - leakage-review.md
  findings: []
  source_support: HUMAN_REQUIRED
  content_quality: HUMAN_REQUIRED
```

The report says what was decided, on which artifacts, in which scope, and what
it deliberately did not judge. A reader can disagree with it on the evidence,
because the evidence is named.

A maker allowed to write "verified" into its own output has produced a string,
not a verification; the word has to be earned by a process the maker did not
run. The test of the boundary is simple: if the maker could make the checker
pass by writing more confident prose, the boundary is broken. A real checker
passes or fails on facts about the artifacts, never on the tone of the claim.

*Independent* needs a narrow definition here. A second model in a second prompt
shares too many of the maker's failure modes to qualify on its own; it may catch
some errors and confabulate new agreement. The checker needs a separate
execution boundary, a constrained input surface, no access to the maker's
private reasoning, and no authority to accept a claim that lacks support in an
inspected artifact. A deterministic process offers the strongest separation: it
reads only the artifacts on disk, cannot receive instructions from the maker,
and writes its decision to a durable record. Greater separation reduces the
chance that maker and checker fail together.

## Catch degenerate or repeated prose

Models often respond to an oversized word target with repetition rather than
silence. The same sentence returns with different nouns, one paragraph restates
the previous paragraph, and a section heading promises material that never
arrives. The draft remains fluent, on-topic, and empty. A length check sees the
requested word count and passes it.

A machine-scale pipeline needs a measurement because a human cannot re-read
every draft. This implementation uses a distinct-trigram ratio: split the body
into overlapping three-word sequences, then divide the number of distinct
sequences by the total. Prose that develops an argument keeps producing new
combinations. Repetitive prose reuses the same combinations, so the ratio falls.
A configured threshold turns the metric into a gate. A draft below the floor
fails as degenerate. The threshold must be calibrated for the target corpus,
language, tokenizer, and preprocessing method, then recorded with the checker
configuration. Any change to those inputs requires recalibration.

| Signal | What it measures | What it catches | What it misses |
|---|---|---|---|
| Word count | Length against a target | Drafts that are too short or too long | Padding that hits the target |
| Distinct-trigram ratio | Local repetition across the body | Loops, restatement, filler collapse | Mediocre but varied prose |
| Human editorial read | Argument, accuracy, voice, judgment | Misleading claims, weak reasoning, poor calibration | Does not scale; depends on reviewer expertise and attention |

*Table: Each signal has a job and a blind spot; none replaces the others.*

The control has a narrow scope. The trigram floor catches collapse, not
mediocrity. A draft can repeat one sentence several times inside varied prose
and still score above the floor. The metric proves only that this repetition
check passed. Lexical variety can coexist with vague, circular, or empty
reasoning. The machine owns the ratio gate; a human owns editorial quality. The
control records the computed ratio and the configured floor for review.

## Catch fabricated sources and citations

A citation can make a confabulation harder to detect. A bare claim invites
scrutiny; a claim with a source, a date, and a file path looks settled. Models
can produce these details because sourced sentences appear throughout their
training data. The citation may be invented: a plausible author, a real-sounding
paper, or a URL whose domain exists but whose path does not.

A source register treats every citation as unverified until checked and records
the verification level reached. The default posture is offline. The system
records each claim, its asserted source, and a status, but it does not contact
the network without permission. An offline run cannot claim that it verified a
URL. The register records a URL as `NEEDS_ONLINE_CHECK`, which means the check
did not run.

Network verification requires an explicit opt-in. When the operator allows it,
the register resolves each URL and records the result. The system must keep
three outcomes distinct: verified, failed, and not checked. Collapsing not
checked into pass manufactures confidence the process did not earn. The compact
record looks like this:

```yaml
claim_check:
  claim: structured orientation answered the query with far less context
  source: evidence/token-saving-public-results.md
  asserted_status: public-evidence
  verification_method: offline-register
  checks:
    existence: pass        # the file is present in the package
    accessibility: pass    # the file is readable
    support: unchecked     # does it back the claim? a human judgment
  result: NEEDS_SUPPORT_REVIEW
  checked: 2026-06-29
```

For a URL source offline, even `existence` stays `unchecked` and the result is
`NEEDS_ONLINE_CHECK`; the record never reports a level it did not reach. A
reviewer reading either status knows exactly what is left to do and is not
misled into treating the claim as confirmed.

Verification has levels. Source existence confirms that the cited source is
present. Source accessibility confirms that the system can fetch and read it.
Source support checks whether the source backs the claim. Only the third
provides semantic verification; the first two are integrity checks. Resolving a
URL or locating a file in the repository does not prove that a benchmark
supports a thirty percent claim in the sense the sentence implies. A green
existence check must not imply source support. The status field should name the
level reached, and a claim whose support remains unchecked is not verified.

The register is only as complete as the extraction step that feeds it. Someone
or something has to decide what counts as a claim and at what granularity; one
sentence can contain several factual claims. If a model performs the extraction,
the register inherits a probabilistic stage. The pipeline must declare that
stage. A workable rule separates mandatory factual claims from optional detail
and rhetorical framing, then fails closed: a factual claim without a source
blocks release.

The control produces a per-claim record of the verification method, the level
reached, and every unresolved check. It cannot replace an unresolved status with
a uniform pass.

## Catch private or unsafe leakage

An agentic system that works on real material can access local paths, internal
repository names, customer identifiers, and private notes. The model does not
know which strings may appear in public output. It may include an absolute
home-directory path in an article because the path fits the surrounding text.

Use deterministic checks for this failure. A denylist scan reads every output
file before release and searches for the exact patterns that must not appear in
public material: known private path prefixes, internal repository names, code
names, and markers for private artifacts. It reports a match count plus the file
and line for each match. Zero matches passes. Any match blocks release and
points to the line that needs correction.

Keep the scan literal and comprehensive. A scanner that tries to decide whether
a match is sensitive can rationalize its way to a miss. A literal scanner fails
on any denylisted string across every output file and has no judgment to
corrupt. The model may leak; the scanner must only report matches.

The denylist is the floor of the privacy control, not the whole of it. It
catches known forbidden strings with high reliability; it does not discover a
secret in a form it was never told to look for: a new token, a key, restructured
personal data, a reconstructable fragment with no stable pattern. A mature
pipeline keeps the literal denylist as a base layer and adds secret scanning,
patterns for personal data, and human review before a public release. The
discipline is to extend the deterministic floor, never to replace it with a
generative judgment about what "feels" sensitive. The evidence is a match count
and the exact line evidence for each scanned file, recorded with the package.

## Keep human judgment in the loop

These four controls verify structure, integrity, sources, and leakage. They do
not judge content quality. The trigram floor cannot detect a weak argument, and
the denylist cannot detect a sourced but misleading claim.

The release process reserves content-quality approval for a human. The agent
cannot satisfy this gate by trying harder or writing a more confident note. A
named person owns the gate, and the release remains blocked until that person
closes it. The ledger prevents "approved" from becoming shorthand for "the
script finished."

For that to be a control and not a wish, "human-required" has to be enforced by
the release state machine, not merely written in a checklist. The release state
cannot advance without a named human owner's approval, and that approval is one
the maker has no permission to generate. A gate that is only documented is a
policy someone can forget under deadline. A gate the pipeline cannot step over
is a control: the artifact stays in a non-releasable state until the owner moves
it, and nothing the model emits can move it for them.

The design assigns repeatable checks to machines and reserves editorial judgment
for a reviewer. The machine gates reduce the work required at the human gate.
Removing that gate moves discovery from review to publication and weakens the
release process.

## Walk one claim through the gates

A single claim shows how the gates interact. Take the agent's original sentence:
"the cited benchmark shows a thirty percent improvement, and the source is a
file in the repository."

The maker produces the draft containing that sentence and cannot approve it. The
independent checker reads the artifacts. The length and repetition metrics pass
because the surrounding prose meets the configured thresholds; this result says
only that the draft passed those checks. The source register examines the
citation. In offline mode, the asserted file path resolves against the package,
so the register records that the source exists. An absent file produces a
failure. The register has established existence, not support: the file is
present, but the process has not shown that it backs a thirty percent claim. The
denylist finds no private path or internal name. The checker emits
`MECHANICAL_PASS` for structure, integrity, consistency, and leakage, and lists
every inspected artifact. The release remains `BLOCKED_PENDING_HUMAN_REVIEW`
because source support and content quality belong to human-owned gates.

At this point, the benchmark's support remains unverified. A reviewer must
decide whether the benchmark shows a thirty percent improvement in the sense the
sentence implies. The reviewer reads it, finds that it measured latency rather
than the claimed metric, and rejects the sentence. The controls carried the
claim to the reviewer with the mechanical checks complete and the semantic
question unresolved. No gate passed a claim outside its scope.

## Common failure modes

**The model grades its own homework.** A self-review step returns a confident
"looks correct," and the team treats it as verification. Replace it with an
independent checker that reads artifacts, not reasoning.

**The checker passes on tone.** The verification step can be satisfied by more
assertive prose. Rewrite it to pass or fail on facts about the artifacts, never
on the confidence of the claim.

**Not-checked is reported as passed.** The source register collapses an
unverified URL into a pass. Keep verified, failed, and not-checked as three
distinct outcomes, and let the honest non-answer survive to the reviewer.

**The repetition metric becomes a quality claim.** A draft clears the trigram
floor and someone calls it good. Clearing the floor proves only that one
repetition check did not fail; it does not prove the text is worth reading. Keep
editorial quality on the human gate.

**The leak scanner interprets matches.** A scanner that decides whether a match
is sensitive can rationalize a miss. Keep the scan literal and comprehensive:
any denylisted string fails in every scanned file.

**The human gate is optimized away.** Under deadline, the content-quality gate
is marked done to ship. The machine gates make the human gate cheap; they do not
replace it. A release with the human gate skipped is unverified, whatever the
checker report says.

**Verification runs after the model already acted.** In an agentic system, side
effects cause the expensive failures. Run the checks before the irreversible
step so a confabulated "the tests pass" cannot trigger a deploy.

## A staged adoption path

Begin by separating the maker from the checker. The process that approves work
must differ from the process that produced it. Even a thin checker that confirms
the required artifacts exist provides more value than an elaborate self-review
because it removes the structural conflict.

Add deterministic gates after establishing that separation: the leakage scan
plus length and repetition checks. They need no network, model, or judgment, so
the pipeline can run them on every output. These checks also reduce the material
a person must inspect.

Introduce the source register in offline mode. Record each claim and its
asserted source, and preserve the not-checked status for sources the system did
not verify. Add network verification only through explicit opt-in and keep
verified, failed, and not checked as separate outcomes.

Make the human gate explicit and unskippable. Name its owner in the ledger. A
green checker report cannot substitute for editorial sign-off. This sequence
reduces the cost of each later control and reserves human attention for
judgments machines cannot make.

## Operating the system

In ordinary operation, the runtime treats each model output as a proposal that
must clear verification. Deterministic gates and the independent checker run
before release, while a human owns the content-quality gate.

The trace provides auditability by recording what the model produced and what
each control checked: the inspected artifacts, the trigram ratio, each source's
verification level, the denylist match count, and the owner of the open quality
gate. A reviewer can explain a release through those records, including the
checks that remained unresolved.

The model will keep confabulating. Better prompts can reduce the surface area,
but no prompt removes the failure mode. Trust comes from the runtime's refusal
to accept unchecked claims and from the human review reserved for semantic and
editorial judgment.

## Sources and verification snapshot

The controls in this chapter are informed by both a working publishing loop and
research on self-correction, factuality checking, and conversational
susceptibility. The following sources define the boundary of the claims made
above.

Verification date for the research sources: July 6, 2026. Re-check the papers
and their follow-up literature before treating any finding as settled.

- Jie Huang et al.,
  ["Large Language Models Cannot Self-Correct Reasoning Yet"](https://arxiv.org/abs/2310.01798).
  Supports the claim that self-correction without external feedback may fail or
  degrade reasoning performance.
- Dancheng Liu et al.,
  ["Large Language Models have Intrinsic Self-Correction Ability"](https://arxiv.org/abs/2406.15673).
  Preserves the counterpoint that self-correction can improve results under
  constrained conditions such as unbiased prompts and zero temperature.
- Potsawee Manakul, Adian Liusie, and Mark J. F. Gales,
  ["SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models"](https://arxiv.org/abs/2303.08896).
  Shows that repeated sampling can provide a probabilistic factuality signal
  without becoming deterministic source verification.
- Sungwon Kim and Daniel Khashabi,
  ["Challenging the Evaluator: LLM Sycophancy Under User Rebuttal"](https://arxiv.org/abs/2509.16533).
  Supports the warning that a follow-up challenge can influence an evaluator
  independently of factual correctness.

The deterministic controls described below come from the publishing loop used
for *Private Agent Systems*, a book and companion toolset about governed
runtimes around private agents. The implementation provides context for the
controls; it does not prove that they improve every system. Read them with these
limits:

- The maker/checker split is a design principle, not a measurement. Its value is
  structural: it removes the conflict of interest in self-review. It does not by
  itself guarantee the checker's rules are complete.
- The distinct-trigram ratio is a local repetition measurement with a configured
  and documented floor. It proves only that one repetition check did not fail.
  It does not prove editorial quality, and a varied but mediocre draft can clear
  it. The threshold must be calibrated and recorded with its preprocessing
  method.
- The source register defaults to offline. A `NEEDS_ONLINE_CHECK` status means
  the check was not performed, not that the source is valid. Network
  verification is opt-in, and even a network pass confirms that a source exists
  and is reachable, not that it supports the claim. Source support is a
  separate, semantic check.
- The denylist scan is deterministic and literal. Zero matches means no
  denylisted string was present in the scanned files. It is a base layer, not a
  guarantee that no sensitive material exists in forms the denylist does not
  name.
- The content-quality gate is always human-owned and is enforced by the release
  state, not by a checklist. No machine result in this chapter should be read as
  editorial approval.

A governed agent records verification decisions with the same care it gives tool
calls. Larger models and longer context windows can improve fluency, but they do
not decide which claims deserve trust. The runtime earns that trust by keeping
unchecked claims out of the verified state.
