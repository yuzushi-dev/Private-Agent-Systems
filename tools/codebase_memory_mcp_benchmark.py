#!/usr/bin/env python3
"""Summarize codebase-memory-mcp indexing and token-saving measurements."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


def estimate_tokens_from_bytes(byte_count: int) -> int:
    return round(byte_count / 4)


def reduction_pct(baseline_tokens: int, measured_tokens: int) -> float:
    if baseline_tokens <= 0:
        return 0.0
    return round(((baseline_tokens - measured_tokens) / baseline_tokens) * 100, 2)


def parse_time_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(errors="ignore")
    result: dict[str, Any] = {}
    elapsed = re.search(r"elapsed_seconds=([0-9.]+)", text)
    rss = re.search(r"max_rss_kb=([0-9]+)", text)
    if elapsed:
        result["index_elapsed_seconds"] = float(elapsed.group(1))
    if rss:
        result["index_max_rss_kb"] = int(rss.group(1))
    return result


@dataclass(frozen=True)
class GraphStats:
    indexed_files: int
    indexed_source_bytes: int
    nodes: int
    edges: int
    db_bytes: int


def graph_stats(db_path: Path, project: str) -> GraphStats:
    db = sqlite3.connect(db_path)
    try:
        indexed_files, indexed_source_bytes = db.execute(
            "SELECT count(*), COALESCE(sum(size), 0) FROM file_hashes WHERE project = ?",
            (project,),
        ).fetchone()
        nodes = db.execute("SELECT count(*) FROM nodes WHERE project = ?", (project,)).fetchone()[0]
        edges = db.execute("SELECT count(*) FROM edges WHERE project = ?", (project,)).fetchone()[0]
    finally:
        db.close()
    return GraphStats(
        indexed_files=int(indexed_files),
        indexed_source_bytes=int(indexed_source_bytes),
        nodes=int(nodes),
        edges=int(edges),
        db_bytes=db_path.stat().st_size,
    )


def indexed_paths(db_path: Path, project: str) -> list[str]:
    db = sqlite3.connect(db_path)
    try:
        rows = db.execute(
            "SELECT rel_path FROM file_hashes WHERE project = ? ORDER BY rel_path",
            (project,),
        ).fetchall()
    finally:
        db.close()
    return [str(row[0]) for row in rows]


def matching_indexed_file_bytes(repo_path: Path, db_path: Path, project: str, pattern: str) -> tuple[int, int]:
    regex = re.compile(pattern)
    count = 0
    byte_count = 0
    for rel_path in indexed_paths(db_path, project):
        path = repo_path / rel_path
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        if regex.search(text):
            count += 1
            byte_count += path.stat().st_size
    return count, byte_count


def file_group_bytes(repo_path: Path, rel_paths: list[str]) -> int:
    total = 0
    for rel_path in rel_paths:
        path = repo_path / rel_path
        if path.exists():
            total += path.stat().st_size
    return total


def scenario_row(name: str, output_path: Path, baseline_bytes: int, notes: str) -> dict[str, Any]:
    output_bytes = output_path.stat().st_size if output_path.exists() else 0
    baseline_tokens = estimate_tokens_from_bytes(baseline_bytes)
    measured_tokens = estimate_tokens_from_bytes(output_bytes)
    return {
        "scenario": name,
        "baseline_bytes": baseline_bytes,
        "mcp_output_bytes": output_bytes,
        "baseline_est_tokens": baseline_tokens,
        "mcp_est_tokens": measured_tokens,
        "saved_est_tokens": baseline_tokens - measured_tokens,
        "reduction_pct": reduction_pct(baseline_tokens, measured_tokens),
        "notes": notes,
    }


def build_benchmark(
    repo_path: Path,
    db_path: Path,
    project: str,
    domain_pattern: str,
    trace_files: list[str],
    time_path: Path,
    search_graph_path: Path,
    query_graph_path: Path,
    trace_path: Path,
    architecture_path: Path,
    search_code_path: Path,
) -> dict[str, Any]:
    stats = graph_stats(db_path, project)
    domain_file_count, domain_bytes = matching_indexed_file_bytes(repo_path, db_path, project, domain_pattern)
    trace_baseline_bytes = file_group_bytes(repo_path, trace_files)
    scenarios = [
        scenario_row(
            "domain_search_graph",
            search_graph_path,
            domain_bytes,
            "Structured name search over feature-area symbols vs reading matching indexed files.",
        ),
        scenario_row(
            "domain_query_graph",
            query_graph_path,
            domain_bytes,
            "Cypher-style graph query returning names, files, lines, and complexity.",
        ),
        scenario_row(
            "trace_path",
            trace_path,
            trace_baseline_bytes,
            "Caller/callee trace for selected entry points vs reading selected trace baseline files.",
        ),
        scenario_row(
            "architecture_overview",
            architecture_path,
            stats.indexed_source_bytes,
            "Architecture summary vs reading all indexed source bytes.",
        ),
        scenario_row(
            "regex_search_code",
            search_code_path,
            domain_bytes,
            "Regex code search metadata vs reading matching indexed files.",
        ),
    ]
    return {
        "generated": date.today().isoformat(),
        "project": project,
        "repo_path": str(repo_path),
        "db_path": str(db_path),
        "stats": stats,
        "time": parse_time_file(time_path),
        "domain_file_count": domain_file_count,
        "domain_file_bytes": domain_bytes,
        "trace_baseline_bytes": trace_baseline_bytes,
        "scenarios": scenarios,
    }


def write_csv(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        fieldnames = [
            "scenario",
            "baseline_bytes",
            "mcp_output_bytes",
            "baseline_est_tokens",
            "mcp_est_tokens",
            "saved_est_tokens",
            "reduction_pct",
            "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result["scenarios"])


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def write_markdown(
    path: Path,
    result: dict[str, Any],
    repo_label: str = "redacted repository",
    db_label: str = "redacted index database",
    project_label: str = "redacted project",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stats: GraphStats = result["stats"]
    time = result["time"]
    rows = "\n".join(
        "| {scenario} | {baseline_est_tokens} | {mcp_est_tokens} | {saved_est_tokens} | {reduction_pct}% |".format(
            scenario=row["scenario"],
            baseline_est_tokens=fmt(row["baseline_est_tokens"]),
            mcp_est_tokens=fmt(row["mcp_est_tokens"]),
            saved_est_tokens=fmt(row["saved_est_tokens"]),
            reduction_pct=fmt(row["reduction_pct"]),
        )
        for row in result["scenarios"]
    )
    text = f"""# codebase-memory-mcp Benchmark

Generated: {result['generated']}

Repository: `{repo_label}`
Project: `{project_label}`
Index database: `{db_label}`

## Indexing Result

Command tested:

```bash
codebase-memory-mcp cli index_repository '{{"repo_path": "<repo-path>"}}'
```

| Metric | Value |
|---|---:|
| Indexed files | {fmt(stats.indexed_files)} |
| Indexed source bytes | {fmt(stats.indexed_source_bytes)} |
| Graph nodes | {fmt(stats.nodes)} |
| Graph edges | {fmt(stats.edges)} |
| Index DB bytes | {fmt(stats.db_bytes)} |
| Index elapsed seconds | {fmt(time.get('index_elapsed_seconds', 'n/a'))} |
| Index max RSS KB | {fmt(time.get('index_max_rss_kb', 'n/a'))} |
| Domain matching indexed files | {fmt(result['domain_file_count'])} |
| Domain matching source bytes | {fmt(result['domain_file_bytes'])} |

## Token-Saving Scenarios

Token estimates use bytes/4. Baseline means the agent would read the relevant
source files into context. MCP means the agent reads only the structured
tool response for the same investigative step.

| Scenario | Baseline est. tokens | MCP est. tokens | Saved est. tokens | Reduction |
|---|---:|---:|---:|---:|
{rows}

## Interpretation

The strongest result is not that the index is small; the index is larger than
the indexed source because it stores graph and vector structures. The saving
comes from query-time selectivity: graph metadata answers orientation questions
without loading source files. For the feature-area exploration, the baseline is
{fmt(estimate_tokens_from_bytes(result['domain_file_bytes']))}
estimated tokens if matching indexed files are read, while the structured graph
query uses {fmt(result['scenarios'][1]['mcp_est_tokens'])} estimated tokens.

These are local workflow measurements, not provider invoices. They are suitable
for article claims if reported as "estimated prompt tokens avoided" and paired
with the exact command and repo surface above.
"""
    path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--domain-pattern",
        required=True,
        help="Regex used to identify the feature-area files for the baseline.",
    )
    parser.add_argument(
        "--trace-file",
        action="append",
        default=[],
        help="Relative source file included in the trace-path baseline. Repeat as needed.",
    )
    parser.add_argument("--time", type=Path, default=Path("/tmp/codebase-memory-index.time"))
    parser.add_argument("--search-graph", type=Path, default=Path("/tmp/cbm-search-domain.json"))
    parser.add_argument("--query-graph", type=Path, default=Path("/tmp/cbm-query-domain.json"))
    parser.add_argument("--trace", type=Path, default=Path("/tmp/cbm-trace-path.json"))
    parser.add_argument("--architecture", type=Path, default=Path("/tmp/cbm-architecture.json"))
    parser.add_argument("--search-code", type=Path, default=Path("/tmp/cbm-search-code-regex.json"))
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--repo-label", default="redacted repository")
    parser.add_argument("--db-label", default="redacted index database")
    parser.add_argument("--project-label", default="redacted project")
    args = parser.parse_args()

    result = build_benchmark(
        repo_path=args.repo,
        db_path=args.db,
        project=args.project,
        domain_pattern=args.domain_pattern,
        trace_files=args.trace_file,
        time_path=args.time,
        search_graph_path=args.search_graph,
        query_graph_path=args.query_graph,
        trace_path=args.trace,
        architecture_path=args.architecture,
        search_code_path=args.search_code,
    )
    write_markdown(
        args.markdown,
        result,
        repo_label=args.repo_label,
        db_label=args.db_label,
        project_label=args.project_label,
    )
    write_csv(args.csv, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
