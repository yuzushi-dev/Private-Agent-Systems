# Operational Memory Schema

Operational memory records current work. It can link to durable concepts in
`wiki/`, but it remains separate from them.

## Project note

Location: `10-projects/<project-slug>.md`

```yaml
---
type: project
status: active
updated: YYYY-MM-DD
tags:
  - project
---
```

Use the sections Goal, Current State, Important Paths, Commands, and Open
Questions when they apply.

## Decision note

Location: `20-decisions/YYYY-MM-DD-<decision-slug>.md`

```yaml
---
type: decision
date: YYYY-MM-DD
status: accepted
tags:
  - decision
---
```

Use the sections Context, Decision, Consequences, and Rejected Alternatives.

## Runbook note

Location: `30-runbooks/<topic>.md`

```yaml
---
type: runbook
updated: YYYY-MM-DD
tags:
  - runbook
---
```

Use the sections Purpose, Preconditions, Procedure, Verification, and Rollback.

## Daily note

Location: `40-daily/YYYY-MM-DD.md`

Daily notes record events, observations, and unfinished work. Promote a claim to
`wiki/` only after linking evidence and reviewing it as durable knowledge.

## Archive

Move inactive operational records to `90-archive/`. Preserve links and status.
Do not archive wiki concepts merely because a project closed.
