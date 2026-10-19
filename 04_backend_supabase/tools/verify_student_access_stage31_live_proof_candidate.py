from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app"
AUTHORITY = BACKEND / "student_access_client_edge_runtime_proof_authority.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
CUTOVER = BACKEND / "student_access_client_cutover_authority.json"
INCIDENT = BACKEND / "stage31_live_proof_guard_incident_authority.json"
CONTRACT = APP / "lib" / "features" / "student" / "student_access_transport_contract.dart"
TRANSPORT = APP / "lib" / "features" / "student" / "student_access_transport.dart"
TEST = APP / "test" / "student_access_stage31_live_edge_proof_test.dart"

STATE = "CLIENT_EDGE_RUNTIME_PROOF_FIXTURE_REMOTE_LIVE_PROOF_PENDING_DIRECT_MODE"
FIXTURE_NAME = "stage31_client_edge_runtime_fixture"
FIXTURE_VERSION = "20260821113205"
GUARD_SENTINEL_CLASS = "BGF-STAGE31-PROOF-GUARD-SENTINEL-SELF-MATCH-222"
FAILURE_CLASSES = [
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-FIXTURE-216",
    "BGF-STAGE31-VERIFICATION-SEAM-PRODUCTION-LEAK-217",
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-PROOF-PREMATURE-218",
    "BGF-STAGE31-CLIENT-EDGE-RUNTIME-PROOF-REEXECUTION-219",
]
ROUTES = [
    "get_workout",
    "start_workout",
    "set_completion",
    "get_feedback_context",
    "submit_feedback",
]
SECURITY_SENTINELS = (
    "token_hash",
    "authorization",
    "apikey",
    "network_origin",
    "raw_network_origin",
    "origin_hash",
    "service_role",
    "cf-connecting-ip",
    "x-forwarded-for",
    "x-real-ip",
)


def fail(message: str) -> None:
    raise SystemExit("STAGE31_CLIENT_EDGE_LIVE_PROOF_CANDIDATE_GUARD=FAIL\n" + message)


def text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def data(path: Path) -> dict:
    try:
        value = json.loads(text(path))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require(mapping: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            fail(f"{label} drift: {key}")


def main() -> None:
    authority = data(AUTHORITY)
    ledger = data(LEDGER)
    cutover = data(CUTOVER)
    incident = data(INCIDENT)
    contract = text(CONTRACT)
    transport = text(TRANSPORT)
    proof = text(TEST)

    require(
        incident,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "failure_class": GUARD_SENTINEL_CLASS,
        },
        "Stage 31 sentinel-guard incident authority",
    )
    if incident.get("incident", {}).get("workflow_run_id") != 32478699265:
        fail("sentinel-guard incident workflow receipt drifted")
    prevention = incident.get("permanent_prevention", {})
    for key in (
        "forbidden_response_sentinel_is_allowed_in_test_assertion_set",
        "service_role_key_or_secret_configuration_remains_forbidden",
        "direct_rpc_and_direct_functions_invoke_remain_forbidden_in_proof",
        "raw_64_hex_bearer_literal_remains_forbidden",
        "guard_must_validate_semantic_credential_patterns_not_the_sentinel_label_alone",
    ):
        if prevention.get(key) is not True:
            fail(f"{GUARD_SENTINEL_CLASS} prevention invariant missing: {key}")
    if incident.get("incident", {}).get("live_proof_executed") is not False:
        fail("sentinel-guard incident incorrectly claims live proof execution")

    require(
        authority,
        {
            "schema_version": 1,
            "project_ref": "mceukeondizkwlpfxzgf",
            "current_state": STATE,
            "failure_classes": FAILURE_CLASSES,
            "fixture_remote_reconciliation_failure_class": "BGF-STAGE31-FIXTURE-REMOTE-RECONCILIATION-221",
        },
        "Stage 31 live-proof authority",
    )

    fixture = authority.get("fixture", {})
    require(
        fixture,
        {
            "migration_name": FIXTURE_NAME,
            "migration_ledger_state": "remote_reconciled",
            "remote_applied": True,
            "remote_version": FIXTURE_VERSION,
            "synthetic_only": True,
            "cleanup_required_after_proof": True,
        },
        "Stage 31 fixture",
    )
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }
    if remote.get(FIXTURE_NAME) != FIXTURE_VERSION:
        fail("Stage 31 fixture remote version is not reconciled in migration ledger")
    repo_only = [
        row for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    ]
    if repo_only:
        fail("live proof candidate refuses a repo_only migration divergence")

    production = authority.get("production_boundary", {})
    require(
        production,
        {
            "active_transport": "directRpc",
            "resolved_transport": "directRpc",
            "edge_gateway_selected": False,
            "flutter_uses_edge_gateway_in_production": False,
            "direct_v2_rpc_path_active": True,
            "direct_anon_v2_rpc_execute_revoked": False,
            "explicit_rollback_requested": False,
            "explicit_rollback_authorized": False,
            "automatic_edge_to_direct_fallback": False,
            "client_cutover_verified": False,
            "behavioral_transport_change": False,
        },
        "production boundary",
    )
    cutover_transport = cutover.get("transport_contract", {})
    for key, expected in {
        "active_mode": "directRpc",
        "resolved_mode": "directRpc",
        "edge_gateway_selected": False,
        "automatic_edge_to_direct_fallback": False,
        "explicit_rollback_requested": False,
        "explicit_rollback_authorized": False,
        "direct_rpc_execute_revoked": False,
        "client_cutover_verified": False,
    }.items():
        if cutover_transport.get(key) != expected:
            fail(f"cutover production boundary drifted before live proof: {key}")

    for fragment in (
        "StudentAccessTransportMode.directRpc;",
        "static const bool edgeGatewaySelected = false;",
        "static const bool automaticEdgeToDirectFallback = false;",
        "static const bool explicitRollbackRequested = false;",
        "static const bool explicitRollbackAuthorized = false;",
        "static const bool directRpcExecuteRevoked = false;",
        "static const bool clientCutoverVerified = false;",
    ):
        if fragment not in contract:
            fail(f"production transport contract drifted before live proof: {fragment}")
    for fragment in (
        "factory StudentAccessTransport.forVerification({",
        "configuredModeOverride: configuredMode",
        "return _client.rpc(directRpc, params: directParams);",
        "return _invokeEdge(action: action, payload: edgePayload);",
        "_client.functions.invoke(",
    ):
        if fragment not in transport:
            fail(f"single transport runtime drifted before live proof: {fragment}")

    required_test_fragments = (
        "StudentAccessTransport.forVerification(",
        "configuredMode: StudentAccessTransportMode.edgeGateway",
        "STAGE31_LIVE_PROOF_ENABLED",
        "STAGE31_SYNTHETIC_TOKEN",
        "STAGE31_SUPABASE_URL",
        "STAGE31_SUPABASE_PUBLISHABLE_KEY",
        "HttpOverrides.global = null;",
        "Stage31 Synthetic Student",
        "Stage31 Synthetic Plan",
        "Stage31 Synthetic Exercise",
        "31000000000000000000000000000001",
        "31000000000000000000000000000002",
        "31000000000000000000000000000003",
        "Stage31 live proof executes only in the sealed one-shot workflow.",
    )
    for fragment in required_test_fragments:
        if fragment not in proof:
            fail(f"Stage 31 live proof source incomplete: {fragment}")
    for sentinel in SECURITY_SENTINELS:
        if f"'{sentinel}'" not in proof:
            fail(f"{GUARD_SENTINEL_CLASS} response leak sentinel disappeared: {sentinel}")
    for action in ROUTES:
        if proof.count(f"action: '{action}'") != 1:
            fail(f"Stage 31 live proof must route {action} through transport exactly once")
    if proof.count("transport.invoke(") != 5:
        fail("Stage 31 live proof must enter the single transport exactly five times")

    # Sentinel labels such as service_role and cf-connecting-ip are intentionally
    # present in the response-leak assertion set. Reject privileged configuration
    # and transport bypasses semantically rather than banning those labels raw.
    for forbidden in (
        ".rpc(",
        "functions.invoke(",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEY",
        "serviceRoleKey",
        "service_role_key",
        "Authorization': 'Bearer",
        'Authorization": "Bearer',
    ):
        if forbidden in proof:
            fail(f"Stage 31 live proof bypassed the client boundary or embedded privileged material: {forbidden}")
    if re.search(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", proof):
        fail("Stage 31 live proof contains a bearer-looking 64-hex literal")

    runtime = authority.get("runtime_proof", {})
    if runtime.get("workflow_run_id") is not None or runtime.get("result") is not None:
        fail(f"{FAILURE_CLASSES[3]} live proof already has a receipt")
    for key in (
        "flutter_transport_edge_path_verified",
        "get_workout_verified",
        "start_workout_verified",
        "set_completion_verified",
        "get_feedback_context_verified",
        "submit_feedback_verified",
        "all_five_routes_verified",
        "raw_token_returned",
        "raw_network_origin_returned",
        "real_customer_data_used",
        "real_customer_data_mutated",
        "proof_reexecution_allowed",
        "cleanup_completed",
    ):
        if runtime.get(key) is not False:
            fail(f"{FAILURE_CLASSES[2]} live proof self-attested before execution: {key}")

    next_stage = authority.get("next_stage", {})
    if next_stage.get("name") != "PREPARE_STAGE31_CLIENT_EDGE_RUNTIME_LIVE_PROOF":
        fail("Stage 31 authority is not at the live-proof preparation frontier")
    if next_stage.get("requires_exact_pr_and_head_seal_before_first_execution") is not True:
        fail(f"{FAILURE_CLASSES[3]} exact PR/head seal interlock disappeared")
    if next_stage.get("requires_one_shot_workflow") is not True:
        fail(f"{FAILURE_CLASSES[3]} one-shot workflow interlock disappeared")
    if next_stage.get("requires_fixture_remote_applied") is not True:
        fail("live proof lost remote fixture prerequisite")
    if next_stage.get("may_select_edge_gateway_now") is not False:
        fail("Edge production selection was prematurely authorized")
    if next_stage.get("may_revoke_direct_rpc_execute_now") is not False:
        fail("direct RPC revocation was prematurely authorized")

    print("STAGE31_CLIENT_EDGE_LIVE_PROOF_CANDIDATE_GUARD=PASS")
    print(f"CURRENT_STATE={STATE}")
    print(f"FIXTURE_REMOTE_VERSION={FIXTURE_VERSION}")
    print(f"SENTINEL_GUARD_PREVENTION={GUARD_SENTINEL_CLASS}")
    print("FLUTTER_TRANSPORT_PROOF_SOURCE=READY")
    print("ROUTES_IN_PROOF=5")
    print("DIRECT_RPC_FROM_PROOF=DENIED")
    print("PRODUCTION_ACTIVE_TRANSPORT=directRpc")
    print("EDGE_SELECTION=false")
    print("DIRECT_RPC_PRIVILEGE_REVOCATION=false")
    print("LIVE_PROOF_EXECUTED=false")
    print("EXACT_PR_HEAD_SEAL=REQUIRED_BEFORE_EXECUTION")
    print("LAUNCH_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
