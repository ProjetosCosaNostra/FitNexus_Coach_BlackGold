from __future__ import annotations

import copy
import json

NAME = "stage52_student_issuance_target_privacy_hardening"
REMOTE_VERSION = "20260824204450"
PROMOTION_BASELINE = "b5f466ef09dd027f10c88d3d13726f3d7c0281ba"
PROMOTION_OBSERVED = "2026-08-24T20:27:07.829322Z"
PROMOTION_SOURCE = "Supabase.list_migrations+Supabase.execute_sql"
FINAL_BASELINE = "a81767e12037fcf45dbf8e8104182f226bded65a"
FINAL_OBSERVED = "2026-08-24T20:45:14.762907Z"
FINAL_SOURCE = "Supabase.list_migrations+Supabase.execute_sql"

PROMOTION_REPO_ONLY = {
    "direction": "repo_only",
    "name": NAME,
    "reason": "Stage52 promotes the green issuance target-privacy operations candidate as an exact versioned migration in the repository first. It must remain repo-only until the promotion PR is green and merged, then be applied exactly once through Supabase.apply_migration. It does not create users, students, organizations, or launch authority.",
    "owner": "BlackGold Forge",
    "related_failure_class": "BGF-STAGE52-CANDIDATE-DIRECT-APPLY-485",
}


def clone(value: dict) -> dict:
    return copy.deepcopy(value)


def remote_map(ledger: dict) -> dict[str, str]:
    return {
        str(row.get("name")): str(row.get("version"))
        for row in ledger.get("remote_migrations", [])
        if isinstance(row, dict)
    }


def divergences(ledger: dict) -> tuple[list[dict], list[dict]]:
    rows = [row for row in ledger.get("declared_divergences", []) if isinstance(row, dict)]
    return (
        [row for row in rows if row.get("direction") == "remote_only"],
        [row for row in rows if row.get("direction") == "repo_only"],
    )


def _version_before_or_equal_stage52(row: object) -> bool:
    if not isinstance(row, dict):
        return False
    version = str(row.get("version", ""))
    return version.isdigit() and len(version) == 14 and version <= REMOTE_VERSION


def _version_before_stage52(row: object) -> bool:
    if not isinstance(row, dict):
        return False
    version = str(row.get("version", ""))
    return version.isdigit() and len(version) == 14 and version < REMOTE_VERSION


def state(ledger: dict) -> str:
    if ledger.get("schema_version") != 1 or ledger.get("project_ref") != "mceukeondizkwlpfxzgf":
        raise ValueError("common ledger identity drift")
    remote_only, repo_only = divergences(ledger)
    if len(remote_only) != 3:
        raise ValueError("historical Stage17 remote-only count drift")
    remote = remote_map(ledger)
    stage52_repo = [row for row in repo_only if row.get("name") == NAME]
    baseline = ledger.get("baseline_main_sha")
    observed = ledger.get("observed_at_utc")
    if baseline == PROMOTION_BASELINE and observed == PROMOTION_OBSERVED:
        if remote.get(NAME) is not None or stage52_repo != [PROMOTION_REPO_ONLY]:
            raise ValueError("Stage52 promotion frontier drift")
        return "promotion"
    if baseline == FINAL_BASELINE and observed == FINAL_OBSERVED:
        if remote.get(NAME) != REMOTE_VERSION or stage52_repo or repo_only:
            raise ValueError("Stage52 final frontier drift")
        return "final"
    if remote.get(NAME) == REMOTE_VERSION and not stage52_repo:
        return "post_final"
    raise ValueError("unknown Stage52 migration frontier")


def to_promotion(ledger: dict) -> dict:
    if state(ledger) == "promotion":
        return clone(ledger)
    projected = clone(ledger)
    projected["baseline_main_sha"] = PROMOTION_BASELINE
    projected["observed_at_utc"] = PROMOTION_OBSERVED
    projected["source"] = PROMOTION_SOURCE
    projected["remote_migrations"] = [
        row for row in projected.get("remote_migrations", [])
        if _version_before_stage52(row)
        and not (isinstance(row, dict) and row.get("name") == NAME)
    ]
    remote_only, _repo_only = divergences(projected)
    projected["declared_divergences"] = remote_only + [clone(PROMOTION_REPO_ONLY)]
    state(projected)
    return projected


def to_final(ledger: dict) -> dict:
    kind = state(ledger)
    if kind == "final":
        return clone(ledger)
    if kind != "post_final":
        raise ValueError(f"cannot project {kind} to final")
    projected = clone(ledger)
    projected["baseline_main_sha"] = FINAL_BASELINE
    projected["observed_at_utc"] = FINAL_OBSERVED
    projected["source"] = FINAL_SOURCE
    projected["remote_migrations"] = [
        row for row in projected.get("remote_migrations", [])
        if _version_before_or_equal_stage52(row)
    ]
    remote_only, _repo_only = divergences(projected)
    projected["declared_divergences"] = remote_only
    state(projected)
    return projected


def json_dump(value: dict) -> str:
    return json.dumps(value, indent=2) + "\n"
