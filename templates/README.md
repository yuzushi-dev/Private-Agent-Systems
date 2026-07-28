# Reusable templates

Fill-in versions of the operational artifacts from *Private Agent Systems*
(Appendix B). Copy a file into your project documentation, design reviews, or
release tickets, then replace the placeholders with project-specific evidence.

These are patterns, not production-ready libraries. Your stack, legal basis,
provider contract, region, and user group will change the final shape.

| File | Artifact | Used in |
|------|----------|---------|
| `agent-suitability-record.yaml` | Should this be an agent at all | Ch. 1: Why Private, Observable, Governed Agents |
| `policy-gate-matrix.yaml` | Policy gate definition and decisions | Ch. 2: Anatomy of an Agentic Harness |
| `open-source-harness-review-card.yaml` | Reviewing a fast-moving OSS agent project | Ch. 3: Open-Source Harnesses |
| `local-inference-readiness-card.yaml` | Local inference route readiness | Ch. 5: Local Inference, Model Notation, and Adaptation |
| `model-adaptation-decision-record.yaml` | Prompt vs RAG vs LoRA/QLoRA vs fine-tune | Ch. 5: Local Inference, Model Notation, and Adaptation |
| `context-budget-worksheet.yaml` | Token budget and packing rules | Ch. 5: Local Inference, Model Notation, and Adaptation |
| `rag-eval-case.yaml` | Retrieval/grounding eval case | Ch. 6-7: Retrieval; Observability & Evaluation |
| `eval-packet.yaml` | Release evaluation packet | Ch. 7: Observability, Evaluation, and Debugging |
| `eval-stack-card.yaml` | Eval/observability stack and gates | Ch. 7: Observability, Evaluation, and Debugging |
| `agent-eval-case.yaml` | Agent execution eval case | Ch. 7: Observability, Evaluation, and Debugging |
| `prompt-regression-case.yaml` | Prompt/route regression + red-team case | Ch. 7: Observability, Evaluation, and Debugging |
| `trace-linked-evaluation-record.yaml` | Score tied back to a run trace | Ch. 7: Observability, Evaluation, and Debugging |
| `route-card.yaml` | Per-route data/purpose/retention contract | Ch. 8: Privacy, Consent, and Data Governance |
| `data-class-table.yaml` | Data classes and their allowed routes | Ch. 8: Privacy, Consent, and Data Governance |
| `data-flow.yaml` | End-to-end data flow for a system | Ch. 8: Privacy, Consent, and Data Governance |
| `provider-review-sheet.yaml` | Provider/endpoint data-handling review | Ch. 8: Privacy, Consent, and Data Governance |
| `source-revalidation-row.yaml` | One re-checked source after publication | Ch. 8: Privacy, Consent, and Data Governance |
| `incident-report.yaml` | Incident and postmortem record | Ch. 9: Security and Mitigations |
| `topology-audit-schema.json` | Topology review packet: registers, evidence, declared checks | Supplemental: [From Loop Engineering to Graph Engineering](../chapters/from-loop-engineering-to-graph-engineering.md) |

The source register lives one level up: [`../source-register.md`](../source-register.md).

## License

These templates are public domain under **CC0 1.0**: see [`LICENSE`](LICENSE). Copy and use them freely, no attribution required.
