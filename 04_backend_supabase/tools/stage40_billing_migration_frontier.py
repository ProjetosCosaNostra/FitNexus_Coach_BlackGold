from __future__ import annotations

import copy
import json

NAME = "stage40_billing_production_environment_interlock"
REMOTE_VERSION = "20260824003612"
PROMOTION_BASELINE = "f3288d465cf6f3457ce2403b470a2546b5672d0f"
PROMOTION_OBSERVED = "2026-08-24T00:27:03.610215Z"
PROMOTION_SOURCE = "Supabase.list_migrations+Supabase.execute_sql"
FINAL_BASELINE = "e208f98bce763c71e7edb8b066a8c97b45a12904"
FINAL_OBSERVED = "2026-08-24T00:37:12.870108Z"
FINAL_SOURCE = "Supabase.list_migrations+Supabase.execute_sql"

PROMOTION_REPO_ONLY = {
    "direction": "repo_only",
    "name": NAME,
    "reason": "Stage40 promotes the already-green operations candidate as an exact versioned migration in the repository first. It must remain repo-only until this promotion PR is green and merged, then be applied exactly once through Supabase.apply_migration. It does not activate Asaas or attest external evidence.",
    "owner": "BlackGold Forge",
    "related_failure_class": "BGF-STAGE40-BILLING-CANDIDATE-DIRECT-APPLY-360",
}


def clone(value: dict) -> dict:
    return copy.deepcopy(value)


def remote_map(ledger: dict) -> dict[str, str]:
    return {str(r.get("name")): str(r.get("version")) for r in ledger.get("remote_migrations", []) if isinstance(r, dict)}


def divergences(ledger: dict) -> tuple[list[dict], list[dict]]:
    rows = [r for r in ledger.get("declared_divergences", []) if isinstance(r, dict)]
    return ([r for r in rows if r.get("direction") == "remote_only"], [r for r in rows if r.get("direction") == "repo_only"])


def state(ledger: dict) -> str:
    if ledger.get("schema_version") != 1 or ledger.get("project_ref") != "mceukeondizkwlpfxzgf":
        raise ValueError("common ledger identity drift")
    remote_only, repo_only = divergences(ledger)
    if len(remote_only) != 3:
        raise ValueError("historical Stage17 remote-only count drift")
    remote = remote_map(ledger)
    stage40_repo = [r for r in repo_only if r.get("name") == NAME]
    baseline = ledger.get("baseline_main_sha")
    observed = ledger.get("observed_at_utc")
    if baseline == PROMOTION_BASELINE and observed == PROMOTION_OBSERVED:
        if remote.get(NAME) is not None or stage40_repo != [PROMOTION_REPO_ONLY]:
            raise ValueError("Stage40 promotion frontier drift")
        return "promotion"
    if baseline == FINAL_BASELINE and observed == FINAL_OBSERVED:
        if remote.get(NAME) != REMOTE_VERSION or stage40_repo or repo_only:
            raise ValueError("Stage40 final frontier drift")
        return "final"
    if remote.get(NAME) == REMOTE_VERSION and not stage40_repo:
        return "post_final"
    raise ValueError("unknown Stage40 migration frontier")


def to_promotion(ledger: dict) -> dict:
    if state(ledger) == "promotion":
        return clone(ledger)
    projected = clone(ledger)
    projected["baseline_main_sha"] = PROMOTION_BASELINE
    projected["observed_at_utc"] = PROMOTION_OBSERVED
    projected["source"] = PROMOTION_SOURCE
    projected["remote_migrations"] = [r for r in projected.get("remote_migrations", []) if not (isinstance(r, dict) and r.get("name") == NAME)]
    remote_only, _ = divergences(projected)
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
    remote_only, _ = divergences(projected)
    projected["declared_divergences"] = remote_only
    state(projected)
    return projected


def json_dump(value: dict) -> str:
    return json.dumps(value, indent=2) + "\n"
