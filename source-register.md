# Source register

A source register records which time-sensitive claims in *Private Agent Systems*
were checked, against which primary source, on which date, and what action the
edition took. The book references this register throughout (Appendix B).

Treat every row as dated. Re-check the source before relying on the claim, and
record the new date when you do. When a source changes after publication, this
file is the stable place to record the updated link, date, and impact on the
relevant claim.

```yaml
source_register:
  edition_checked_on: "2026-06-04"
  rows:
    - claim_area: owasp_llm_top_10
      source: https://genai.owasp.org/llm-top-10/
      version: "2025"
      action: use_2025_risk_names_or_label_v1_1
    - claim_area: owasp_mcp_top_10
      source: https://owasp.org/www-project-mcp-top-10/
      status: beta_living_document
      action: cite_as_emerging_reference
    - claim_area: opentelemetry_genai_semconv
      source: https://opentelemetry.io/docs/specs/semconv/gen-ai/
      status: development
      action: treat_as_snapshot_not_stable_standard
    - claim_area: openai_agents_docs
      source: https://platform.openai.com/docs/guides/agents
      action: match_current_agentkit_wording
    - claim_area: openai_business_api_data
      source: https://openai.com/policies/api-data-usage-policies/
      action: keep_path_specific_and_dated
    - claim_area: anthropic_effective_agents
      source: https://www.anthropic.com/engineering/building-effective-agents
      published_on: "2024-12-19"
      action: keep
    - claim_area: google_vertex_ai_data_governance
      source: https://cloud.google.com/vertex-ai/generative-ai/docs/data-governance
      action: keep_path_specific_and_dated
    - claim_area: mcp_specification
      source: https://modelcontextprotocol.io/specification/2025-06-18/index
      version: "2025-06-18"
      action: keep_with_spec_version
    - claim_area: gemma_4_family
      source: https://huggingface.co/google/gemma-4-12B
      action: treat_e2b_e4b_as_model_family_labels_not_notation
    - claim_area: clinical_qlora_example
      source: https://arxiv.org/abs/2604.14175
      title: "QU-NLP at ArchEHR-QA 2026: Two-Stage QLoRA Fine-Tuning of Qwen3-4B for Patient-Oriented Clinical Question Answering and Evidence Sentence Alignment"
      action: cite_as_narrow_high_risk_domain_example_not_general_recommendation
    - claim_area: eval_observability_tools
      sources:
        - https://docs.ragas.io/
        - https://www.promptfoo.dev/docs/intro/
        - https://inspect.aisi.org.uk/
        - https://langfuse.com/docs
      action: keep_as_replaceable_examples_not_prescribed_stack
    - claim_area: amber_case_study
      source: https://github.com/yuzushi-dev/Amber
      snapshot_commit: "6e6225107420f239d51044b87572c2569b9f33e6"
      action: disclose_first_party_open_source_case_study
    - claim_area: relic_case_study
      source: https://github.com/yuzushi-dev/Relic
      snapshot_commit: "b8d56939af38a293b6692349726da73a8b60f41e"
      action: disclose_first_party_research_stage_case_study
```

## Updates after publication

When a source changes, add a dated entry below rather than editing the snapshot
above. Keep the original snapshot intact so readers can see what was true at the
edition date.

<!-- Example:
### 2026-XX-XX owasp_llm_top_10
Source moved / version changed. New link: ... . Impact on the book: ... .
-->
