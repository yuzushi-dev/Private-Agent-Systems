import json
import copy
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "topology_audit_validate.py"
SCHEMA = ROOT / "templates" / "topology-audit-schema.json"
POSITIVE = ROOT / "evidence" / "topology-audit-positive.json"
NEGATIVE = ROOT / "evidence" / "topology-audit-negative-dangling-reference.json"
NEGATIVE_PACKETS = {
    "topology-audit-negative-missing-field.json": "TRP-001",
    "topology-audit-negative-duplicate-id.json": "TRP-002",
    "topology-audit-negative-dangling-reference.json": "TRP-003",
    "topology-audit-negative-invalid-enum.json": "TRP-004",
    "topology-audit-negative-route-gap.json": "TRP-005",
    "topology-audit-negative-unmapped-requirement.json": "TRP-006",
}


def run_validator(
    packet: Path, report: Path, schema: Path = SCHEMA
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--schema",
            str(schema),
            "--input",
            str(packet),
            "--report",
            str(report),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_reference_packet_passes(tmp_path: Path) -> None:
    report = tmp_path / "positive-report.json"
    result = run_validator(POSITIVE, report)

    assert result.returncode == 0, result.stderr
    assert json.loads(report.read_text())["status"] == "PASS"


def test_dangling_register_reference_fails_trp_003(tmp_path: Path) -> None:
    report = tmp_path / "negative-report.json"
    result = run_validator(NEGATIVE, report)

    assert result.returncode == 1
    findings = json.loads(report.read_text())["findings"]
    assert any(item["rule_id"] == "TRP-003" for item in findings)


def test_supplied_schema_is_applied(tmp_path: Path) -> None:
    schema = tmp_path / "stricter-schema.json"
    schema.write_text(
        json.dumps({"type": "object", "required": ["schema_only_requirement"]})
    )
    report = tmp_path / "schema-report.json"

    result = run_validator(POSITIVE, report, schema)

    assert result.returncode == 1
    findings = json.loads(report.read_text())["findings"]
    assert any(item["rule_id"] == "TRP-001" for item in findings)


def test_execution_register_requires_surface_fields(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    del packet["registers"][0]["predecessor"]
    incomplete = tmp_path / "incomplete-execution.json"
    incomplete.write_text(json.dumps(packet))
    report = tmp_path / "surface-report.json"

    result = run_validator(incomplete, report)

    assert result.returncode == 1
    findings = json.loads(report.read_text())["findings"]
    assert any(item["rule_id"] == "TRP-001" for item in findings)


def test_every_catalog_requirement_has_a_check(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["manifest"]["requirement_catalog"].append(
        {
            "requirement_id": "REQ-UNMAPPED",
            "source": "acceptance-case://AC-99",
            "surface": "execution",
            "target_ids": ["W-1->M-9"],
        }
    )
    incomplete = tmp_path / "unmapped-requirement.json"
    incomplete.write_text(json.dumps(packet))
    report = tmp_path / "coverage-report.json"

    result = run_validator(incomplete, report)

    assert result.returncode == 1
    findings = json.loads(report.read_text())["findings"]
    assert any(item["rule_id"] == "TRP-006" for item in findings)


def test_empty_denominator_cannot_pass(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["manifest"]["requirement_catalog"] = []
    packet["checks"] = []
    incomplete = tmp_path / "empty-denominator.json"
    incomplete.write_text(json.dumps(packet))
    report = tmp_path / "empty-report.json"

    result = run_validator(incomplete, report)

    assert result.returncode == 1
    assert any(
        item["rule_id"] == "TRP-006"
        for item in json.loads(report.read_text())["findings"]
    )


def test_check_and_register_targets_must_match(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["registers"][0]["target_id"] = "W-X->M-9"
    mismatch = tmp_path / "target-mismatch.json"
    mismatch.write_text(json.dumps(packet))
    report = tmp_path / "mismatch-report.json"

    result = run_validator(mismatch, report)

    assert result.returncode == 1
    assert any(
        item["rule_id"] == "TRP-006"
        for item in json.loads(report.read_text())["findings"]
    )


def test_failure_semantics_cannot_be_empty(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["registers"][0]["failure_semantics"] = {}
    incomplete = tmp_path / "empty-failure-semantics.json"
    incomplete.write_text(json.dumps(packet))
    report = tmp_path / "failure-semantics-report.json"

    result = run_validator(incomplete, report)

    assert result.returncode == 1
    assert any(
        item["rule_id"] == "TRP-001"
        for item in json.loads(report.read_text())["findings"]
    )


def test_report_contains_reproduction_metadata(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    result = run_validator(POSITIVE, report)

    assert result.returncode == 0
    payload = json.loads(report.read_text())
    assert {
        "validator_version",
        "checked_at",
        "limitations",
        "schema_sha256",
        "input_sha256",
    } <= payload.keys()
    assert {"check_id", "register_row_id"} <= payload["rule_results"][0].keys()


def test_knowledge_only_packet_can_pass(tmp_path: Path) -> None:
    packet = {
        "protocol_version": "1.0",
        "manifest": {
            "review_id": "knowledge-only",
            "system_version": "k1",
            "route_sequence": [],
            "requirement_catalog": [
                {
                    "requirement_id": "REQ-KNOWLEDGE",
                    "source": "acceptance-case://K-1",
                    "surface": "knowledge",
                    "target_ids": ["EDGE-K1"],
                }
            ],
        },
        "registers": [
            {
                "register_row_id": "REG-K1",
                "surface": "knowledge",
                "target_id": "EDGE-K1",
                "applicability": "APPLICABLE",
                "owner": "knowledge-owner",
                "evidence_ids": ["EV-K1"],
                "source_type": "Document",
                "target_type": "Claim",
                "relationship_meaning": "supports",
                "provenance_status": "verified",
                "checked_date": "2026-07-24",
                "validity_rule": "recheck-30d",
                "assertion_class": "source-assertion",
                "authorization_scope": "tenant-read",
                "merge_rule": "retain-provenance",
                "conflict_rule": "retain-both",
            }
        ],
        "evidence": [
            {
                "evidence_id": "EV-K1",
                "locator": "source://K1",
                "origin": "source-register",
                "collector": "independent-reviewer",
                "integrity_control": "sha256-manifest",
                "trust_class": "T1",
                "limitations": "Snapshot only",
            }
        ],
        "checks": [
            {
                "check_id": "CHK-K1",
                "requirement_id": "REQ-KNOWLEDGE",
                "surface": "knowledge",
                "requirement": "Edge retains provenance",
                "target_id": "EDGE-K1",
                "register_row_ids": ["REG-K1"],
                "evidence_ids": ["EV-K1"],
                "status": "SUPPORTED",
                "rationale": "Source locator resolves",
                "owner": "knowledge-owner",
            }
        ],
    }
    source = tmp_path / "knowledge-only.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "knowledge-report.json"

    result = run_validator(source, report)

    assert result.returncode == 0, report.read_text()


def test_not_applicable_register_requires_reason_but_not_surface_fields(
    tmp_path: Path,
) -> None:
    packet = json.loads(POSITIVE.read_text())
    row = packet["registers"][0]
    for field in (
        "predecessor",
        "consumer",
        "trigger",
        "state_in",
        "state_out",
        "consumed_result_evidence",
        "failure_semantics",
        "join_owner",
        "partial_result",
        "required_authorization",
        "observed_authorization",
        "telemetry_locator",
    ):
        row.pop(field)
    row["applicability"] = "NOT_APPLICABLE"
    row["applicability_reason"] = "Execution surface absent from this boundary"
    packet["manifest"]["route_sequence"] = []
    packet["checks"][0]["status"] = "NOT_APPLICABLE"
    source = tmp_path / "not-applicable.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "not-applicable-report.json"

    result = run_validator(source, report)

    assert result.returncode == 0, report.read_text()


def test_malformed_manifest_returns_fail_report_instead_of_crashing(
    tmp_path: Path,
) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["manifest"] = []
    source = tmp_path / "malformed-manifest.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "malformed-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert report.exists(), result.stderr
    assert json.loads(report.read_text())["status"] == "FAIL"


def test_invalid_packet_json_returns_fail_report(tmp_path: Path) -> None:
    source = tmp_path / "invalid.json"
    source.write_text('{"protocol_version":')
    report = tmp_path / "invalid-json-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert report.exists(), result.stderr
    payload = json.loads(report.read_text())
    assert payload["status"] == "FAIL"
    assert payload["findings"][0]["rule_id"] == "TRP-001"


@pytest.mark.parametrize("field", ["registers", "evidence", "checks"])
def test_malformed_collection_returns_fail_report(
    tmp_path: Path, field: str
) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet[field] = None
    source = tmp_path / f"malformed-{field}.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / f"malformed-{field}-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert report.exists(), result.stderr
    assert json.loads(report.read_text())["status"] == "FAIL"


def test_nested_malformed_value_returns_fail_report(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["checks"][0]["evidence_ids"] = None
    source = tmp_path / "malformed-nested-value.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "malformed-nested-value-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert report.exists(), result.stderr
    assert json.loads(report.read_text())["status"] == "FAIL"


def test_requirement_ids_must_be_unique(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["manifest"]["requirement_catalog"].append(
        copy.deepcopy(packet["manifest"]["requirement_catalog"][0])
    )
    source = tmp_path / "duplicate-requirement.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "duplicate-requirement-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert any(
        item["rule_id"] == "TRP-002"
        for item in json.loads(report.read_text())["findings"]
    )


def test_check_requirement_reference_must_resolve(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    extra_check = copy.deepcopy(packet["checks"][0])
    extra_check["check_id"] = "CHK-UNKNOWN-REQUIREMENT"
    extra_check["requirement_id"] = "REQ-UNKNOWN"
    packet["checks"].append(extra_check)
    source = tmp_path / "unknown-requirement.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "unknown-requirement-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert any(
        item["rule_id"] == "TRP-003"
        for item in json.loads(report.read_text())["findings"]
    )


def test_not_applicable_execution_row_does_not_cover_route(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["registers"][0]["applicability"] = "NOT_APPLICABLE"
    packet["registers"][0]["applicability_reason"] = "Boundary is absent"
    packet["checks"][0]["status"] = "NOT_APPLICABLE"
    source = tmp_path / "not-applicable-route.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "not-applicable-route-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert any(
        item["rule_id"] == "TRP-005"
        for item in json.loads(report.read_text())["findings"]
    )


def test_supported_check_requires_evidence(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["checks"][0]["evidence_ids"] = []
    source = tmp_path / "unsupported-supported-check.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "evidence-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert any(
        item["rule_id"] == "TRP-001"
        for item in json.loads(report.read_text())["findings"]
    )


def test_applicable_surface_fields_cannot_be_empty(tmp_path: Path) -> None:
    packet = json.loads(POSITIVE.read_text())
    packet["registers"][0]["consumed_result_evidence"] = ""
    source = tmp_path / "empty-surface-field.json"
    source.write_text(json.dumps(packet))
    report = tmp_path / "empty-surface-field-report.json"

    result = run_validator(source, report)

    assert result.returncode == 1
    assert any(
        item["rule_id"] == "TRP-001"
        for item in json.loads(report.read_text())["findings"]
    )


@pytest.mark.parametrize(
    ("filename", "expected_rule"),
    NEGATIVE_PACKETS.items(),
)
def test_published_negative_packets_fail_for_advertised_rule(
    tmp_path: Path, filename: str, expected_rule: str
) -> None:
    report = tmp_path / f"{Path(filename).stem}-report.json"

    result = run_validator(ROOT / "evidence" / filename, report)

    assert result.returncode == 1
    findings = json.loads(report.read_text())["findings"]
    assert {item["rule_id"] for item in findings} == {expected_rule}


def test_invalid_enum_fixture_exercises_check_status() -> None:
    packet = json.loads(
        (ROOT / "evidence" / "topology-audit-negative-invalid-enum.json").read_text()
    )

    assert packet["checks"]
    assert packet["checks"][0]["status"] not in {
        "SUPPORTED",
        "PARTIAL",
        "UNSUPPORTED",
        "INCONCLUSIVE",
        "NOT_APPLICABLE",
    }
