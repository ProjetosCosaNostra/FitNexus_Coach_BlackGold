from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

FAILURE_CLASS = "BGF-STAGE74-INDEPENDENT-REVIEW-INTAKE-GUARD-715"
PLACEHOLDER_RE = re.compile(r"<[^>]+>|placeholder|tbd|to[_ -]?be[_ -]?defined|example", re.IGNORECASE)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_OUTCOMES = {
    "APPROVED_WITHOUT_CHANGES",
    "APPROVED_WITH_REQUIRED_CHANGES",
    "NOT_APPROVED_REQUIRES_REVISION",
}
SOURCE_KEYS = {
    "privacy_notice",
    "processing_role_matrix",
    "dsr_runbook",
    "incident_runbook",
    "open_decisions",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|api[_-]?key|access[_-]?token|service[_-]?role[_-]?key|client[_-]?secret|secret[_-]?value)\s*[:=]\s*[^\s,}\]]+", re.IGNORECASE),
)


def fail(detail: str) -> None:
    raise SystemExit(
        "STAGE74_INDEPENDENT_REVIEW_CANDIDATE=FAIL\n"
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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def validate_timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or PLACEHOLDER_RE.search(value):
        fail("reviewed_at_utc must be a real timezone-aware ISO-8601 timestamp")
    raw = value.strip()
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError:
        fail("reviewed_at_utc is not valid ISO-8601")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail("reviewed_at_utc must be timezone-aware")
    if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
        fail("reviewed_at_utc cannot be in the future")
    return parsed.astimezone(timezone.utc).isoformat()


def validate_review_artifact(path: Path) -> str:
    if not path.is_file() or path.stat().st_size <= 0:
        fail("review artifact must be a real non-empty file")
    if path.stat().st_size > 8 * 1024 * 1024:
        fail("review artifact exceeds 8 MiB intake boundary")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail("review artifact must be UTF-8 text for secret-marker inspection")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail("review artifact contains a secret-like marker; redact before intake")
    return sha256_file(path)


def validate_packet(path: Path) -> tuple[dict, dict[str, str], str]:
    packet = load_json(path, "Stage74 review packet")
    if packet.get("schema_version") != 1:
        fail("review packet schema_version drift")
    if packet.get("stage") != "STAGE74_CONTROLLER_PROCESSOR_INDEPENDENT_REVIEW_INTAKE":
        fail("review packet stage drift")
    if packet.get("output_kind") != "NON_ATTESTING_INDEPENDENT_REVIEW_INTAKE_PACKET":
        fail("review packet output_kind drift")
    if packet.get("packet_state") != "EXACT_DRAFT_BYTES_BOUND_FOR_EXTERNAL_REVIEW_NO_REVIEW_PERFORMED_NOT_EVIDENCE":
        fail("review packet state drift")
    decision = packet.get("decision")
    if not isinstance(decision, dict) or decision.get("decision_id") != "CONTROLLER_PROCESSOR_ROLE_MATRIX":
        fail("review packet decision drift")
    if decision.get("state") != "OPEN" or decision.get("resolved") is not False:
        fail("review packet must preserve the open decision")
    if decision.get("fanout_count") != 4:
        fail("review packet fanout drift")

    review_sources = packet.get("review_sources")
    if not isinstance(review_sources, dict) or set(review_sources) != SOURCE_KEYS:
        fail("review packet source set drift")
    digests: dict[str, str] = {}
    for key in sorted(SOURCE_KEYS):
        source = review_sources.get(key)
        if not isinstance(source, dict):
            fail(f"review packet source missing: {key}")
        digest = str(source.get("sha256", ""))
        if not SHA256_RE.fullmatch(digest):
            fail(f"review packet source digest invalid: {key}")
        if source.get("approved") is not False or source.get("gate_evidence") is not False:
            fail(f"review packet source improperly promoted: {key}")
        digests[key] = digest

    for key in (
        "real_reviewer_reference_present",
        "real_review_artifact_present",
        "independent_review_completed",
        "candidate_documents_promoted",
        "open_decision_closed",
        "evidence_ref_created",
        "evidence_digest_promoted",
        "evidence_migration_created",
        "gate_ready_attested",
        "network_call_performed",
        "provider_call_performed",
        "supabase_mutation_performed",
        "deployment_performed",
        "controlled_launch_promoted",
        "paid_media_promoted",
    ):
        if packet.get(key) is not False:
            fail(f"review packet non-attesting boundary drift: {key}")
    return packet, digests, sha256_file(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-packet", required=True, type=Path)
    parser.add_argument("--review-input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    packet, packet_digests, packet_file_sha = validate_packet(args.review_packet.resolve())
    review = load_json(args.review_input.resolve(), "real independent review input")

    if review.get("schema_version") != 1:
        fail("review input schema_version must be 1")
    if review.get("input_kind") != "REAL_INDEPENDENT_CONTROLLER_PROCESSOR_REVIEW_INPUT":
        fail("review input_kind drift")
    if review.get("status") == "PLACEHOLDER_TEMPLATE_NOT_REAL_REVIEW" or PLACEHOLDER_RE.search(str(review.get("status", ""))):
        fail("review input is still placeholder-like")
    if review.get("test_fixture") is not False:
        fail("review input is a test fixture; real independent review is required")
    if review.get("contains_placeholders") is not False:
        fail("review input declares placeholders")
    if review.get("decision_id") != "CONTROLLER_PROCESSOR_ROLE_MATRIX":
        fail("review input decision_id drift")

    reviewer_reference = str(review.get("reviewer_reference", "")).strip()
    reviewer_role = str(review.get("reviewer_role", "")).strip()
    if len(reviewer_reference) < 3 or PLACEHOLDER_RE.search(reviewer_reference):
        fail("real traceable reviewer reference is required")
    if len(reviewer_role) < 3 or PLACEHOLDER_RE.search(reviewer_role):
        fail("real reviewer role/qualification is required")
    reviewed_at_utc = validate_timestamp(review.get("reviewed_at_utc"))
    if review.get("independent_review_confirmed") is not True:
        fail("independent review confirmation is required")
    if review.get("reviewer_acknowledged_exact_source_digests") is not True:
        fail("reviewer must acknowledge exact source digests")
    if review.get("review_artifact_secret_values_absent_or_redacted_confirmed") is not True:
        fail("review artifact secret-redaction confirmation is required")

    outcome = str(review.get("outcome", "")).strip()
    if outcome not in ALLOWED_OUTCOMES:
        fail("review outcome must be one of the three allowed real-review outcomes")

    reviewed_source_sha256 = review.get("reviewed_source_sha256")
    if not isinstance(reviewed_source_sha256, dict) or set(reviewed_source_sha256) != SOURCE_KEYS:
        fail("reviewed_source_sha256 must contain exactly the five packet source keys")
    for key in SOURCE_KEYS:
        if reviewed_source_sha256.get(key) != packet_digests[key]:
            fail(f"review source digest mismatch: {key}")

    artifact_raw = str(review.get("review_artifact_path", "")).strip()
    if not artifact_raw or PLACEHOLDER_RE.search(artifact_raw):
        fail("real review artifact path is required")
    review_artifact_sha = validate_review_artifact(Path(artifact_raw).expanduser().resolve())

    requires_new_candidate_bytes = outcome in {
        "APPROVED_WITH_REQUIRED_CHANGES",
        "NOT_APPROVED_REQUIRES_REVISION",
    }
    candidate = {
        "schema_version": 1,
        "stage": "STAGE74_CONTROLLER_PROCESSOR_INDEPENDENT_REVIEW_INTAKE",
        "output_kind": "DIGEST_ONLY_INDEPENDENT_REVIEW_CANDIDATE",
        "candidate_state": "REAL_REVIEW_DIGEST_BOUND_AWAITING_CANONICAL_GATE_REVIEW_NOT_GATE_EVIDENCE",
        "decision_id": "CONTROLLER_PROCESSOR_ROLE_MATRIX",
        "packet_source_commit_sha": packet.get("source_commit_sha"),
        "review_packet_file_sha256": packet_file_sha,
        "reviewed_source_sha256": packet_digests,
        "reviewed_at_utc": reviewed_at_utc,
        "reviewer_reference_sha256": sha256_bytes(reviewer_reference.encode("utf-8")),
        "reviewer_role": reviewer_role,
        "review_artifact_sha256": review_artifact_sha,
        "outcome": outcome,
        "requires_new_candidate_bytes": requires_new_candidate_bytes,
        "reviewer_identity_copied": False,
        "review_artifact_path_copied": False,
        "review_artifact_contents_copied": False,
        "secret_values_copied": False,
        "candidate_documents_updated": False,
        "candidate_documents_promoted": False,
        "open_decision_closed": False,
        "gate_ready_attested": False,
        "evidence_ref_created": False,
        "evidence_digest_promoted": False,
        "evidence_migration_created": False,
        "network_call_performed": False,
        "provider_call_performed": False,
        "supabase_mutation_performed": False,
        "deployment_performed": False,
        "controlled_launch_promoted": False,
        "paid_media_promoted": False,
        "next_action": "CANONICAL_GATE_REVIEW_AND_ANY_REQUIRED_CANDIDATE_REVISION_BEFORE_EVIDENCE_PROMOTION",
    }

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("STAGE74_INDEPENDENT_REVIEW_CANDIDATE=PASS_DIGEST_ONLY")
    print(f"OUTCOME={outcome}")
    print(f"REQUIRES_NEW_CANDIDATE_BYTES={str(requires_new_candidate_bytes).lower()}")
    print("REVIEWER_IDENTITY_COPIED=false")
    print("REVIEW_ARTIFACT_PATH_COPIED=false")
    print("OPEN_DECISION_CLOSED=false")
    print("GATE_READY=false")
    print("REMOTE_MUTATION=false")


if __name__ == "__main__":
    main()
