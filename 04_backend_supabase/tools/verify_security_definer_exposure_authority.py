from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "04_backend_supabase" / "security_definer_exposure_authority.json"
IDENTITY = ROOT / "04_backend_supabase" / "project_identity.json"
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"

FAILURE_CLASS = "BGF-SECURITY-DEFINER-EXPOSURE-DRIFT-159"

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
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def normalize_roles(raw: str) -> list[str]:
    result: list[str] = []
    for item in raw.split(","):
        role = item.strip().lower().strip('"')
        if role:
            result.append(role)
    return result


def replay_repository_privileges() -> dict[str, FunctionState]:
    states: dict[str, FunctionState] = {}

    for path in sorted(MIGRATIONS.glob("*.sql")):
        text = path.read_text(encoding="utf-8")
        events: list[tuple[int, str, re.Match[str]]] = []
        events.extend((match.start(), "definition", match) for match in DEFINITION_RE.finditer(text))
        events.extend((match.start(), "privilege", match) for match in PRIVILEGE_RE.finditer(text))

        for _position, kind, match in sorted(events, key=lambda item: item[0]):
            name = match.group("name").lower()
            state = states.setdefault(name, FunctionState())

            if kind == "definition":
                if not state.created:
                    # PostgreSQL grants EXECUTE to PUBLIC on a newly created function unless revoked.
                    state.execute_roles.add("public")
                    state.created = True
                header = match.group(0).lower()
                state.security_definer = "security definer" in header
                continue

            action = match.group("action").lower()
            roles = normalize_roles(match.group("roles"))
            if action == "grant":
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


def main() -> None:
    authority = load(AUTHORITY)
    identity = load(IDENTITY)

    if authority.get("schema_version") != 1:
        fail("schema_version must be 1")
    if authority.get("failure_class") != FAILURE_CLASS:
        fail("unexpected failure_class")
    if authority.get("project_ref") != identity.get("project_ref"):
        fail("authority project_ref does not match project_identity.json")

    rows = authority.get("approved_exposures")
    if not isinstance(rows, list) or not rows:
        fail("approved_exposures must be a non-empty array")

    approved: dict[str, set[str]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            fail(f"approved exposure #{index} must be an object")
        name = str(row.get("function", "")).strip().lower()
        args = str(row.get("identity_arguments", "")).strip().lower()
        boundary = str(row.get("boundary", "")).strip()
        reason = str(row.get("reason", "")).strip()
        roles_raw = row.get("roles")
        if not re.fullmatch(r"[a-z0-9_]+", name):
            fail(f"approved exposure #{index} has invalid function name")
        if name in approved:
            fail(f"duplicate approved exposure function: {name}")
        if not args or not boundary or not reason:
            fail(f"approved exposure {name} is missing identity_arguments/boundary/reason")
        if not isinstance(roles_raw, list) or not roles_raw:
            fail(f"approved exposure {name} must declare roles")
        roles = {str(role).strip().lower() for role in roles_raw}
        if not roles <= {"anon", "authenticated"}:
            fail(f"approved exposure {name} contains unsupported role")
        approved[name] = roles

    expected_names = {
        "get_student_feedback_context_v2",
        "get_student_workout_v2",
        "issue_student_access_token_v2",
        "set_student_exercise_completion_v2",
        "start_student_workout_v2",
        "submit_student_workout_feedback_v2",
    }
    if set(approved) != expected_names:
        fail(
            "approved exposure set must match the live reviewed baseline; got="
            + ",".join(sorted(approved))
        )

    states = replay_repository_privileges()
    exposed: dict[str, set[str]] = {}
    for name, state in states.items():
        if not state.security_definer:
            continue
        roles = effective_external_roles(state)
        if roles:
            exposed[name] = roles

    unexpected = sorted(set(exposed) - set(approved))
    missing = sorted(set(approved) - set(exposed))
    role_drift = sorted(
        name for name in set(approved) & set(exposed) if approved[name] != exposed[name]
    )

    if unexpected or missing or role_drift:
        details: list[str] = []
        if unexpected:
            details.append("UNAPPROVED_SECURITY_DEFINER_EXPOSURE=" + ",".join(unexpected))
        if missing:
            details.append("APPROVED_EXPOSURE_MISSING=" + ",".join(missing))
        if role_drift:
            details.append(
                "ROLE_DRIFT="
                + ",".join(
                    f"{name}:expected={sorted(approved[name])}:actual={sorted(exposed[name])}"
                    for name in role_drift
                )
            )
        fail(" | ".join(details))

    anon = sorted(name for name, roles in exposed.items() if "anon" in roles)
    authenticated = sorted(
        name for name, roles in exposed.items() if "authenticated" in roles
    )

    print("SECURITY_DEFINER_EXPOSURE_AUTHORITY_GUARD=PASS")
    print(f"APPROVED_EXPOSURES={len(exposed)}")
    print(f"ANON_SECURITY_DEFINER_EXPOSURES={len(anon)}")
    print(f"AUTH_SECURITY_DEFINER_EXPOSURES={len(authenticated)}")
    print("UNAPPROVED_EXPOSURES=0")
    print("PUBLIC_DEFAULT_EXECUTE_DRIFT=0")


if __name__ == "__main__":
    main()
