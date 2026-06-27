# Token-Saving Public Results

Generated: 2026-06-26

Evidence table ID: context-budget-public-results-2026-06-26

Scope: sanitized audit snapshot; private system identifiers and internal
measurement artifacts omitted.

## Public Table

| Layer | Best use | Evidence type | Token method | Baseline | Optimized path | Saved or avoided tokens | Reduction | Scope / acceptance | Reviewer class | Public status |
|---|---|---|---|---|---|---|---|---|---|---|
| RTK shell filtering | Shell-heavy coding runs with noisy command output | Instrument-reported runtime aggregate | Tool instrumentation | n/a | n/a | 23,800,000 | 63.70% | Dated command-output filtering snapshot | n/a, runtime aggregate | Publishable |
| Claude Context Mode | Keeping large tool outputs outside active context until needed | Instrument-reported runtime aggregate | Tool instrumentation | n/a | n/a | 1,101,790 | 50.95% avg | Dated active-context masking snapshot | n/a, runtime aggregate | Publishable |
| Progressive skill loading | Loading task-specific procedures instead of a full instruction library | Static footprint estimate | chars/4 estimate | 151,339 Codex + 170,589 Claude skill tokens | Load only triggered skills | 321,928 estimated always-on tokens avoided | n/a | Always-on instruction footprint avoided | operator review | Publishable as footprint evidence |
| claude-mem | Long-term memory retrieval with selected detail fetches | Task-level same-task estimate | chars/4 estimate | 6,762 | 2,606 | 4,156 | about 61% | Memory retrieval acceptance check passed | task owner/operator | Publishable |
| codebase-memory-mcp, feature-area query | Source-code orientation before reading files | Task-level same-task estimate | bytes/4 estimate | 44,917 | 704 | 44,213 | about 98% | Orientation answer accepted, not end-to-end success | task owner/operator | Publishable |
| codebase-memory-mcp, architecture overview | Architecture overview without loading broad source context | Task-level same-task estimate | bytes/4 estimate | 159,372 | 1,050 | 158,322 | about 99% | Architecture orientation accepted, not end-to-end success | task owner/operator | Publishable |
