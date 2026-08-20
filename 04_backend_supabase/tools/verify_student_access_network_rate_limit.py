from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
MIGRATION = BACKEND / "migrations" / "20260820063000_stage27_student_network_origin_rate_limit.sql"
AUTHORITY = BACKEND / "student_access_network_rate_limit_authority.json"
NETWORK_AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
ABUSE_AUTHORITY = BACKEND / "student_access_abuse_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
EXTERNAL_GATES = BACKEND / "external_gate_evidence_placeholders.json"

FAILURE_CLASSES = (
    "BGF-EDGE-INVALID-TOKEN-RATE-LIMIT-174",
    "BGF-NETWORK-ORIGIN-RAW-PERSISTENCE-175",
    "BGF-NETWORK-THROTTLE-CALLER-LIMIT-OVERRIDE-176",
    "BGF-EDGE-SECRET-KEY-LEAK-177",
)

THRESHOLDS = {
    "get_workout": 120,
    "start_workout": 30,
    "set_completion": 120,
    "get_feedback_context": 90,
    "submit_feedback": 30,
}

DIRECT_V2_RPCS = (
    "get_student_workout_v2",
    "start_student_workout_v2",
    "set_student_exercise_completion_v2",
    "get_student_feedback_context_v2",
    "submit_student_workout_feedback_v2",
)


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_NETWORK_RATE_LIMIT_GUARD=FAIL\n" + message)


def read_text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def require(text: str, fragments: tuple[str, ...], failure_class: str) -> None:
    lower = text.lower()
    missing = [fragment for fragment in fragments if fragment.lower() not in lower]
    if missing:
        fail(f"{failure_class} missing invariants: {missing}")


def main() -> None:
    authority = read_json(AUTHORITY)
    network = read_json(NETWORK_AUTHORITY)
    abuse = read_json(ABUSE_AUTHORITY)
    ledger = read_json(LEDGER)
    external = read_json(EXTERNAL_GATES)
    migration = read_text(MIGRATION)
    lower = migration.lower()

    if authority.get("schema_version") != 1:
        fail("Stage 27 authority schema_version must remain 1")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project authority")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("Stage 27 failure-class authority drifted")
    if authority.get("current_state") != "REPO_ONLY_DDL_NOT_APPLIED":
        fail("Stage 27 may not self-attest remote application")

    migration_auth = authority.get("migration", {})
    expected_migration = {
        "repository_file": "04_backend_supabase/migrations/20260820063000_stage27_student_network_origin_rate_limit.sql",
        "migration_name": "stage27_student_network_origin_rate_limit",
        "remote_applied": False,
        "migration_ledger_state": "repo_only_declared",
    }
    for key, expected in expected_migration.items():
        if migration_auth.get(key) != expected:
            fail(f"migration authority drift for {key}: {migration_auth.get(key)!r}")

    trusted = authority.get("trusted_origin_authority", {})
    expected_trust = {
        "source": "cf-connecting-ip",
        "source_state": "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED",
        "edge_function_version": 2,
        "spoof_proof_workflow_run_id": 32338900002,
        "spoof_proof_outcome": "BLOCKED_AT_EDGE_403",
        "client_can_force_source": False,
    }
    for key, expected in expected_trust.items():
        if trusted.get(key) != expected:
            fail(f"{FAILURE_CLASSES[0]} trusted-origin authority drift for {key}")

    network_runtime = network.get("observed_runtime", {})
    if network.get("current_state") != "ORIGIN_SOURCE_SPOOF_RESISTANCE_VERIFIED":
        fail(f"{FAILURE_CLASSES[0]} Stage 26 trusted origin was not preserved")
    if network_runtime.get("runtime_origin_candidate") != "cf-connecting-ip":
        fail(f"{FAILURE_CLASSES[0]} trusted origin source drifted")
    if network_runtime.get("runtime_origin_candidate_trusted_for_security") is not True:
        fail(f"{FAILURE_CLASSES[0]} trusted origin source is no longer verified")

    if authority.get("route_thresholds_per_minute") != THRESHOLDS:
        fail(f"{FAILURE_CLASSES[2]} database-owned threshold authority drifted")

    db = authority.get("database_contract", {})
    expected_db = {
        "private_function": "private.student_access_network_rate_limit_v1(text,text)",
        "public_bridge": "public.check_student_access_network_rate_limit_v1(text,text)",
        "public_bridge_security_mode": "SECURITY_INVOKER",
        "public_bridge_execute_role": "service_role",
        "caller_can_supply_limit": False,
        "raw_network_origin_persisted": False,
        "origin_digest_persisted": True,
        "origin_digest_algorithm": "HMAC-SHA256",
        "pepper_generated_at_remote_migration_apply": True,
        "pepper_length_bytes": 32,
        "pepper_stored_in_repository": False,
        "pepper_direct_service_role_access": False,
        "bucket_retention_days": 2,
        "rate_limit_error": "STUDENT_NETWORK_RATE_LIMITED",
        "signal_type": "network_rate_limit_burst",
        "signal_severity": "high",
    }
    for key, expected in expected_db.items():
        if db.get(key) != expected:
            fail(f"database privacy/authority drift for {key}: {db.get(key)!r}")

    # Migration ledger must explicitly admit the reviewed repo-only DDL before merge/apply.
    divergences = ledger.get("declared_divergences", [])
    stage27 = [
        item for item in divergences
        if item.get("direction") == "repo_only"
        and item.get("name") == "stage27_student_network_origin_rate_limit"
    ]
    if len(stage27) != 1:
        fail("Stage 27 repo_only migration divergence is missing or duplicated")
    if stage27[0].get("related_failure_class") != FAILURE_CLASSES[0]:
        fail("Stage 27 migration divergence failure class drifted")

    require(
        migration,
        (
            "create table if not exists private.student_access_network_origin_secret",
            "extensions.gen_random_bytes(32)",
            "create table if not exists private.student_access_network_rate_buckets",
            "origin_hash bytea not null",
            "primary key (origin_hash, operation, window_started_at)",
            "create or replace function private.student_access_network_rate_limit_v1(",
            "p_network_origin text",
            "p_operation text",
            "extensions.hmac(",
            "convert_to('fitnexus-student-origin-v1:' || v_origin, 'UTF8')",
            "create or replace function public.check_student_access_network_rate_limit_v1(",
            "security invoker",
            "grant execute on function public.check_student_access_network_rate_limit_v1(text,text)",
            "to service_role",
            "network_rate_limit_burst",
            "STUDENT_NETWORK_RATE_LIMITED",
            "network_rate_limit_burst_signals_60m",
        ),
        FAILURE_CLASSES[0],
    )

    # The limit is selected internally by operation. No RPC signature or body may let the
    # caller provide a numeric limit and silently weaken the boundary.
    if "p_limit" in lower or "limit_per_minute integer" in lower:
        fail(f"{FAILURE_CLASSES[2]} caller-supplied rate limit appeared")
    for operation, threshold in THRESHOLDS.items():
        fragment = f"when '{operation}' then {threshold}"
        if fragment not in lower:
            fail(f"{FAILURE_CLASSES[2]} missing DB-owned threshold: {fragment}")

    # Raw network origin is transient only. Persisted bucket schema must contain a digest,
    # and no IP/origin text column is permitted in the bucket table.
    bucket_start = lower.index("create table if not exists private.student_access_network_rate_buckets")
    bucket_end = lower.index(");", bucket_start) + 2
    bucket_ddl = lower[bucket_start:bucket_end]
    if "origin_hash bytea" not in bucket_ddl:
        fail(f"{FAILURE_CLASSES[1]} bucket is not keyed by digest")
    forbidden_bucket_columns = ("client_ip", "ip_address", "network_origin text", "origin text")
    present_bucket = [item for item in forbidden_bucket_columns if item in bucket_ddl]
    if present_bucket:
        fail(f"{FAILURE_CLASSES[1]} raw origin persistence appeared: {present_bucket}")

    if "insert into private.student_access_network_rate_buckets" not in lower:
        fail("network bucket persistence disappeared")
    if "v_origin_hash" not in lower:
        fail("HMAC digest is not used as bucket authority")
    if "v_origin," in lower and "insert into private.student_access_network_rate_buckets" in lower:
        # This deliberately catches the common accidental replacement of the digest with
        # a normalized raw origin in the persistence statement.
        insert_tail = lower[lower.index("insert into private.student_access_network_rate_buckets"):]
        values_end = insert_tail.find("on conflict")
        persisted = insert_tail[:values_end]
        if "v_origin," in persisted or "v_origin)" in persisted:
            fail(f"{FAILURE_CLASSES[1]} raw normalized origin is persisted")

    # The pepper must be generated only by remote DDL and inaccessible as a direct service
    # role object. Never hard-code a key-shaped literal in source.
    require(
        migration,
        (
            "revoke all on private.student_access_network_origin_secret",
            "from public, anon, authenticated, service_role",
            "revoke all on private.student_access_network_rate_buckets",
        ),
        FAILURE_CLASSES[3],
    )
    forbidden_secret_fragments = ("sb_secret_", "service_role_key=", "supabase_service_role_key")
    leaked_secret = [item for item in forbidden_secret_fragments if item in lower]
    if leaked_secret:
        fail(f"{FAILURE_CLASSES[3]} backend secret material appeared in migration source")

    runtime = authority.get("runtime_boundary", {})
    required_false = (
        "edge_gateway_uses_network_rate_limit",
        "invalid_token_network_origin_rate_limit_verified_live",
        "flutter_uses_edge_gateway",
        "direct_anon_v2_rpc_execute_revoked",
        "edge_alert_delivery_verified",
        "rollback_verified",
    )
    for key in required_false:
        if runtime.get(key) is not False:
            fail(f"Stage 27 repo-only DDL self-promoted runtime state: {key}")
    if runtime.get("direct_v2_rpc_path_active") is not True:
        fail("direct student RPC path was removed before Edge/Flutter cutover")

    # Until the migration and Edge integration are live, Stage 24 must still state the
    # unresolved invalid-token/network-origin boundary.
    blind_spot = abuse.get("known_external_boundary", {}).get("blind_spot", "").lower()
    if "invalid-token" not in blind_spot or "client ip" not in blind_spot:
        fail("Stage 24 blind spot was removed before live rate-limit verification")

    direct_calls: dict[str, list[str]] = {rpc: [] for rpc in DIRECT_V2_RPCS}
    for path in APP.rglob("*.dart"):
        text = path.read_text(encoding="utf-8")
        for rpc in DIRECT_V2_RPCS:
            if f".rpc(\n      '{rpc}'" in text or f".rpc('{rpc}'" in text:
                direct_calls[rpc].append(path.relative_to(ROOT).as_posix())
    missing = [rpc for rpc, paths in direct_calls.items() if not paths]
    if missing:
        fail(f"partial Flutter cutover detected before Stage 27 runtime integration: {missing}")

    gates = external.get("gates", {})
    for gate_name in ("incident_response", "production_deployment"):
        gate = gates.get(gate_name, {})
        if gate.get("placeholder_only") is not True:
            fail(f"{gate_name} was promoted without dedicated evidence")
        if gate.get("evidence_ref") is not None or gate.get("evidence_digest") is not None:
            fail(f"{gate_name} contains fabricated evidence")

    launch = authority.get("launch_authority", {})
    for key, value in launch.items():
        if value is not False:
            fail(f"Stage 27 DDL gained launch authority: {key}")

    preconditions = authority.get("promotion_preconditions")
    if not isinstance(preconditions, list) or len(preconditions) < 10:
        fail("Stage 27 promotion preconditions are incomplete")

    print("STUDENT_ACCESS_NETWORK_RATE_LIMIT_GUARD=PASS")
    print("CURRENT_STATE=REPO_ONLY_DDL_NOT_APPLIED")
    print("TRUSTED_ORIGIN_SOURCE=cf-connecting-ip")
    print("ROUTE_THRESHOLDS=120,30,120,90,30")
    print("RAW_NETWORK_ORIGIN_PERSISTENCE=DENIED")
    print("ORIGIN_DIGEST=HMAC_SHA256")
    print("CALLER_LIMIT_OVERRIDE=DENIED")
    print("PUBLIC_BRIDGE=SECURITY_INVOKER_SERVICE_ROLE_ONLY")
    print("DIRECT_V2_RPC_PATHS=5")
    print("EDGE_RATE_LIMIT_INTEGRATION=NOT_DEPLOYED")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
