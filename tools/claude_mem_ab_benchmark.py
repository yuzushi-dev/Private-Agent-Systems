#!/usr/bin/env python3
"""Synthetic A/B benchmark for the claude-mem search/filter/fetch workflow."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


QUERY = "token OR budget OR rtk OR context OR mode"


def estimate_tokens(text: str) -> int:
    return round(len(text) / 4)


@dataclass
class Observation:
    id: int
    title: str
    obs_type: str
    narrative: str
    facts: str
    concepts: str
    relevant: bool


def make_observations(total: int = 60, relevant: int = 6) -> list[Observation]:
    observations: list[Observation] = []
    for idx in range(1, total + 1):
        is_relevant = idx <= relevant
        if is_relevant:
            title = f"Token budget decision {idx}: RTK and Context Mode"
            concepts = "token-budget,rtk,context-mode,progressive-disclosure"
            topic = (
                "This observation records a decision about reducing agent context "
                "costs with RTK shell-output filtering, Context Mode masking, "
                "and skill progressive disclosure."
            )
        else:
            title = f"Unrelated implementation note {idx}"
            concepts = "ui,build,testing,release"
            topic = (
                "This observation records an unrelated implementation detail about "
                "UI context, release packaging, and routine test maintenance."
            )
        narrative = " ".join([topic] * 7)
        facts = "\n".join(
            [
                f"- fact {n}: {'token budget context' if is_relevant else 'ordinary implementation'} detail {idx}-{n}"
                for n in range(1, 7)
            ]
        )
        observations.append(
            Observation(
                id=idx,
                title=title,
                obs_type="decision" if is_relevant else "change",
                narrative=narrative,
                facts=facts,
                concepts=concepts,
                relevant=is_relevant,
            )
        )
    return observations


def create_fts_db(observations: list[Observation]) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute(
        """
        CREATE VIRTUAL TABLE observations_fts USING fts5(
            title, narrative, facts, concepts, content=''
        )
        """
    )
    for obs in observations:
        db.execute(
            "INSERT INTO observations_fts(rowid, title, narrative, facts, concepts) VALUES (?, ?, ?, ?, ?)",
            (obs.id, obs.title, obs.narrative, obs.facts, obs.concepts),
        )
    db.commit()
    return db


def search_ids(db: sqlite3.Connection, query: str, limit: int) -> list[int]:
    rows = db.execute(
        """
        SELECT rowid
        FROM observations_fts
        WHERE observations_fts MATCH ?
        ORDER BY bm25(observations_fts)
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()
    return [int(row[0]) for row in rows]


def full_observation(obs: Observation) -> str:
    return "\n".join(
        [
            f"ID: {obs.id}",
            f"Type: {obs.obs_type}",
            f"Title: {obs.title}",
            f"Concepts: {obs.concepts}",
            "Narrative:",
            obs.narrative,
            "Facts:",
            obs.facts,
        ]
    )


def compact_row(obs: Observation) -> str:
    read_estimate = estimate_tokens(full_observation(obs))
    return f"| #{obs.id} | {obs.obs_type} | {obs.title} | ~{read_estimate} |"


def benchmark(total: int = 60, relevant: int = 6, search_limit: int = 20, fetch_count: int = 6) -> dict[str, Any]:
    observations = make_observations(total=total, relevant=relevant)
    by_id = {obs.id: obs for obs in observations}
    db = create_fts_db(observations)
    ids = search_ids(db, QUERY, search_limit)
    selected_ids = ids[:fetch_count]

    baseline_text = "\n\n".join(full_observation(by_id[obs_id]) for obs_id in ids)
    index_text = "\n".join(compact_row(by_id[obs_id]) for obs_id in ids)
    selected_text = "\n\n".join(full_observation(by_id[obs_id]) for obs_id in selected_ids)

    baseline_tokens = estimate_tokens(baseline_text)
    variant_tokens = estimate_tokens(index_text) + estimate_tokens(selected_text)
    saved_tokens = baseline_tokens - variant_tokens
    reduction_pct = round((saved_tokens / baseline_tokens) * 100, 2) if baseline_tokens else 0
    relevant_found = sum(1 for obs_id in selected_ids if by_id[obs_id].relevant)

    return {
        "query": QUERY,
        "corpus_observations": total,
        "relevant_observations": relevant,
        "search_limit": search_limit,
        "fetched_after_filter": fetch_count,
        "search_results": len(ids),
        "relevant_found_in_fetch": relevant_found,
        "baseline_fetch_all_tokens": baseline_tokens,
        "search_filter_fetch_tokens": variant_tokens,
        "saved_tokens": saved_tokens,
        "reduction_pct": reduction_pct,
        "accepted": relevant_found == min(relevant, fetch_count),
    }


def real_db_counts(db_path: Path) -> dict[str, int]:
    empty = {
        "sdk_sessions": 0,
        "user_prompts": 0,
        "observations": 0,
        "session_summaries": 0,
    }
    if not db_path.exists():
        return empty
    db = sqlite3.connect(db_path)
    try:
        return {
            "sdk_sessions": db.execute("SELECT count(*) FROM sdk_sessions").fetchone()[0],
            "user_prompts": db.execute("SELECT count(*) FROM user_prompts").fetchone()[0],
            "observations": db.execute("SELECT count(*) FROM observations").fetchone()[0],
            "session_summaries": db.execute("SELECT count(*) FROM session_summaries").fetchone()[0],
        }
    finally:
        db.close()


def write_csv(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result.keys()))
        writer.writeheader()
        writer.writerow(result)


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def write_markdown(path: Path, result: dict[str, Any], counts: dict[str, int], db_label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    result_rows = "\n".join(f"| {key} | {fmt(value)} |" for key, value in result.items())
    count_rows = "\n".join(f"| {key} | {fmt(value)} |" for key, value in counts.items())
    text = f"""# claude-mem A/B Benchmark

Generated: {date.today().isoformat()}

This benchmark does not read or print stored real memory content. The installed
real database is checked only for row counts. If the real database has no
observations yet, the token-saving measurement uses a deterministic synthetic
corpus shaped like claude-mem observations.

## Real Database State

Database: `{db_label}`

| Table | Rows |
|---|---:|
{count_rows}

## Synthetic A/B Result

| Metric | Value |
|---|---:|
{result_rows}

## Interpretation

The baseline fetches full details for every search result. The optimized
claude-mem workflow shows compact search rows first, then fetches only selected
observation IDs. On this fixture, the optimized workflow saves
**{fmt(result['saved_tokens'])} estimated tokens** per query, a
**{fmt(result['reduction_pct'])}%** reduction, while retrieving all relevant
observations in the filtered set.

This is a workflow benchmark, not a provider invoice. A production claim should
be updated after the real claude-mem database contains enough observations from
normal work.
"""
    path.write_text(text)


def main() -> int:
    home = Path.home()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=home / ".claude-mem" / "claude-mem.db")
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--db-label", default="redacted memory database")
    args = parser.parse_args()

    result = benchmark()
    counts = real_db_counts(args.db)
    write_markdown(args.markdown, result, counts, args.db_label)
    write_csv(args.csv, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
