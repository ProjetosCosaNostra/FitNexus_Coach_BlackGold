from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
APP = ROOT / "03_app_flutter" / "fitnexus_app" / "lib"
MIGRATIONS = BACKEND / "migrations"

AUTHORITY = BACKEND / "student_access_network_origin_boundary.json"
STAGE21 = MIGRATIONS / "20260819103700_stage21_student_access_security_boundary.sql"
ABUSE_AUTHORITY = BACKEND / "student_access_abuse_authority.json"
EXTERNAL_GATES = BACKEND / "external_gate_evidence_placeholders.json"
GATEWAY_ENTRYPOINT = BACKEND / "functions" / "student-access-gateway" / "index.ts"

FAILURE_CLASSES = (
    "BGF-NETWORK-ORIGIN-ABUSE-BYPASS-163",
    "BGF-EDGE-ORIGIN-TRUST-164",
    "BGF-STUDENT-ACCESS-PARTIAL-EDGE-CUTOVER-165",
    "BGF-ALERT-DELIVERY-SELF-ATTESTATION-166",
    "BGF-EDGE-RUNTIME-ORIGIN-ASSUMPTION-167",
    "BGF-EDGE-PROBE-DATA-LEAK-168",
    "BGF-EDGE-PROBE-PREMATURE-CUTOVER-169",
)

DIRECT_V2_RPCS = (
    "get_student_workout_v2",
    "start_student_workout_v2",
    "set_student_exercise_completion_v2",
    "get_student_feedback_context_v2",
    "submit_student_workout_feedback_v2",
)


def fail(message: str) -> None:
    raise SystemExit("STUDENT_ACCESS_NETWORK_ORIGIN_BOUNDARY_GUARD=FAIL\n" + message)


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
    missing = [fragment for fragment in fragments if fragment.lower() not in text.lower()]
    if missing:
        fail(f"{failure_class} missing invariants: {missing}")


def main() -> None:
    authority = read_json(AUTHORITY)
    stage21 = read_text(STAGE21).lower()
    abuse = read_json(ABUSE_AUTHORITY)
    external = read_json(EXTERNAL_GATES)
    gateway = read_text(GATEWAY_ENTRYPOINT)
    gateway_lower = gateway.lower()

    if authority.get("schema_version") != 2:
        fail("Stage 26 authority schema_version must remain 2")
    if authority.get("project_ref") != "mceukeondizkwlpfxzgf":
        fail("wrong Supabase project authority")
    if authority.get("failure_classes") != list(FAILURE_CLASSES):
        fail("failure-class authority drifted")

    state = authority.get("current_state")
    if state != "ORIGIN_PROBE_REPOSITORY_READY_NOT_DEPLOYED":
        fail(
            f"{FAILURE_CLASSES[6]} Stage 26 probe state changed without runtime evidence: {state!r}"
        )

    runtime = authority.get("observed_runtime", {})
    if runtime.get("edge_function_name") != "student-access-gateway":
        fail(f"{FAILURE_CLASSES[2]} gateway name drifted")
    if runtime.get("edge_function_deployed") is not False:
        fail(f"{FAILURE_CLASSES[6]} repository-only probe may not self-attest deployment")
    if runtime.get("observed_edge_function_count") != 0:
        fail(f"{FAILURE_CLASSES[6]} runtime count was changed before a new live observation")
    if runtime.get("source") != "Supabase.list_edge_functions":
        fail(f"{FAILURE_CLASSES[6]} runtime evidence source drifted")
    if runtime.get("runtime_origin_candidate_verified") is not False:
        fail(f"{FAILURE_CLASSES[4]} network-origin candidate was self-attested")
    if runtime.get("runtime_origin_candidate") is not None:
        fail(f"{FAILURE_CLASSES[4]} network-origin authority assigned before probe")
    if runtime.get("probe_repository_entrypoint_present") is not True:
        fail(f"{FAILURE_CLASSES[6]} probe repository state is incomplete")

    probe = authority.get("probe_contract", {})
    expected_probe = {
        "mode": "origin_probe_not_student_gateway_cutover",
        "allowed_method": "GET",
        "candidate_header": "cf-connecting-ip",
        "returns_raw_ip": False,
        "logs_raw_ip": False,
        "reads_request_body": False,
        "forwards_student_rpc": False,
        "accepts_client_forwarded_header_as_authority": False,
        "launch_gate_authority": False,
    }
    for key, expected in expected_probe.items():
        if probe.get(key) != expected:
            fail(f"{FAILURE_CLASSES[4]} probe contract drift for {key}: {probe.get(key)!r}")

    current = authority.get("current_client_boundary", {})
    if current.get("direct_v2_rpc_calls") != list(DIRECT_V2_RPCS):
        fail(f"{FAILURE_CLASSES[2]} direct-RPC inventory drifted")
    if current.get("anonymous_v2_rpc_execute_required_by_current_client") is not True:
        fail(f"{FAILURE_CLASSES[2]} current client privilege semantics were self-promoted")
    if current.get("network_origin_rate_limit_for_invalid_token") is not False:
        fail(f"{FAILURE_CLASSES[0]} network-origin protection was self-attested")
    if current.get("edge_alert_delivery_verified") is not False:
        fail(f"{FAILURE_CLASSES[3]} alert delivery was self-attested")

    target = authority.get("target_cutover_invariants", {})
    required_true = (
        "single_student_gateway",
        "network_origin_must_come_from_trusted_runtime_metadata",
        "client_supplied_forwarded_headers_must_not_be_trusted",
        "invalid_token_attempts_rate_limited_by_network_origin_and_route",
        "valid_token_database_rate_limits_remain_active",
        "raw_possession_token_logging_forbidden",
        "arbitrary_request_payload_logging_forbidden",
        "direct_anon_v2_rpc_execute_revoked_after_verified_cutover",
        "client_direct_rpc_fallback_forbidden_after_verified_cutover",
        "alert_delivery_requires_real_runtime_receipt",
        "rollback_requires_real_runtime_receipt",
    )
    missing_targets = [key for key in required_true if target.get(key) is not True]
    if missing_targets:
        fail(f"target cutover invariants weakened: {missing_targets}")

    launch = authority.get("launch_authority", {})
    for key in (
        "can_promote_incident_response_gate",
        "can_promote_production_deployment_gate",
        "can_enable_paid_ads",
        "current_state_is_security_readiness",
    ):
        if launch.get(key) is not False:
            fail(f"{FAILURE_CLASSES[3]} {key} must remain false")

    # Stage 24 must continue to state the remaining network-origin boundary.
    blind_spot = abuse.get("known_external_boundary", {}).get("blind_spot", "").lower()
    if "invalid-token" not in blind_spot or "client ip" not in blind_spot:
        fail(f"{FAILURE_CLASSES[0]} Stage 24 network-origin blind spot disappeared")

    # A probe is not a client cutover. All five Flutter callsites and their temporary anon
    # grants must remain intact until the full gateway has passed runtime verification.
    direct_calls: dict[str, list[str]] = {rpc: [] for rpc in DIRECT_V2_RPCS}
    for path in APP.rglob("*.dart"):
        text = path.read_text(encoding="utf-8")
        for rpc in DIRECT_V2_RPCS:
            if f".rpc(\n      '{rpc}'" in text or f".rpc('{rpc}'" in text:
                direct_calls[rpc].append(path.relative_to(ROOT).as_posix())

    missing_calls = [rpc for rpc, paths in direct_calls.items() if not paths]
    if missing_calls:
        fail(
            f"{FAILURE_CLASSES[2]} partial client cutover during probe stage: {missing_calls}"
        )

    expected_grants = (
        "grant execute on function public.get_student_workout_v2(text) to anon, authenticated;",
        "grant execute on function public.start_student_workout_v2(text,text) to anon, authenticated;",
        "grant execute on function public.set_student_exercise_completion_v2(text,uuid,uuid,boolean,text) to anon, authenticated;",
        "grant execute on function public.get_student_feedback_context_v2(text) to anon, authenticated;",
        "grant execute on function public.submit_student_workout_feedback_v2(text,uuid,integer,integer,integer,text,text,text) to anon, authenticated;",
    )
    missing_grants = [grant for grant in expected_grants if grant not in stage21]
    if missing_grants:
        fail(f"{FAILURE_CLASSES[2]} partial privilege cutover during probe stage: {missing_grants}")

    # Probe source is intentionally inert with respect to student data. It may inspect only
    # header presence and must not consume a body, service-role secret or student RPC.
    require(
        gateway,
        (
            'mode: "origin_probe_not_student_gateway_cutover"',
            'req.headers.get("cf-connecting-ip")',
            'req.headers.get("cf-ray")',
            'x_forwarded_for_present_but_untrusted',
            'x_real_ip_present_but_untrusted',
            'raw_network_origin_returned: false',
            'request_body_read: false',
            'student_rpc_forwarding_enabled: false',
            'launch_gate_authority: false',
            'error: "STUDENT_GATEWAY_NOT_CUTOVER"',
        ),
        FAILURE_CLASSES[4],
    )

    forbidden_probe_fragments = (
        "console.log",
        "console.error",
        "req.json(",
        "req.text(",
        "supabase_service_role_key",
        "/rest/v1/rpc/",
        "get_student_workout_v2",
        "start_student_workout_v2",
        "set_student_exercise_completion_v2",
        "get_student_feedback_context_v2",
        "submit_student_workout_feedback_v2",
    )
    leaked = [fragment for fragment in forbidden_probe_fragments if fragment in gateway_lower]
    if leaked:
        fail(f"{FAILURE_CLASSES[5]} probe contains forbidden data/runtime behavior: {leaked}")

    # The only authoritative-source candidate in this version is cf-connecting-ip. Other
    # forwarded headers may be reported as booleans for spoof testing but never trusted.
    if gateway_lower.count('req.headers.get("cf-connecting-ip")') != 1:
        fail(f"{FAILURE_CLASSES[4]} candidate origin extraction is ambiguous")
    if "network_origin_source_candidate: \"cf-connecting-ip\"" not in gateway_lower:
        fail(f"{FAILURE_CLASSES[4]} probe response does not identify the candidate source")

    gates = external.get("gates", {})
    for gate_name in ("incident_response", "production_deployment"):
        gate = gates.get(gate_name, {})
        if gate.get("placeholder_only") is not True:
            fail(f"{FAILURE_CLASSES[3]} {gate_name} was promoted without runtime evidence")
        if gate.get("evidence_ref") is not None or gate.get("evidence_digest") is not None:
            fail(f"{FAILURE_CLASSES[3]} {gate_name} contains fabricated evidence")

    preconditions = authority.get("promotion_preconditions")
    if not isinstance(preconditions, list) or len(preconditions) < 14:
        fail(f"{FAILURE_CLASSES[2]} cutover preconditions are incomplete")

    print("STUDENT_ACCESS_NETWORK_ORIGIN_BOUNDARY_GUARD=PASS")
    print("CURRENT_EDGE_STATE=ORIGIN_PROBE_REPOSITORY_READY_NOT_DEPLOYED")
    print("OBSERVED_EDGE_FUNCTION_COUNT=0")
    print("DIRECT_V2_RPC_PATHS=5")
    print("PROBE_CANDIDATE=cf-connecting-ip")
    print("PROBE_RAW_IP_RETURN=DENIED")
    print("PROBE_STUDENT_RPC_FORWARDING=DENIED")
    print("INVALID_TOKEN_NETWORK_ORIGIN_RATE_LIMIT=NOT_VERIFIED")
    print("TRUSTED_NETWORK_ORIGIN_EXTRACTION=NOT_VERIFIED")
    print("PARTIAL_CUTOVER=DENIED")
    print("INCIDENT_RESPONSE_GATE_PROMOTION=DENIED")
    print("PRODUCTION_DEPLOYMENT_GATE_PROMOTION=DENIED")


if __name__ == "__main__":
    main()
