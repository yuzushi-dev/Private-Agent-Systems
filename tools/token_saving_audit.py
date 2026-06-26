#!/usr/bin/env python3
"""Generate a local token-saving audit for Claude/Codex workflows.

The report intentionally excludes one local token-saving tool. It uses only:
- RTK aggregate output, when `rtk gain` is available.
- Claude Context Mode stats JSON files.
- Static instruction/skill/plugin footprint from local files.

Token estimates for static files use a conservative chars/4 heuristic unless a
provider-native tokenizer is added later. The report labels these as estimates.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


def estimate_tokens(text: str) -> int:
    return round(len(text) / 4)


def parse_human_number(value: str) -> int:
    cleaned = value.strip().replace(",", "")
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMB])?", cleaned, re.I)
    if not match:
        raise ValueError(f"Cannot parse number: {value!r}")
    number = float(match.group(1))
    suffix = (match.group(2) or "").upper()
    multiplier = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suffix]
    return int(round(number * multiplier))


def parse_rtk_gain(output: str) -> dict[str, Any]:
    fields = {
        "commands": r"Total commands:\s+([0-9.,KMB]+)",
        "input_tokens": r"Input tokens:\s+([0-9.,KMB]+)",
        "output_tokens": r"Output tokens:\s+([0-9.,KMB]+)",
        "tokens_saved": r"Tokens saved:\s+([0-9.,KMB]+)\s+\(([0-9.]+)%\)",
    }
    result: dict[str, Any] = {"available": True}
    for key, pattern in fields.items():
        match = re.search(pattern, output)
        if not match:
            continue
        result[key] = parse_human_number(match.group(1))
        if key == "tokens_saved":
            result["reduction_pct"] = float(match.group(2))
    return result


def run_rtk_gain() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["rtk", "gain"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": str(exc)}
    if completed.returncode != 0:
        return {"available": False, "error": completed.stderr.strip() or completed.stdout.strip()}
    return parse_rtk_gain(completed.stdout)


def _numeric(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key, 0)
    return value if isinstance(value, (int, float)) else 0


def aggregate_context_mode_stats(stats_dir: Path) -> dict[str, Any]:
    files = sorted(stats_dir.glob("stats-pid-*.json"))
    rows: list[dict[str, Any]] = []
    for path in files:
        try:
            rows.append(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            continue

    totals: dict[str, Any] = {
        "available": bool(rows),
        "files": len(rows),
        "total_calls": 0,
        "bytes_returned": 0,
        "bytes_indexed": 0,
        "bytes_sandboxed": 0,
        "cache_hits": 0,
        "cache_bytes_saved": 0,
        "kept_out": 0,
        "total_processed": 0,
        "tokens_saved": 0,
        "dollars_saved_session": 0.0,
    }
    reductions: list[float] = []
    for row in rows:
        for key in totals:
            if key in {"available", "files"}:
                continue
            totals[key] += _numeric(row, key)
        reduction = row.get("reduction_pct")
        if isinstance(reduction, (int, float)):
            reductions.append(float(reduction))
    totals["avg_reduction_pct"] = round(sum(reductions) / len(reductions), 2) if reductions else None
    return totals


def _file_estimate(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    text = path.read_text(errors="ignore")
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "est_tokens": estimate_tokens(text),
    }


def static_context_footprint(codex_dir: Path, claude_dir: Path, vault_dir: Path) -> dict[str, Any]:
    always_on_paths = [
        codex_dir / "AGENTS.md",
        claude_dir / "CLAUDE.md",
        codex_dir / "RTK.md",
        claude_dir / "RTK.md",
        vault_dir / "AGENTS.md",
        vault_dir / "CLAUDE.md",
        vault_dir / "00-system" / "llm-wiki-spec.md",
    ]
    always_on = [entry for path in always_on_paths if (entry := _file_estimate(path))]

    codex_skill_files = sorted((codex_dir / "skills").glob("*/SKILL.md"))
    claude_skill_files = sorted((claude_dir / "skills").glob("*/SKILL.md"))

    def skill_totals(files: list[Path]) -> tuple[int, int, int]:
        byte_total = sum(path.stat().st_size for path in files)
        token_total = sum(estimate_tokens(path.read_text(errors="ignore")) for path in files)
        return len(files), byte_total, token_total

    codex_count, codex_bytes, codex_tokens = skill_totals(codex_skill_files)
    claude_count, claude_bytes, claude_tokens = skill_totals(claude_skill_files)

    return {
        "always_on_files": always_on,
        "always_on_est_tokens": sum(item["est_tokens"] for item in always_on),
        "codex_skill_count": codex_count,
        "codex_skills_bytes": codex_bytes,
        "codex_skills_est_tokens": codex_tokens,
        "claude_skill_count": claude_count,
        "claude_skills_bytes": claude_bytes,
        "claude_skills_est_tokens": claude_tokens,
    }


def plugin_inventory(claude_dir: Path) -> dict[str, Any]:
    path = claude_dir / "plugins" / "installed_plugins.json"
    if not path.exists():
        return {"available": False, "plugins": []}
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return {"available": False, "error": str(exc), "plugins": []}
    plugins = []
    for name, installs in (payload.get("plugins") or {}).items():
        first = installs[0] if installs else {}
        plugins.append(
            {
                "name": name,
                "install_count": len(installs),
                "version": first.get("version", ""),
                "scope": first.get("scope", ""),
            }
        )
    return {"available": True, "plugins": sorted(plugins, key=lambda item: item["name"])}


def aggregate_claude_project_memory(claude_dir: Path) -> dict[str, Any]:
    memory_files = sorted((claude_dir / "projects").glob("*/memory/MEMORY.md"))
    entries: list[dict[str, Any]] = []
    for path in memory_files:
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        entries.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "est_tokens": estimate_tokens(text),
            }
        )
    return {
        "available": bool(entries),
        "memory_file_count": len(entries),
        "memory_bytes": sum(item["bytes"] for item in entries),
        "memory_est_tokens": sum(item["est_tokens"] for item in entries),
        "memory_files": entries,
    }


def aggregate_claude_mem(home: Path, claude_dir: Path) -> dict[str, Any]:
    """Detect thedotmack/claude-mem without printing stored memory content."""
    root = home / ".claude-mem"
    settings = root / "settings.json"
    plugin_payload = plugin_inventory(claude_dir)
    installed_plugins = [
        item
        for item in plugin_payload.get("plugins", [])
        if "claude-mem" in item.get("name", "").lower()
        or "claudemem" in item.get("name", "").lower()
        or "thedotmack" in item.get("name", "").lower()
    ]

    files: list[dict[str, Any]] = []
    if root.exists():
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            try:
                size = path.stat().st_size
            except OSError:
                continue
            files.append({"path": str(path), "bytes": size})

    return {
        "available": root.exists() or bool(installed_plugins),
        "root": str(root),
        "root_present": root.exists(),
        "settings_present": settings.exists(),
        "plugin_present": bool(installed_plugins),
        "installed_plugins": installed_plugins,
        "data_file_count": len(files),
        "data_bytes": sum(item["bytes"] for item in files),
        "data_files": files,
    }


@dataclass
class Audit:
    rtk: dict[str, Any]
    context_mode: dict[str, Any]
    claude_mem: dict[str, Any]
    claude_project_memory: dict[str, Any]
    static: dict[str, Any]
    plugins: dict[str, Any]


def build_audit(home: Path, codex_dir: Path, claude_dir: Path, vault_dir: Path, skip_rtk: bool) -> Audit:
    rtk = {"available": False, "skipped": True} if skip_rtk else run_rtk_gain()
    context_mode = aggregate_context_mode_stats(claude_dir / "context-mode" / "sessions")
    claude_mem = aggregate_claude_mem(home, claude_dir)
    claude_project_memory = aggregate_claude_project_memory(claude_dir)
    static = static_context_footprint(codex_dir, claude_dir, vault_dir)
    plugins = plugin_inventory(claude_dir)
    return Audit(
        rtk=rtk,
        context_mode=context_mode,
        claude_mem=claude_mem,
        claude_project_memory=claude_project_memory,
        static=static,
        plugins=plugins,
    )


def audit_rows(audit: Audit) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if audit.rtk.get("available"):
        rows.extend(
            [
                {
                    "evidence_class": "instrument_reported",
                    "source": "rtk gain",
                    "metric": "tokens_saved",
                    "value": audit.rtk.get("tokens_saved"),
                    "unit": "tokens",
                    "notes": "Reported by RTK; shell-output filtering only.",
                },
                {
                    "evidence_class": "instrument_reported",
                    "source": "rtk gain",
                    "metric": "reduction_pct",
                    "value": audit.rtk.get("reduction_pct"),
                    "unit": "percent",
                    "notes": "Reported by RTK.",
                },
            ]
        )
    if audit.context_mode.get("available"):
        rows.extend(
            [
                {
                    "evidence_class": "instrument_reported",
                    "source": "Claude Context Mode stats",
                    "metric": "tokens_saved",
                    "value": audit.context_mode.get("tokens_saved"),
                    "unit": "tokens",
                    "notes": "Aggregated from stats-pid JSON files.",
                },
                {
                    "evidence_class": "instrument_reported",
                    "source": "Claude Context Mode stats",
                    "metric": "avg_reduction_pct",
                    "value": audit.context_mode.get("avg_reduction_pct"),
                    "unit": "percent",
                    "notes": "Mean of per-session reported reduction_pct.",
                },
                {
                    "evidence_class": "instrument_reported",
                    "source": "Claude Context Mode stats",
                    "metric": "kept_out",
                    "value": audit.context_mode.get("kept_out"),
                    "unit": "bytes",
                    "notes": "Bytes kept out of active context.",
                },
            ]
        )
    rows.extend(
        [
            {
                "evidence_class": "static_footprint",
                "source": "Claude project memory",
                "metric": "claude_project_memory_est_tokens",
                "value": audit.claude_project_memory.get("memory_est_tokens"),
                "unit": "estimated_tokens_chars_div_4",
                "notes": "Approximate footprint of ~/.claude/projects/*/memory/MEMORY.md; content omitted.",
            },
            {
                "evidence_class": "static_footprint",
                "source": "Local instruction files",
                "metric": "always_on_est_tokens",
                "value": audit.static.get("always_on_est_tokens"),
                "unit": "estimated_tokens_chars_div_4",
                "notes": "Approximate static footprint of bridge instructions and vault spec.",
            },
            {
                "evidence_class": "static_footprint",
                "source": "Codex SKILL.md files",
                "metric": "codex_skills_est_tokens",
                "value": audit.static.get("codex_skills_est_tokens"),
                "unit": "estimated_tokens_chars_div_4",
                "notes": "Approximate full Codex skill library body, not always loaded.",
            },
            {
                "evidence_class": "static_footprint",
                "source": "Claude SKILL.md files",
                "metric": "claude_skills_est_tokens",
                "value": audit.static.get("claude_skills_est_tokens"),
                "unit": "estimated_tokens_chars_div_4",
                "notes": "Approximate full Claude skill library body, not always loaded.",
            },
        ]
    )
    rows.extend(
        [
            {
                "evidence_class": "inventory",
                "source": "thedotmack/claude-mem",
                "metric": "root_present",
                "value": int(bool(audit.claude_mem.get("root_present"))),
                "unit": "boolean",
                "notes": "Detects ~/.claude-mem; not a token saving claim.",
            },
            {
                "evidence_class": "inventory",
                "source": "thedotmack/claude-mem",
                "metric": "data_bytes",
                "value": audit.claude_mem.get("data_bytes"),
                "unit": "bytes",
                "notes": "Total local claude-mem file bytes; content omitted.",
            },
        ]
    )
    if audit.plugins.get("available"):
        rows.append(
            {
                "evidence_class": "inventory",
                "source": "Claude installed_plugins.json",
                "metric": "installed_plugin_keys",
                "value": len(audit.plugins.get("plugins", [])),
                "unit": "count",
                "notes": "Inventory only; not a token saving claim.",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["evidence_class", "source", "metric", "value", "unit", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def write_markdown(path: Path, audit: Audit, rows: list[dict[str, Any]], include_local_details: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plugins = audit.plugins.get("plugins", [])
    if include_local_details:
        plugin_lines = "\n".join(
            f"- `{item['name']}` ({item.get('version') or 'unknown'}, {item.get('scope') or 'unknown'})"
            for item in plugins
        ) or "- n/a"
        always_on_lines = "\n".join(
            f"- `{item['path']}`: {fmt(item['est_tokens'])} estimated tokens"
            for item in audit.static.get("always_on_files", [])
        )
        claude_project_memory_lines = "\n".join(
            f"- `{item['path']}`: {fmt(item['est_tokens'])} estimated tokens"
            for item in audit.claude_project_memory.get("memory_files", [])
        ) or "- n/a"
        claude_mem_lines = "\n".join(
            f"- `{item['path']}`: {fmt(item['bytes'])} bytes"
            for item in audit.claude_mem.get("data_files", [])
        ) or "- n/a"
    else:
        plugin_lines = f"- Redacted by default. Plugin keys detected: {fmt(len(plugins))}."
        always_on_lines = "- Redacted by default. Use `--include-local-details` for a private local report."
        claude_project_memory_lines = "- Redacted by default. Use `--include-local-details` for a private local report."
        claude_mem_lines = "- Redacted by default. Use `--include-local-details` for a private local report."
    row_lines = "\n".join(
        f"| {row['evidence_class']} | {row['source']} | {row['metric']} | {fmt(row['value'])} | {row['unit']} |"
        for row in rows
    )
    text = f"""# Token-Saving Audit

Generated: {date.today().isoformat()}

This audit excludes one local token-saving tool. It separates runtime-reported savings from
static context footprint. The static token counts use a chars/4 estimate and
should not be treated as provider billing records.

## Summary

| Evidence class | Source | Metric | Value | Unit |
|---|---|---:|---:|---|
{row_lines}

## Runtime Filtering

### RTK

- Available: {audit.rtk.get('available')}
- Commands observed: {fmt(audit.rtk.get('commands'))}
- Input tokens: {fmt(audit.rtk.get('input_tokens'))}
- Output tokens: {fmt(audit.rtk.get('output_tokens'))}
- Tokens saved: {fmt(audit.rtk.get('tokens_saved'))}
- Reduction: {fmt(audit.rtk.get('reduction_pct'))}%

### Claude Context Mode

- Stats files: {fmt(audit.context_mode.get('files'))}
- Tool calls processed: {fmt(audit.context_mode.get('total_calls'))}
- Bytes processed: {fmt(audit.context_mode.get('total_processed'))}
- Bytes returned: {fmt(audit.context_mode.get('bytes_returned'))}
- Bytes kept out: {fmt(audit.context_mode.get('kept_out'))}
- Tokens saved: {fmt(audit.context_mode.get('tokens_saved'))}
- Average reduction: {fmt(audit.context_mode.get('avg_reduction_pct'))}%
- Cache hits: {fmt(audit.context_mode.get('cache_hits'))}

## Static Context Footprint

### Claude Project Memory

Claude project memory files under `~/.claude/projects/*/memory/MEMORY.md`.

{claude_project_memory_lines}

- Files: {fmt(audit.claude_project_memory.get('memory_file_count'))}
- Total estimate: {fmt(audit.claude_project_memory.get('memory_est_tokens'))} tokens

### claude-mem External Memory

`claude-mem` here means thedotmack/claude-mem. The audit detects local
installation/configuration and file footprint only; it does not print memory
contents.

- Root present: {audit.claude_mem.get('root_present')}
- Settings present: {audit.claude_mem.get('settings_present')}
- Plugin present: {audit.claude_mem.get('plugin_present')}
- Data files: {fmt(audit.claude_mem.get('data_file_count'))}
- Data bytes: {fmt(audit.claude_mem.get('data_bytes'))}

{claude_mem_lines}

### Always-On Files

{always_on_lines}

Total always-on estimate: **{fmt(audit.static.get('always_on_est_tokens'))} tokens**

### Skill Libraries

- Codex skills: {fmt(audit.static.get('codex_skill_count'))} files,
  {fmt(audit.static.get('codex_skills_est_tokens'))} estimated tokens.
- Claude skills: {fmt(audit.static.get('claude_skill_count'))} files,
  {fmt(audit.static.get('claude_skills_est_tokens'))} estimated tokens.

Interpretation: these skill bodies are the instruction mass that progressive
disclosure keeps out of the baseline context until a task triggers them.

## Plugin Inventory

{plugin_lines}

Plugin inventory is not a saving claim. It identifies capability surface that
can add tool schemas, instructions, permissions, and supply-chain risk.

## Article-Ready Claim

In this local stack, RTK reports {fmt(audit.rtk.get('tokens_saved'))} shell-output
tokens saved with a {fmt(audit.rtk.get('reduction_pct'))}% reduction. Claude
Context Mode reports {fmt(audit.context_mode.get('tokens_saved'))} tokens saved
across {fmt(audit.context_mode.get('files'))} session stat files, with an average
reported reduction of {fmt(audit.context_mode.get('avg_reduction_pct'))}%.
Separately, progressive disclosure keeps roughly
{fmt(audit.static.get('codex_skills_est_tokens'))} Codex skill tokens and
{fmt(audit.static.get('claude_skills_est_tokens'))} Claude skill tokens out of
the always-on instruction layer. Claude project memory contributes another
{fmt(audit.claude_project_memory.get('memory_est_tokens'))} estimated tokens across
{fmt(audit.claude_project_memory.get('memory_file_count'))} local memory files; whether
those tokens are loaded depends on the active project and Claude Code's memory
loading behavior. The external claude-mem footprint is reported as inventory
only until paired A/B runs show task-level saving.

## Caveats

- RTK and Context Mode numbers are instrument-reported operational savings, not
  provider invoices.
- Static skill counts are estimated from local file text, not tokenizer-specific
  billing counters.
- A/B task verification is still required before claiming cost per accepted task.
- One local token-saving tool is intentionally excluded from this audit.
"""
    path.write_text(text)


def main() -> int:
    home = Path.home()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=home)
    parser.add_argument("--codex-dir", type=Path, default=home / ".codex")
    parser.add_argument("--claude-dir", type=Path, default=home / ".claude")
    parser.add_argument("--vault-dir", type=Path, default=home / "Obsidian" / "AgentMemory")
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--skip-rtk", action="store_true")
    parser.add_argument(
        "--include-local-details",
        action="store_true",
        help="Include local file paths and plugin names in the markdown report. Use only for private reports.",
    )
    args = parser.parse_args()

    audit = build_audit(args.home, args.codex_dir, args.claude_dir, args.vault_dir, args.skip_rtk)
    rows = audit_rows(audit)
    write_markdown(args.markdown, audit, rows, include_local_details=args.include_local_details)
    write_csv(args.csv, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
