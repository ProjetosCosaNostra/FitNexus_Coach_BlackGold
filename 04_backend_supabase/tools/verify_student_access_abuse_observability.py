from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
MIGRATIONS = BACKEND / "migrations"

AUTHORITY = BACKEND / "student_access_abuse_authority.json"
STAGE21 = MIGRATIONS / "20260819103700_stage21_student_access_security_boundary.sql"
STAGE24 = MIGRATIONS / "20260819192100_stage24_student_access_abuse_observability.sql"
EXTERNAL_GATES = BACKEND / "external_gate_evidence_placeholders.json"

FAILURE_CLASSES = (
    "BGF-STUDENT-ACCESS-ABUSE-BLIND-SPOT-160",
    "BGF-STUDENT-ACCESS-ABUSE-THRESHOLD-DRIFT-161",
    "BGF-INCIDENT-GATE-SELF-ATTESTATION-162",
)

EXPECTED_SIGNALS = [
    {
        "signal_type": "rate_limit_burst",
        "source_outcome": "rate_limited",
        "subject": "link_id+operation",
        "rolling_window_seconds": 300,
        "dedupe_bucket_seconds": 300,
        "threshold": 10,
        "severity": "high",
    },
    {
        "signal_type": "command_replay_burst",
        "source_outcome": "replay",
        "subject": "link_id+operation",
        "rolling_window_seconds": 600,
        "dedupe_bucket_seconds": 600,
        "threshold": 3,
        "severity": "high",
    },
    {
        "signal_type": "token_rotation_burst",
        "source_outcome": "rotated",
        "subject": "organization_id+student_id",
        "rolling_window_seconds": 1800,
        "dedupe_bucket_seconds": 1800,
        "threshold": 4,
        "severity": "medium",
    },
]


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_ABUSE_OBSERVABILITY_GUARD=FAIL\n" + message)


def read_text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def require(text: str, fragments: list[str], label: str) -> None:
    missing = [fragment for fragment in fragments if fragment.lower() not in text.lower()]
    if missing:
        fail(f"{label} missing invariants: {missing}")


def main() -> None:
    authority = read_json(AUTHORITY)
    stage21 = read_text(STAGE21).lower()
    stage24 = read_text(STAGE24).lower()
    external = read_json(EXTERNAL_GATES)

    if authority.get("schema_version") != 1:
        fail(f"{FAILURE_CLASSES[1]} authority schema_version must remain 1")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail(f"{FAILURE_CLASSES[1]} wrong Supabase project authority")

    failure_classes = authority.get("failure_classes")
    if failure_classes != list(FAILURE_CLASSES):
        fail(f"authority failure classes drifted: {failure_classes!r}")

    if authority.get("source_table") != "private.student_access_security_events":
        fail(f"{FAILURE_CLASSES[0]} source event authority drifted")
    if authority.get("signal_table") != "private.student_access_security_signals":
        fail(f"{FAILURE_CLASSES[0]} signal table authority drifted")
    if authority.get("posture_view") != "private.student_access_security_posture_v1":
        fail(f"{FAILURE_CLASSES[0]} posture view authority drifted")
    if authority.get("signals") != EXPECTED_SIGNALS:
        fail(f"{FAILURE_CLASSES[1]} threshold authority drifted")

    posture = authority.get("posture", {})
    if posture.get("window_seconds") != 3600:
        fail(f"{FAILURE_CLASSES[1]} posture window must remain 3600 seconds")

    privacy = authority.get("privacy", {})
    if any(
        privacy.get(key) is not False
        for key in ("raw_token_stored", "ip_address_stored", "arbitrary_request_payload_stored")
    ):
        fail(f"{FAILURE_CLASSES[0]} abuse telemetry privacy boundary weakened")

    launch = authority.get("launch_authority", {})
    if any(
        launch.get(key) is not False
        for key in (
            "can_promote_incident_response_gate",
            "can_promote_production_deployment_gate",
            "can_enable_paid_ads",
        )
    ):
        fail(f"{FAILURE_CLASSES[2]} observability authority may not promote launch gates")

    require(
        stage21,
        [
            "create table if not exists private.student_access_security_events",
            "outcome text not null check (outcome in ('allowed','rate_limited','replay','rotated'))",
            "grant select on private.student_access_security_events to service_role",
        ],
        FAILURE_CLASSES[0],
    )

    require(
        stage24,
        [
            "create table if not exists private.student_access_security_signals",
            "'rate_limit_burst'",
            "'command_replay_burst'",
            "'token_rotation_burst'",
            "unique (signal_type, subject_key, operation, window_started_at)",
            "student_access_security_events_abuse_window_idx",
            "student_access_security_events_rotation_subject_idx",
            "student_access_security_signals_link_fk_idx",
            "create or replace function private.detect_student_access_abuse_signal_v1()",
            "after insert on private.student_access_security_events",
            "when (new.outcome in ('rate_limited','replay','rotated'))",
            "create or replace view private.student_access_security_posture_v1",
            "with (security_invoker = true)",
            "grant select on private.student_access_security_signals to service_role",
            "grant select on private.student_access_security_posture_v1 to service_role",
            "revoke all on private.student_access_security_signals from public, anon, authenticated",
            "revoke all on function private.detect_student_access_abuse_signal_v1()",
        ],
        FAILURE_CLASSES[0],
    )

    threshold_fragments = [
        "new.occurred_at - interval '5 minutes'",
        "if v_count >= 10 then",
        "date_bin(\n        interval '5 minutes'",
        "new.occurred_at - interval '10 minutes'",
        "if v_count >= 3 then",
        "date_bin(\n        interval '10 minutes'",
        "new.occurred_at - interval '30 minutes'",
        "if v_count >= 4 then",
        "date_bin(\n        interval '30 minutes'",
        "v_severity := 'high'",
        "v_severity := 'medium'",
    ]
    require(stage24, threshold_fragments, FAILURE_CLASSES[1])

    forbidden_stage24 = [
        "create or replace function public.",
        "grant execute on function private.detect_student_access_abuse_signal_v1() to anon",
        "grant execute on function private.detect_student_access_abuse_signal_v1() to authenticated",
        "grant select on private.student_access_security_signals to anon",
        "grant select on private.student_access_security_signals to authenticated",
        "raw_token",
        "ip_address",
    ]
    present = [marker for marker in forbidden_stage24 if marker in stage24]
    if present:
        fail(f"{FAILURE_CLASSES[0]} forbidden exposure/storage markers found: {present}")

    gates = external.get("gates", {})
    incident = gates.get("incident_response", {})
    production = gates.get("production_deployment", {})
    for gate_name, gate in (("incident_response", incident), ("production_deployment", production)):
        if gate.get("placeholder_only") is not True:
            fail(f"{FAILURE_CLASSES[2]} {gate_name} placeholder was promoted")
        if gate.get("evidence_ref") is not None or gate.get("evidence_digest") is not None:
            fail(f"{FAILURE_CLASSES[2]} {gate_name} received fabricated evidence")

    rules = external.get("rules", {})
    if rules.get("this_file_can_mark_gate_ready") is not False:
        fail(f"{FAILURE_CLASSES[2]} placeholder file gained promotion authority")

    blind_spot = authority.get("known_external_boundary", {}).get("blind_spot", "").lower()
    if "invalid-token" not in blind_spot or "client ip" not in blind_spot:
        fail(f"{FAILURE_CLASSES[0]} deploy-layer blind spot is no longer explicit")

    print("STUDENT_ACCESS_ABUSE_OBSERVABILITY_GUARD=PASS")
    print("ABUSE_SIGNAL_TYPES=3")
    print("RATE_LIMIT_BURST=10_IN_5M")
    print("COMMAND_REPLAY_BURST=3_IN_10M")
    print("TOKEN_ROTATION_BURST=4_IN_30M")
    print("POSTURE_WINDOW=60M")
    print("RAW_TOKEN_STORAGE=DENIED")
    print("NETWORK_ORIGIN_BLIND_SPOT=EXPLICIT_DEPLOY_LAYER_BOUNDARY")
    print("INCIDENT_RESPONSE_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
