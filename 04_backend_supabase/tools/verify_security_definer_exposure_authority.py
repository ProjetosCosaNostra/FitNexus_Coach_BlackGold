from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "security_definer_exposure_authority.json"
IDENTITY = BACKEND / "project_identity.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
MIGRATIONS = BACKEND / "migrations"
FAILURE_CLASS = "BGF-SECURITY-DEFINER-EXPOSURE-DRIFT-159"
STAGE33_MIGRATION = "stage33_direct_rpc_revocation_and_post_revocation_fixture"
STAGE86_TERMS_MIGRATION = "stage85_terms_acceptance_registry_ledger"
STAGE86_TERMS_MIGRATION_FILE = MIGRATIONS / "20260826180000_stage85_terms_acceptance_registry_ledger.sql"

DEFINITION_RE = re.compile(
    r"create\s+(?:or\s+replace\s+)?function\s+public\.(?P<name>[a-z0-9_]+)\s*\(.*?\)\s*returns.*?\bas\s+\$\$",
    re.IGNORECASE | re.DOTALL,
)
PRIVILEGE_RE = re.compile(
    r"(?P<action>grant|revoke)\s+(?:all|execute)\s+on\s+function\s+public\."
    r"(?P<name>[a-z0-9_]+)\s*\([^;]*?\)\s+(?:to|from)\s+(?P<roles>[^;]+);",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class FunctionState:
    security_definer: bool = False
    created: bool = False
    execute_roles: set[str] = field(default_factory=set)


def fail(message: str) -> None:
    raise SystemExit(f"SECURITY_DEFINER_EXPOSURE_AUTHORITY_GUARD=FAIL\n{message}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read {path.relative_to(ROOT)}: {type(exc).__name__}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def normalize_roles(raw: str) -> list[str]:
    return [item.strip().lower().strip('"') for item in raw.split(",") if item.strip()]


def replay_repository_privileges() -> dict[str, FunctionState]:
    states: dict[str, FunctionState] = {}
    for path in sorted(MIGRATIONS.glob("*.sql")):
        source = path.read_text(encoding="utf-8")
        events: list[tuple[int, str, re.Match[str]]] = []
        events.extend((m.start(), "definition", m) for m in DEFINITION_RE.finditer(source))
        events.extend((m.start(), "privilege", m) for m in PRIVILEGE_RE.finditer(source))
        for _position, kind, match in sorted(events, key=lambda item: item[0]):
            name = match.group("name").lower()
            state = states.setdefault(name, FunctionState())
            if kind == "definition":
                if not state.created:
                    state.execute_roles.add("public")
                    state.created = True
                state.security_definer = "security definer" in match.group(0).lower()
                continue
            roles = normalize_roles(match.group("roles"))
            if match.group("action").lower() == "grant":
                state.execute_roles.update(roles)
            else:
                state.execute_roles.difference_update(roles)
    return states


def effective_external_roles(state: FunctionState) -> set[str]:
    roles: set[str] = set()
    if "public" in state.execute_roles:
        roles.update({"anon", "authenticated"})
    if "anon" in state.execute_roles:
        roles.add("anon")
    if "authenticated" in state.execute_roles:
        roles.add("authenticated")
    return roles


def parse_exposures(rows: object, label: str) -> dict[str, set[str]]:
    if not isinstance(rows, list) or not rows:
        fail(f"{label} must be a non-empty array")
    result: dict[str, set[str]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            fail(f"{label} #{index} must be an object")
        name = str(row.get("function", "")).strip().lower()
        args = str(row.get("identity_arguments", "")).strip().lower()
        boundary = str(row.get("boundary", "")).strip()
        reason = str(row.get("reason", "")).strip()
        roles_raw = row.get("roles")
        if not re.fullmatch(r"[a-z0-9_]+", name):
            fail(f"{label} #{index} invalid function name")
        if not args or not boundary or not reason:
            fail(f"{label} {name} missing arguments/boundary/reason")
        if not isinstance(roles_raw, list) or not roles_raw:
            fail(f"{label} {name} missing roles")
        roles = {str(role).strip().lower() for role in roles_raw}
        if not roles <= {"anon", "authenticated"}:
            fail(f"{label} {name} unsupported role")
        if name in result:
            fail(f"duplicate {label} function: {name}")
        result[name] = roles
    return result


def main() -> None:
    authority = load(AUTHORITY)
    identity = load(IDENTITY)
    ledger = load(LEDGER)
    if authority.get("schema_version") != 2:
        fail("schema_version must remain 2 for Stage33-compatible lifecycle authority")
    if authority.get("failure_class") != FAILURE_CLASS:
        fail("unexpected failure_class")
    if authority.get("project_ref") != identity.get("project_ref"):
        fail("authority project_ref mismatch")

    remote_expected = parse_exposures(
        authority.get("remote_pre_revocation_approved_exposures"),
        "remote_pre_revocation_approved_exposures",
    )
    repo_expected = parse_exposures(
        authority.get("repository_target_approved_exposures"),
        "repository_target_approved_exposures",
    )

    student_targets = {
        "get_student_feedback_context_v2",
        "get_student_workout_v2",
        "set_student_exercise_completion_v2",
        "start_student_workout_v2",
        "submit_student_workout_feedback_v2",
    }
    if set(remote_expected) != student_targets | {"issue_student_access_token_v2"}:
        fail("remote pre-revocation exposure set drifted")
    for name in student_targets:
        if remote_expected.get(name) != {"anon", "authenticated"}:
            fail(f"remote pre-revocation roles drifted: {name}")
    if remote_expected.get("issue_student_access_token_v2") != {"authenticated"}:
        fail("issue_student_access_token_v2 remote authority drifted")

    transition = authority.get("stage33_transition", {})
    state = authority.get("current_state")
    if state not in {
        "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION",
        "STAGE33_REVOCATION_REMOTE_RECONCILED_POST_REVOCATION",
    }:
        fail("unsupported Stage33 exposure lifecycle state")
    expected_ledger_state = (
        "repo_only" if state == "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION"
        else "remote_reconciled"
    )
    if transition.get("migration_name") != STAGE33_MIGRATION:
        fail("Stage33 transition migration name drifted")
    if transition.get("migration_ledger_state") != expected_ledger_state:
        fail("Stage33 transition ledger state drifted")
    if transition.get("target_student_route_count") != 5:
        fail("Stage33 target route count drifted")
    if transition.get("service_role_preserved_for_edge_backend") is not True:
        fail("service_role preservation missing")
    if transition.get("issue_student_access_token_v2_preserved") is not True:
        fail("token issuance preservation missing")

    repo_only = {
        row.get("name") for row in ledger.get("declared_divergences", [])
        if isinstance(row, dict) and row.get("direction") == "repo_only"
    }
    remote = {
        row.get("name"): row.get("version")
        for row in ledger.get("remote_migrations", []) if isinstance(row, dict)
    }
    if state == "STAGE33_REVOCATION_REPO_ONLY_REMOTE_PRE_REVOCATION":
        if STAGE33_MIGRATION not in repo_only:
            fail("Stage33 migration must remain repo-only in pre-revocation state")
        if STAGE33_MIGRATION in remote:
            fail("Stage33 migration unexpectedly remote in repo-only state")
        if transition.get("remote_applied") is not False or transition.get("remote_version") is not None:
            fail("repo-only transition falsely claims remote application")
    else:
        if STAGE33_MIGRATION in repo_only:
            fail("remote-reconciled transition still declares repo-only Stage33 migration")
        if remote.get(STAGE33_MIGRATION) != transition.get("remote_version"):
            fail("remote-reconciled Stage33 version mismatch")
        if transition.get("remote_applied") is not True:
            fail("remote-reconciled transition missing remote_applied")

    stage86 = authority.get("stage86_repository_target_transition")
    if STAGE86_TERMS_MIGRATION in repo_only:
        if not isinstance(stage86, dict):
            fail("Stage86 repo-only Terms migration requires explicit exposure transition authority")
        if stage86.get("baseline_main_sha") != "3d6d14a659611594081b8a22b0ae6c483459de48":
            fail("Stage86 exposure baseline main drift")
        if stage86.get("migration_name") != STAGE86_TERMS_MIGRATION:
            fail("Stage86 exposure migration name drift")
        if stage86.get("migration_file") != str(STAGE86_TERMS_MIGRATION_FILE.relative_to(ROOT)).replace("\\", "/"):
            fail("Stage86 exposure migration path drift")
        if stage86.get("migration_blob_sha") != git_blob_sha(STAGE86_TERMS_MIGRATION_FILE):
            fail("Stage86 exposure migration blob drift")
        if stage86.get("migration_blob_sha") != "a9a77ebbf61f464e5549f338362cdd3a59df8df1":
            fail("Stage86 exposure exact migration pin drift")
        if stage86.get("migration_ledger_state") != "repo_only":
            fail("Stage86 Terms migration exposure must remain repo_only")
        if stage86.get("remote_applied") is not False or stage86.get("remote_version") is not None:
            fail("Stage86 exposure authority falsely claims remote application")
        if STAGE86_TERMS_MIGRATION in remote:
            fail("Stage86 Terms migration unexpectedly present in remote baseline")
        if stage86.get("remote_current_new_terms_exposure_count") != 0:
            fail("Stage86 new Terms exposure must remain remote-zero")
        if stage86.get("terms_registry_seeded") is not False or stage86.get("acceptance_seeded") is not False:
            fail("Stage86 exposure authority cannot claim Terms/acceptance data")
        if stage86.get("legal_terms_gate_promoted") is not False:
            fail("Stage86 exposure authority cannot promote legal Terms gate")

        expected_repo = {
            "issue_student_access_token_v2": {"authenticated"},
            "get_current_terms_v1": {"anon", "authenticated"},
            "accept_current_terms_v1": {"authenticated"},
            "get_my_terms_acceptance_gate_v1": {"authenticated"},
        }
        if repo_expected != expected_repo:
            fail("Stage86 repository target exposure allowlist drift")
        if stage86.get("repository_target_new_terms_function_count") != 3:
            fail("Stage86 new Terms function exposure count drift")
        if stage86.get("repository_target_total_security_definer_exposure_count") != 4:
            fail("Stage86 total repository exposure count drift")
        if stage86.get("repository_target_anon_exposure_count") != 1:
            fail("Stage86 repository anon exposure count drift")
        if stage86.get("repository_target_authenticated_exposure_count") != 4:
            fail("Stage86 repository authenticated exposure count drift")
    else:
        expected_repo = {"issue_student_access_token_v2": {"authenticated"}}
        if repo_expected != expected_repo:
            fail("repository target exposure advanced without declared repo-only Stage86 migration")

    states = replay_repository_privileges()
    actual: dict[str, set[str]] = {}
    for name, function_state in states.items():
        if not function_state.security_definer:
            continue
        roles = effective_external_roles(function_state)
        if roles:
            actual[name] = roles
    if actual != repo_expected:
        missing = sorted(set(repo_expected) - set(actual))
        unexpected = sorted(set(actual) - set(repo_expected))
        role_drift = sorted(
            name for name in set(actual) & set(repo_expected)
            if actual[name] != repo_expected[name]
        )
        fail(
            "repository target exposure drift: "
            f"missing={missing};unexpected={unexpected};role_drift={role_drift}"
        )

    print("SECURITY_DEFINER_EXPOSURE_AUTHORITY_GUARD=PASS")
    print(f"LIFECYCLE_STATE={state}")
    print("REMOTE_PRE_REVOCATION_EXPOSURES=6")
    print("REMOTE_PRE_REVOCATION_ANON_EXPOSURES=5")
    print("REMOTE_PRE_REVOCATION_AUTH_EXPOSURES=6")
    print(f"REPOSITORY_TARGET_EXPOSURES={len(repo_expected)}")
    print(f"REPOSITORY_TARGET_ANON_EXPOSURES={sum('anon' in roles for roles in repo_expected.values())}")
    print(f"REPOSITORY_TARGET_AUTH_EXPOSURES={sum('authenticated' in roles for roles in repo_expected.values())}")
    print("STAGE86_TERMS_REMOTE_EXPOSURES=0")
    print("UNAPPROVED_EXPOSURES=0")
    print("PUBLIC_DEFAULT_EXECUTE_DRIFT=0")


if __name__ == "__main__":
    main()
