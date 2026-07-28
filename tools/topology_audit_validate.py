#!/usr/bin/env python3
"""Validate the minimum Topology Review Protocol packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


REQUIRED_TOP = {"protocol_version", "manifest", "registers", "evidence", "checks"}
REQUIRED_REGISTER = {
    "register_row_id",
    "surface",
    "target_id",
    "applicability",
    "owner",
    "evidence_ids",
}
REQUIRED_EVIDENCE = {
    "evidence_id",
    "locator",
    "origin",
    "collector",
    "integrity_control",
    "trust_class",
    "limitations",
}
REQUIRED_CHECK = {
    "check_id",
    "requirement_id",
    "surface",
    "requirement",
    "target_id",
    "register_row_ids",
    "evidence_ids",
    "status",
    "rationale",
    "owner",
}
SURFACES = {"knowledge", "execution", "lineage"}
STATUSES = {"SUPPORTED", "PARTIAL", "UNSUPPORTED", "INCONCLUSIVE", "NOT_APPLICABLE"}
TRUST_CLASSES = {"T1", "T2", "T3"}


def finding(rule_id: str, locator: str, message: str) -> dict[str, str]:
    return {"rule_id": rule_id, "locator": locator, "message": message}


def missing_fields(item: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(required - item.keys())


def validate(packet: Any, schema: dict[str, Any]) -> list[dict[str, str]]:
    Draft202012Validator.check_schema(schema)
    findings: list[dict[str, str]] = []
    for error in sorted(
        Draft202012Validator(schema).iter_errors(packet),
        key=lambda item: list(item.absolute_path),
    ):
        rule_id = (
            "TRP-001"
            if error.validator in {"required", "minItems", "minLength", "minProperties"}
            else "TRP-004"
        )
        locator = "$" + "".join(f"[{part!r}]" for part in error.absolute_path)
        findings.append(finding(rule_id, locator, error.message))

    if findings:
        return findings

    if not isinstance(packet, dict):
        findings.append(finding("TRP-001", "$", "packet must be an object"))
        return findings

    missing = missing_fields(packet, REQUIRED_TOP)
    if missing:
        findings.append(finding("TRP-001", "$", f"missing fields: {', '.join(missing)}"))
        return findings
    manifest = packet.get("manifest")
    if not isinstance(manifest, dict):
        return findings

    collections = {
        "registers": ("register_row_id", REQUIRED_REGISTER),
        "evidence": ("evidence_id", REQUIRED_EVIDENCE),
        "checks": ("check_id", REQUIRED_CHECK),
    }
    malformed_collection = False
    for name, (id_field, required) in collections.items():
        values = packet.get(name)
        if not isinstance(values, list):
            findings.append(finding("TRP-001", name, "must be an array"))
            malformed_collection = True
            continue
        seen: set[str] = set()
        for index, item in enumerate(values):
            locator = f"{name}[{index}]"
            if not isinstance(item, dict):
                findings.append(finding("TRP-001", locator, "must be an object"))
                continue
            item_missing = missing_fields(item, required)
            if item_missing:
                findings.append(
                    finding("TRP-001", locator, f"missing fields: {', '.join(item_missing)}")
                )
            item_id = item.get(id_field)
            if isinstance(item_id, str):
                if item_id in seen:
                    findings.append(finding("TRP-002", locator, f"duplicate ID: {item_id}"))
                seen.add(item_id)
    if malformed_collection:
        return findings

    requirement_catalog = manifest.get("requirement_catalog")
    route = manifest.get("route_sequence")
    if not isinstance(requirement_catalog, list) or not isinstance(route, list):
        return findings

    registers = {
        item["register_row_id"]: item
        for item in packet.get("registers", [])
        if isinstance(item, dict) and isinstance(item.get("register_row_id"), str)
    }
    evidence = {
        item["evidence_id"]: item
        for item in packet.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }
    requirement_ids: set[str] = set()
    for index, requirement in enumerate(requirement_catalog):
        if not isinstance(requirement, dict):
            continue
        requirement_id = requirement.get("requirement_id")
        if not isinstance(requirement_id, str):
            continue
        if requirement_id in requirement_ids:
            findings.append(
                finding(
                    "TRP-002",
                    f"manifest.requirement_catalog[{index}]",
                    f"duplicate ID: {requirement_id}",
                )
            )
        requirement_ids.add(requirement_id)

    for collection_name in ("registers", "checks"):
        for index, item in enumerate(packet.get(collection_name, [])):
            if not isinstance(item, dict):
                continue
            for evidence_id in item.get("evidence_ids", []):
                if evidence_id not in evidence:
                    findings.append(
                        finding(
                            "TRP-003",
                            f"{collection_name}[{index}].evidence_ids",
                            f"unknown evidence_id: {evidence_id}",
                        )
                    )
    for index, check in enumerate(packet.get("checks", [])):
        if not isinstance(check, dict):
            continue
        requirement_id = check.get("requirement_id")
        if isinstance(requirement_id, str) and requirement_id not in requirement_ids:
            findings.append(
                finding(
                    "TRP-003",
                    f"checks[{index}].requirement_id",
                    f"unknown requirement_id: {requirement_id}",
                )
            )
        for row_id in check.get("register_row_ids", []):
            if row_id not in registers:
                findings.append(
                    finding(
                        "TRP-003",
                        f"checks[{index}].register_row_ids",
                        f"unknown register_row_id: {row_id}",
                    )
                )
    for index, item in enumerate(packet.get("evidence", [])):
        corroborates = item.get("corroborates_evidence_id") if isinstance(item, dict) else None
        if corroborates is not None and corroborates not in evidence:
            findings.append(
                finding(
                    "TRP-003",
                    f"evidence[{index}].corroborates_evidence_id",
                    f"unknown evidence_id: {corroborates}",
                )
            )

    for collection_name in ("registers", "checks"):
        for index, item in enumerate(packet.get(collection_name, [])):
            if not isinstance(item, dict):
                continue
            surface = item.get("surface")
            if surface not in SURFACES:
                findings.append(
                    finding("TRP-004", f"{collection_name}[{index}].surface", "invalid surface")
                )
            if collection_name == "checks" and item.get("status") not in STATUSES:
                findings.append(
                    finding("TRP-004", f"checks[{index}].status", "invalid status")
                )
    for index, item in enumerate(packet.get("evidence", [])):
        if isinstance(item, dict) and item.get("trust_class") not in TRUST_CLASSES:
            findings.append(
                finding("TRP-004", f"evidence[{index}].trust_class", "invalid trust class")
            )

    execution_edges = {
        (item.get("predecessor"), item.get("consumer"))
        for item in packet.get("registers", [])
        if isinstance(item, dict)
        and item.get("surface") == "execution"
        and item.get("applicability") == "APPLICABLE"
    }
    for predecessor, consumer in zip(route, route[1:]):
        if (predecessor, consumer) not in execution_edges:
            findings.append(
                finding(
                    "TRP-005",
                    "manifest.route_sequence",
                    f"missing execution edge: {predecessor}->{consumer}",
                )
            )
    mapped_requirements = {
        (item.get("requirement_id"), item.get("surface"), item.get("target_id"))
        for item in packet.get("checks", [])
        if isinstance(item, dict)
    }
    if not requirement_catalog:
        findings.append(
            finding("TRP-006", "manifest.requirement_catalog", "denominator must not be empty")
        )
    for index, requirement in enumerate(requirement_catalog):
        if not isinstance(requirement, dict):
            continue
        requirement_id = requirement.get("requirement_id")
        surface = requirement.get("surface")
        for target_id in requirement.get("target_ids", []):
            if (requirement_id, surface, target_id) not in mapped_requirements:
                findings.append(
                    finding(
                        "TRP-006",
                        f"manifest.requirement_catalog[{index}]",
                        f"unmapped requirement target: {requirement_id}/{target_id}",
                    )
                )
    for index, check in enumerate(packet.get("checks", [])):
        if not isinstance(check, dict):
            continue
        for row_id in check.get("register_row_ids", []):
            row = registers.get(row_id)
            if row is None:
                continue
            if row.get("target_id") != check.get("target_id") or row.get(
                "surface"
            ) != check.get("surface"):
                findings.append(
                    finding(
                        "TRP-006",
                        f"checks[{index}].register_row_ids",
                        f"check/register scope mismatch: {row_id}",
                    )
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    schema_bytes = args.schema.read_bytes()
    packet_bytes = args.input.read_bytes()
    schema = json.loads(schema_bytes)
    try:
        packet = json.loads(packet_bytes)
    except json.JSONDecodeError as error:
        packet = None
        findings = [
            finding(
                "TRP-001",
                "$",
                f"invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}",
            )
        ]
    else:
        findings = validate(packet, schema)
    report = {
        "protocol_version": packet.get("protocol_version")
        if isinstance(packet, dict)
        else None,
        "validator_version": "1.0",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "limitations": "Validates packet structure and declared mappings, not business truth.",
        "status": "FAIL" if findings else "PASS",
        "schema_sha256": hashlib.sha256(schema_bytes).hexdigest(),
        "input_sha256": hashlib.sha256(packet_bytes).hexdigest(),
        "findings": findings,
        "rule_results": [
            {
                "rule_id": rule_id,
                "check_id": None,
                "register_row_id": None,
                "status": "FAIL"
                if any(item["rule_id"] == rule_id for item in findings)
                else "PASS",
            }
            for rule_id in (
                "TRP-001",
                "TRP-002",
                "TRP-003",
                "TRP-004",
                "TRP-005",
                "TRP-006",
            )
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
