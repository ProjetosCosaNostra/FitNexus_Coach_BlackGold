from __future__ import annotations

import copy
import json

NAME = "stage53_billing_evidence_provider_fk_index_hardening"
REMOTE_VERSION = "20260824212635"
PROMOTION_BASELINE = "21eead9f99236f2bb1711b3d3356cfc1d79751c2"
PROMOTION_OBSERVED = "2026-08-24T21:13:52.299927Z"
PROMOTION_SOURCE = "Supabase.list_migrations+Supabase.execute_sql"
FINAL_BASELINE = "00d670d207a88c4fc299f32bff90f80d2b72023c"
FINAL_OBSERVED = "2026-08-24T21:28:44.870436Z"
FINAL_SOURCE = "Supabase.list_migrations+Supabase.execute_sql"

PROMOTION_REPO_ONLY = {
    "direction": "repo_only",
    "name": NAME,
    "reason": "Stage53 promotes the green provider_code foreign-key index candidate as an exact versioned migration in the repository first. It must remain repo-only until this promotion PR is green and merged, then be applied exactly once through Supabase.apply_migration. It does not alter billing evidence rows, provider state, grants, or launch authority.",
    "owner": "BlackGold Forge",
    "related_failure_class": "BGF-STAGE53-CANDIDATE-DIRECT-APPLY-497",
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


def state(ledger: dict) -> str:
    if ledger.get("schema_version") != 1 or ledger.get("project_ref") != "mceukeondizkwlpfxzgf":
        raise ValueError("common ledger identity drift")
    remote_only, repo_only = divergences(ledger)
    if len(remote_only) != 3:
        raise ValueError("historical Stage17 remote-only count drift")
    remote = remote_map(ledger)
    stage53_repo = [row for row in repo_only if row.get("name") == NAME]
    baseline = ledger.get("baseline_main_sha")
    observed = ledger.get("observed_at_utc")

    if baseline == PROMOTION_BASELINE and observed == PROMOTION_OBSERVED:
        if remote.get(NAME) is not None or stage53_repo != [PROMOTION_REPO_ONLY] or len(repo_only) != 1:
            raise ValueError("Stage53 promotion frontier drift")
        return "promotion"
    if baseline == FINAL_BASELINE and observed == FINAL_OBSERVED:
        if remote.get(NAME) != REMOTE_VERSION or stage53_repo or repo_only:
            raise ValueError("Stage53 final frontier drift")
        return "final"
    if remote.get(NAME) == REMOTE_VERSION and not stage53_repo:
        return "post_final"
    raise ValueError("unknown Stage53 migration frontier")


def to_promotion(ledger: dict) -> dict:
    if state(ledger) == "promotion":
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
    remote_only, _repo_only = divergences(projected)
    projected["declared_divergences"] = remote_only
    state(projected)
    return projected


def json_dump(value: dict) -> str:
    return json.dumps(value, indent=2) + "\n"
