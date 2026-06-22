# Private Agent Systems: resources

Supplemental material for *Private Agent Systems* by Daniele Verì: a manual for
designing private, observable, and governed AI agent systems.

[Book](#book) • [Companion repositories](#companion-repositories) • [New chapter](#new-chapter) • [Contents](#contents) • [Repository structure](#repository-structure) • [Errata](#errata) • [Source updates](#source-updates) • [Contributing](#contributing) • [License](#license)

---

## Book

<div align="center">
  <img src="assets/cover.jpg" alt="Private Agent Systems cover" width="320">
</div>

**Private Agent Systems**
*Architecture, privacy, observability, and governance for local, hybrid, and cloud AI agents*
Daniele Verì

The book treats agents as production software systems, not prompt experiments. It
focuses on the harness around the model: identity, data classification, retrieval,
model routing, tool permissions, memory, observability, evaluation, privacy
controls, and operational ownership, and on turning privacy, consent, security,
tool governance, and rollout into runtime decisions that can be inspected and
reviewed. Two first-party case studies, **Amber** (governable Hybrid GraphRAG) and
**Relic** (runtime governance, provenance, consent, and memory control), ground
the architecture in concrete systems.

- **English edition (canonical):** *Private Agent Systems*: first edition
- **Italian edition:** *Sistemi agentici privati*
- **Where to buy:** <!-- TODO: add the Amazon/KDP purchase link and edition/ASIN -->

*Daniele Verì builds private, observable AI systems, where cognitive science meets
engineering. He is the author of Amber (governable Hybrid GraphRAG) and Relic
(runtime governance for agent memory and consent): the two case studies in this
book.*

---

## Companion repositories

The two first-party case studies from the book are open source:

- **Amber** (governable Hybrid GraphRAG): https://github.com/yuzushi-dev/Amber
- **Relic** (runtime governance, provenance, consent, memory control): https://github.com/yuzushi-dev/Relic

---

## New chapter

**[Building a Governed LLM Wiki as a Second Brain](chapters/building-a-governed-llm-wiki.md)**
is a practical guide to maintaining a local, source-linked knowledge base with
Claude Code and Codex. It covers the knowledge lifecycle, operational memory,
filesystem MCP wiring, provenance, corrections, concurrent writes, security,
and end-to-end acceptance tests.

The accompanying [`second-brain-starter/`](second-brain-starter/) directory is
a portable vault skeleton with matching `CLAUDE.md` and `AGENTS.md` entry files.

---

## Contents

This repository is the stable place for material that may change after publication:

- [`templates/`](templates/): fill-in versions of the reusable artifacts from Appendix B (route cards, eval cases, data flow, policy gates, and more)
- [`chapters/`](chapters/): supplemental chapters published after the first edition
- [`second-brain-starter/`](second-brain-starter/): runnable companion files for the governed LLM Wiki chapter
- [`source-register.md`](source-register.md): the dated source register from Appendix B, kept current here as sources change
- Companion links for Amber and Relic (above)
- Errata and clarifications (added as they are reported)

The print book, ebook, and Kindle edition may refer readers here when a resource is easier to maintain outside the manuscript.

---

## Repository structure

```
.
├── README.md              This file.
├── LICENSE                Licensing terms (CC0 for templates/register; book text reserved).
├── CITATION.cff           How to cite the book.
├── source-register.md     Dated source register (Appendix B), updated as sources change.
├── assets/
│   └── cover.jpg          Book cover.
├── chapters/
│   └── building-a-governed-llm-wiki.md
├── second-brain-starter/  Portable Claude Code and Codex vault skeleton.
└── templates/             Fill-in operational artifacts from Appendix B (CC0).
    ├── README.md          Index of all templates, mapped to their book chapters.
    ├── LICENSE            CC0 1.0 dedication for the templates + source register.
    ├── route-card.yaml
    ├── data-class-table.yaml
    ├── data-flow.yaml
    ├── provider-review-sheet.yaml
    ├── source-revalidation-row.yaml
    ├── policy-gate-matrix.yaml
    ├── agent-suitability-record.yaml
    ├── open-source-harness-review-card.yaml
    ├── local-inference-readiness-card.yaml
    ├── model-adaptation-decision-record.yaml
    ├── context-budget-worksheet.yaml
    ├── eval-packet.yaml
    ├── eval-stack-card.yaml
    ├── agent-eval-case.yaml
    ├── rag-eval-case.yaml
    ├── prompt-regression-case.yaml
    ├── trace-linked-evaluation-record.yaml
    └── incident-report.yaml
```

See [`templates/README.md`](templates/README.md) for what each template is and which chapter it comes from.

---

## Errata

If you find a technical error, outdated reference, broken link, or unclear passage, open an issue in this repository. Include the edition, format, chapter, section, and enough context to reproduce the problem.

For privacy, security, legal, or procurement decisions, treat the book as technical education. Re-check current vendor documentation, laws, contracts, and organizational policy before using any pattern in production.

---

## Source updates

The book relies on time-sensitive material: model cards, provider documentation, standards, security guidance, open-source repositories, and product terms. When a source changes after publication, record the updated link, date, and impact on the relevant claim in [`source-register.md`](source-register.md).

---

## Contributing

Contributions are limited to keeping the supplemental material correct and current:

- **Errata**: open an issue (see above). Pull requests that fix a typo, broken link, or outdated reference in this repository are welcome.
- **Source updates**: if a cited source moved or changed, propose an update to [`source-register.md`](source-register.md) with the new link and the date you checked it.
- **Templates**: the templates are intentionally minimal patterns. Suggestions that keep them general and chapter-faithful are welcome; project-specific variants belong in your own repository.

Please do not open pull requests that reproduce or redistribute the book text.

---

## License

The fill-in templates in [`templates/`](templates/), the portable files in
[`second-brain-starter/`](second-brain-starter/), and
[`source-register.md`](source-register.md) are dedicated to the public domain
under **CC0 1.0** (see [`templates/LICENSE`](templates/LICENSE)). Copy, modify,
and use them freely, including commercially, with no attribution required.

Everything else, including the prose of the book *Private Agent Systems*, the
supplemental chapter prose, the cover image, and the explanatory text in these
README files, is the author's reserved work, provided for reading and reference
only.
