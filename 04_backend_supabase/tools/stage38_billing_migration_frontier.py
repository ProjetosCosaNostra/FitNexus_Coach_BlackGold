from __future__ import annotations

import copy
import json

NAME = "stage38_billing_evidence_bound_activation"
REMOTE_VERSION = "20260823175158"

PROMOTION_BASELINE = "5ba7caa8dde7d5154b8d20da11c18274e83f41a8"
PROMOTION_OBSERVED = "2026-08-23T17:40:52.809092Z"
PROMOTION_SOURCE = "Supabase.list_migrations+Supabase.execute_sql"
FINAL_BASELINE = "42f39ec219983726e6fd1bc1715f90f95f4e3f42"
FINAL_OBSERVED = "2026-08-23T17:52:43.344298Z"
FINAL_SOURCE = "Supabase.list_migrations+Supabase.execute_sql"

PROMOTION_REPO_ONLY = {
    "direction": "repo_only",
    "name": NAME,
    "reason": "Stage38 hardening migration is promoted in repository first and must remain repo-only until its exact merged body passes CI and is applied once through Supabase.apply_migration. It does not activate Asaas or attest external evidence.",
    "owner": "BlackGold Forge",
    "related_failure_class": "BGF-STAGE37-BILLING-EVIDENCE-BINDING-GAP-320",
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


def assert_common(ledger: dict) -> None:
    if ledger.get("schema_version") != 1:
        raise ValueError("schema_version drift")
    if ledger.get("project_ref") != "mceukeondizkwlpfxzgf":
        raise ValueError("project_ref drift")
    remote_only, _ = divergences(ledger)
    if len(remote_only) != 3:
        raise ValueError("historical Stage17 remote-only count drift")


def state(ledger: dict) -> str:
    assert_common(ledger)
    remote = remote_map(ledger)
    _, repo_only = divergences(ledger)
    stage38_repo_only = [row for row in repo_only if row.get("name") == NAME]
    baseline = ledger.get("baseline_main_sha")
    observed = ledger.get("observed_at_utc")

    if baseline == PROMOTION_BASELINE and observed == PROMOTION_OBSERVED:
        if remote.get(NAME) is not None:
            raise ValueError("promotion frontier unexpectedly remote")
        if stage38_repo_only != [PROMOTION_REPO_ONLY]:
            raise ValueError("promotion repo-only declaration drift")
        return "promotion"

    if baseline == FINAL_BASELINE and observed == FINAL_OBSERVED:
        if remote.get(NAME) != REMOTE_VERSION:
            raise ValueError("final Stage38 remote version drift")
        if stage38_repo_only:
            raise ValueError("final Stage38 frontier still repo-only")
        if repo_only:
            raise ValueError("final Stage38 frontier has unrelated repo-only divergence")
        return "final"

    # Later stages may advance the global ledger while Stage38 remains sealed.
    if remote.get(NAME) == REMOTE_VERSION and not stage38_repo_only:
        return "post_final"

    raise ValueError("unknown Stage38 billing migration frontier")


def to_promotion(ledger: dict) -> dict:
    kind = state(ledger)
    if kind == "promotion":
        return clone(ledger)

    projected = clone(ledger)
    projected["baseline_main_sha"] = PROMOTION_BASELINE
    projected["observed_at_utc"] = PROMOTION_OBSERVED
    projected["source"] = PROMOTION_SOURCE
    projected["remote_migrations"] = [
        row for row in projected.get("remote_migrations", [])
        if not (isinstance(row, dict) and row.get("name") == NAME)
    ]
    remote_only, _repo_only = divergences(projected)
    # Historical projection must never carry later-stage repo-only declarations
    # backward into the sealed Stage38 promotion frontier. The exact historical
    # frontier had only the Stage38 repo-only declaration.
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
    remote_only, repo_only = divergences(projected)
    if repo_only:
        # Later repo-only migrations are unrelated to sealed Stage38 history.
        projected["declared_divergences"] = remote_only
    state(projected)
    return projected


def json_dump(value: dict) -> str:
    return json.dumps(value, indent=2) + "\n"
