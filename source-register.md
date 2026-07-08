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
      source: https://developers.openai.com/api/docs/guides/agents
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

### 2026-06-22 governed LLM Wiki chapter

The following sources support the supplemental chapter
[`Building a Governed LLM Wiki as a Second Brain`](chapters/building-a-governed-llm-wiki.md).

```yaml
supplemental_chapter_register:
  chapter: building_a_governed_llm_wiki
  checked_on: "2026-06-22"
  rows:
    - claim_area: llm_wiki_pattern
      source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
      action: treat_as_an_architectural_pattern_not_an_evaluated_product
    - claim_area: claude_code_memory_and_mcp
      sources:
        - https://code.claude.com/docs/en/memory
        - https://code.claude.com/docs/en/mcp
        - https://code.claude.com/docs/en/permissions
      action: keep_instruction_discovery_and_mcp_scope_commands_dated
    - claim_area: codex_agents_md_and_mcp
      sources:
        - https://developers.openai.com/codex/guides/agents-md
        - https://developers.openai.com/codex/mcp
        - https://developers.openai.com/codex/memories
      action: keep_instruction_discovery_limits_and_mcp_commands_dated
    - claim_area: mcp_filesystem_boundary
      package: "@modelcontextprotocol/server-filesystem"
      package_version: "2026.1.14"
      source_snapshot_commit: "3e805376da81c063c2798410906b5fd134334a43"
      sources:
        - https://modelcontextprotocol.io/docs/concepts/roots
        - https://github.com/modelcontextprotocol/servers/tree/3e805376da81c063c2798410906b5fd134334a43/src/filesystem
      action: record_roots_replacement_tool_surface_and_os_boundary
    - claim_area: provenance_and_git_transaction
      sources:
        - https://www.w3.org/TR/prov-dm/
        - https://git-scm.com/docs/git-status
        - https://git-scm.com/docs/git-diff
        - https://git-scm.com/docs/git-restore
        - https://git-scm.com/docs/git-worktree
      action: require_immutable_original_hash_claim_locator_and_atomic_commit
    - claim_area: obsidian_markdown_interface
      sources:
        - https://help.obsidian.md/links
        - https://help.obsidian.md/properties
        - https://help.obsidian.md/plugins/graph
      action: treat_obsidian_as_optional_interface_over_canonical_markdown
    - claim_area: long_context_and_memory_tiers
      sources:
        - https://arxiv.org/abs/2307.03172
        - https://arxiv.org/abs/2310.08560
      action: support_bounded_context_and_memory_tiers_without_claiming_llm_wiki_superiority
```

### 2026-06-26 governed context budget chapter

The following rows support the supplemental chapter
[`Governing Context Budgets in Private Agent Systems`](chapters/governing-context-budgets.md).
The audit rows are sanitized task measurements, not provider invoices.

```yaml
supplemental_chapter_register:
  chapter: governing_context_budgets
  checked_on: "2026-06-26"
  evidence_table_id: context-budget-public-results-2026-06-26
  evidence_table_path: evidence/token-saving-public-results.md
  evidence_table_sha256: c182cf69adf1f223f3b2443fc8bf26f54efcd969ac894b3b770236dc5c6242b4
  rows:
    - claim_area: context_budget_public_results
      source: evidence/token-saving-public-results.md
      action: use_sanitized_public_table_only
    - claim_area: shell_output_filtering
      source: evidence/token-saving-public-results.md
      action: report_as_instrument_reported_runtime_snapshot
    - claim_area: context_masking
      source: evidence/token-saving-public-results.md
      action: report_as_instrument_reported_runtime_snapshot
    - claim_area: progressive_skill_loading
      source: evidence/token-saving-public-results.md
      action: report_as_static_footprint_avoided_not_provider_invoice
    - claim_area: memory_retrieval_savings
      source: evidence/token-saving-public-results.md
      action: label_as_task_level_memory_retrieval_measurement
    - claim_area: source_orientation_savings
      source: evidence/token-saving-public-results.md
      action: label_as_query_time_orientation_saving_not_end_to_end_task_success
```

### 2026-06-28 agentic loops chapter

The following rows support the supplemental chapter
[`Agentic Loops in Private Agent Systems`](chapters/agentic-loops.md).

```yaml
supplemental_chapter_register:
  chapter: agentic_loops
  checked_on: "2026-06-28"
  rows:
    - claim_area: boris_cherny_role
      source: https://www.anthropic.com/webinars/claude-code-for-financial-services-boris-cherny
      status: primary_organizational_source
      action: support_role_attribution
    - claim_area: boris_cherny_loop_quote_and_practitioner_framing
      sources:
        - https://addyosmani.com/blog/loop-engineering/
        - https://lucumr.pocoo.org/2026/6/23/the-coming-loop/
      status: contemporary_secondary_sources
      action: attribute_quote_through_practitioner_essays_primary_recording_not_in_snapshot
    - claim_area: workflow_and_agent_distinction
      source: https://www.anthropic.com/engineering/building-effective-agents
      status: primary_practitioner_guidance
      action: support_distinction_between_workflows_agents_checks_guardrails_and_tradeoffs
    - claim_area: llm_application_security_risks
      source: https://genai.owasp.org/llm-top-10/
      status: risk_framework
      action: anchor_prompt_injection_disclosure_supply_chain_and_excessive_agency_risks
    - claim_area: generative_ai_risk_management
      sources:
        - https://www.nist.gov/itl/ai-risk-management-framework
        - https://doi.org/10.6028/NIST.AI.600-1
      status: risk_framework
      action: anchor_risk_tolerance_lifecycle_legal_context_and_control_selection
    - claim_area: agentic_ai_failure_modes
      sources:
        - https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/bade/documents/products-and-services/en-us/security/Taxonomy-of-Failure-Modes-in-Agentic-AI-Systems-v2-0.pdf
        - https://www.microsoft.com/en-us/security/blog/2026/06/04/updating-taxonomy-failure-modes-agentic-ai-systems-year-red-teaming-taught-us/
      status: threat_modeling_reference
      action: anchor_goal_hijacking_inter_agent_trust_session_context_mcp_plugin_abuse_and_hitl_bypass
    - claim_area: loop_engineering_reference_implementation_and_vocabulary
      source: https://github.com/cobusgreyling/loop-engineering
      status: reference_implementation
      action: treat_patterns_readiness_levels_state_budget_and_maker_checker_as_reference_vocabulary
```
