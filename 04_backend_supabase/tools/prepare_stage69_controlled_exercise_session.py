from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER_RE = re.compile(r"<[^>]+>|placeholder|tbd|to[_ -]?be[_ -]?defined|example", re.IGNORECASE)
REQUIRED_ROLES = (
    "dsr_primary_owner",
    "dsr_backup_owner",
    "incident_commander",
    "privacy_owner",
    "technical_owner",
    "exercise_facilitator",
)
FAILURE_CLASS = "BGF-STAGE69-CONTROLLED-EXERCISE-BOUNDARY-GUARD-665"


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE69_CONTROLLED_EXERCISE_SESSION_PREPARATION=FAIL\n"
        f"FAILURE_CLASS={FAILURE_CLASS}\n"
        f"DETAIL={detail}"
    )


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to load {label}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_real_owner_input(path: Path) -> tuple[dict[str, str], str]:
    owners = load_json(path, "owner input")
    if owners.get("schema_version") != 1:
        fail("owner input schema_version must be 1")
    if owners.get("input_kind") != "REAL_ASSIGNED_OWNER_INPUT":
        fail("owner input_kind must be REAL_ASSIGNED_OWNER_INPUT")
    if owners.get("test_fixture") is not False:
        fail("owner input marked as test fixture; real assigned owners are required")
    if owners.get("contains_placeholders") is not False:
        fail("owner input declares placeholders; real assigned owners are required")
    if PLACEHOLDER_RE.search(str(owners.get("status", ""))):
        fail("owner input status remains placeholder-like")

    roles = owners.get("roles")
    if not isinstance(roles, dict):
        fail("owner input roles must be an object")
    if set(roles) != set(REQUIRED_ROLES):
        fail("owner input must contain exactly the six required roles")

    assignment_digests: dict[str, str] = {}
    seen_names: set[str] = set()
    for role in REQUIRED_ROLES:
        entry = roles.get(role)
        if not isinstance(entry, dict):
            fail(f"role {role} must be an object")
        name = str(entry.get("display_name", "")).strip()
        if len(name) < 3 or PLACEHOLDER_RE.search(name):
            fail(f"role {role} has missing or placeholder display_name")
        if name.casefold() in seen_names and role in {"dsr_primary_owner", "dsr_backup_owner"}:
            fail("DSR primary and backup owners must be distinct")
        seen_names.add(name.casefold())
        if entry.get("acknowledged") is not True:
            fail(f"role {role} has not acknowledged assignment")
        artifact_raw = str(entry.get("assignment_artifact_path", "")).strip()
        if not artifact_raw or PLACEHOLDER_RE.search(artifact_raw):
            fail(f"role {role} assignment artifact path missing or placeholder")
        artifact = Path(artifact_raw).expanduser().resolve()
        if not artifact.is_file() or artifact.stat().st_size <= 0:
            fail(f"role {role} assignment artifact must be a real non-empty file")
        assignment_digests[role] = sha256_file(artifact)

    return assignment_digests, sha256_file(path)


def validate_stage68_bundle(path: Path, source_sha: str) -> tuple[dict, str]:
    bundle = load_json(path, "Stage68 bundle")
    if bundle.get("schema_version") != 1:
        fail("Stage68 bundle schema_version drift")
    if bundle.get("stage") != "STAGE68_SYNTHETIC_GOVERNANCE_REHEARSAL_COMPILER":
        fail("Stage68 bundle stage drift")
    if bundle.get("output_kind") != "NON_ATTESTING_SYNTHETIC_GOVERNANCE_REHEARSAL_BUNDLE":
        fail("Stage68 bundle output_kind drift")
    if bundle.get("bundle_state") != "COMPILED_REHEARSAL_PACKETS_NOT_EXECUTED_NOT_OPERATIONAL_OR_LEGAL_EVIDENCE":
        fail("Stage68 bundle state drift")
    if bundle.get("source_commit_sha") != source_sha:
        fail("Stage68 bundle source SHA does not match requested source SHA")
    if bundle.get("packet_count") != 8:
        fail("Stage68 bundle must contain exactly eight packets")
    packets = bundle.get("packets")
    if not isinstance(packets, list) or len(packets) != 8:
        fail("Stage68 packets missing or count drift")
    if bundle.get("exercise_executed") is not False:
        fail("Stage68 bundle unexpectedly claims exercise execution")
    for key in (
        "real_customer_data_used",
        "network_call_performed",
        "supabase_mutation_performed",
        "provider_call_performed",
        "legal_review_attested",
        "operational_review_attested",
        "evidence_migration_created",
        "data_subject_request_gate_ready_attested",
        "incident_response_gate_ready_attested",
        "controlled_launch_promoted",
        "paid_media_promoted",
    ):
        if bundle.get(key) is not False:
            fail(f"Stage68 bundle boundary drift: {key}")
    return bundle, sha256_file(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--stage68-bundle", required=True, type=Path)
    parser.add_argument("--owner-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not SHA1_RE.fullmatch(source_sha):
        fail("--source-sha must be exact 40-character lower-hex Git SHA")

    assignment_digests, owner_input_sha = validate_real_owner_input(args.owner_input.resolve())
    bundle, bundle_file_sha = validate_stage68_bundle(args.stage68_bundle.resolve(), source_sha)

    assignments = []
    for role in REQUIRED_ROLES:
        assignments.append({
            "role": role,
            "assignment_artifact_sha256": assignment_digests[role],
            "owner_identity_copied": False,
            "assignment_artifact_path_copied": False,
        })

    packet_bindings = []
    for packet in sorted(bundle["packets"], key=lambda item: str(item.get("scenario_id", ""))):
        scenario_id = str(packet.get("scenario_id", ""))
        kind = str(packet.get("kind", ""))
        scenario_sha = str(packet.get("scenario_definition_sha256", ""))
        if not scenario_id or kind not in {"dsr", "incident"} or not re.fullmatch(r"[0-9a-f]{64}", scenario_sha):
            fail("Stage68 packet structure drift")
        required_roles = (
            ["dsr_primary_owner", "dsr_backup_owner", "exercise_facilitator"]
            if kind == "dsr"
            else ["incident_commander", "privacy_owner", "technical_owner", "exercise_facilitator"]
        )
        packet_bindings.append({
            "scenario_id": scenario_id,
            "kind": kind,
            "scenario_definition_sha256": scenario_sha,
            "required_roles": required_roles,
            "exercise_executed": False,
            "completion_record_present": False,
        })

    receipt = {
        "schema_version": 1,
        "stage": "STAGE69_CONTROLLED_EXERCISE_EXECUTION_BOUNDARY",
        "output_kind": "NON_ATTESTING_CONTROLLED_EXERCISE_SESSION_CANDIDATE",
        "session_state": "READY_FOR_HUMAN_CONTROLLED_EXERCISE_NOT_EXECUTED_NOT_EVIDENCE",
        "source_commit_sha": source_sha,
        "stage68_bundle_file_sha256": bundle_file_sha,
        "stage68_bundle_sha256": bundle.get("bundle_sha256"),
        "owner_input_sha256": owner_input_sha,
        "assignment_artifacts": assignments,
        "packet_bindings": packet_bindings,
        "owner_identity_copied_to_receipt": False,
        "owner_artifact_path_copied_to_receipt": False,
        "real_customer_data_used": False,
        "network_call_performed": False,
        "supabase_mutation_performed": False,
        "provider_call_performed": False,
        "exercise_executed": False,
        "legal_review_attested": False,
        "operational_sufficiency_attested": False,
        "stage44_evidence_attested": False,
        "stage45_evidence_attested": False,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "data_subject_request_gate_ready_attested": False,
        "incident_response_gate_ready_attested": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "HUMAN_CONTROLLED_EXERCISE_AND_INDEPENDENT_REVIEW_REQUIRED_BEFORE_ANY_EXERCISE_RECEIPT_OR_GATE_EVIDENCE",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("STAGE69_CONTROLLED_EXERCISE_SESSION_PREPARATION=PASS_CANDIDATE_ONLY")
    print(f"SOURCE_SHA={source_sha}")
    print("REAL_OWNER_ASSIGNMENTS_VALIDATED_STRUCTURALLY=true")
    print("OWNER_IDENTITIES_COPIED=false")
    print("EXERCISE_EXECUTED=false")
    print("STAGE44_EVIDENCE=false")
    print("STAGE45_EVIDENCE=false")
    print("GATE_READY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
