from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

RECEIPT_NAME = "stage35_alert_delivery_receipt_store"
FIXTURE_NAME = "stage35_alert_delivery_controlled_proof_fixture"
CLEANUP_NAME = "stage35_alert_delivery_controlled_proof_cleanup"
RECEIPT_VERSION = "20260823092354"
FIXTURE_VERSION = "20260823145908"
CLEANUP_VERSION = "20260823161543"

FINAL_BASELINE = "0b8081aad409b48df22085da003e595578e0c5bb"
FINAL_OBSERVED = "2026-08-23T16:15:55.264448Z"
CLEANUP_BASELINE = "db522140cc2b21840b5b48727cb15a82ca22f975"
CLEANUP_OBSERVED = "2026-08-23T16:06:48.978350Z"
RECONCILED_BASELINE = "a23dd9d892189b92a633634caf750606504e83ee"
RECONCILED_OBSERVED = "2026-08-23T15:56:57.947085Z"
FIXTURE_BASELINE = "8324413284aaad9fc932f8f86269b6c339f240e9"
FIXTURE_OBSERVED = "2026-08-23T09:05:47.415327Z"
RECEIPT_BASELINE = "6aad66c159c82c634af8ec58f0ec742267484b70"
RECEIPT_OBSERVED = "2026-08-22T07:54:12.776139Z"

RECEIPT_REPO_ONLY = {
    "direction": "repo_only",
    "name": RECEIPT_NAME,
    "reason": "Exact repository promotion of the reviewed Stage35 privacy-minimized alert delivery receipt-store candidate. Remote application remains forbidden until a separate dispatcher deployment and controlled external-delivery proof sequence is authorized.",
    "owner": "BlackGold Forge",
    "related_failure_class": "BGF-STAGE35-ALERT-CANDIDATE-REMOTE-MUTATION-281",
}
FIXTURE_REPO_ONLY = {
    "direction": "repo_only",
    "name": FIXTURE_NAME,
    "reason": "Exact repository promotion of the reviewed Stage35 synthetic controlled-delivery fixture after runtime secret-name readiness was proven. Remote application remains forbidden until this promotion is merged green and the receipt-store apply / dispatcher deployment sequence is separately authorized.",
    "owner": "BlackGold Forge",
    "related_failure_class": "BGF-STAGE35-ALERT-CONTROLLED-FIXTURE-PREMATURE-284",
}
CLEANUP_REPO_ONLY = {
    "direction": "repo_only",
    "name": CLEANUP_NAME,
    "reason": "Exact repository promotion of the sealed Stage35 synthetic proof cleanup after immutable Telegram delivery PASS and fresh durable-receipt verification. Remote application remains forbidden until this promotion is CI-green and merged to main.",
    "owner": "BlackGold Forge",
    "related_failure_class": "BGF-STAGE35-ALERT-PROOF-CLEANUP-286",
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
    if ledger.get("schema_version") != 1 or ledger.get("project_ref") != "mceukeondizkwlpfxzgf":
        raise ValueError("project/schema authority drift")
    remote_only, _ = divergences(ledger)
    if len(remote_only) != 3:
        raise ValueError("historical Stage17 remote-only divergence count drift")
    remote = remote_map(ledger)
    if remote.get("stage33_direct_rpc_revocation_and_post_revocation_fixture") != "20260822032456":
        raise ValueError("Stage33 revocation history drift")
    if remote.get("stage33_post_revocation_proof_cleanup") != "20260822061133":
        raise ValueError("Stage33 cleanup history drift")


def state(ledger: dict) -> str:
    assert_common(ledger)
    baseline = ledger.get("baseline_main_sha")
    observed = ledger.get("observed_at_utc")
    remote = remote_map(ledger)
    _, repo_only = divergences(ledger)
    repo_names = {row.get("name") for row in repo_only}

    if baseline == FINAL_BASELINE and observed == FINAL_OBSERVED:
        if repo_only or remote.get(RECEIPT_NAME) != RECEIPT_VERSION or remote.get(FIXTURE_NAME) != FIXTURE_VERSION or remote.get(CLEANUP_NAME) != CLEANUP_VERSION:
            raise ValueError("final Stage35 frontier drift")
        return "final"
    if baseline == CLEANUP_BASELINE and observed == CLEANUP_OBSERVED:
        if repo_names != {CLEANUP_NAME} or len(repo_only) != 1 or remote.get(RECEIPT_NAME) != RECEIPT_VERSION or remote.get(FIXTURE_NAME) != FIXTURE_VERSION or CLEANUP_NAME in remote:
            raise ValueError("cleanup-promotion frontier drift")
        return "cleanup_promotion"
    if baseline == RECONCILED_BASELINE and observed == RECONCILED_OBSERVED:
        if repo_only or remote.get(RECEIPT_NAME) != RECEIPT_VERSION or remote.get(FIXTURE_NAME) != FIXTURE_VERSION or CLEANUP_NAME in remote:
            raise ValueError("remote-reconciled frontier drift")
        return "reconciled"
    if baseline == FIXTURE_BASELINE and observed == FIXTURE_OBSERVED:
        if repo_names != {RECEIPT_NAME, FIXTURE_NAME} or len(repo_only) != 2 or RECEIPT_NAME in remote or FIXTURE_NAME in remote or CLEANUP_NAME in remote:
            raise ValueError("fixture-promotion frontier drift")
        return "fixture"
    if baseline == RECEIPT_BASELINE and observed == RECEIPT_OBSERVED:
        if repo_names != {RECEIPT_NAME} or len(repo_only) != 1 or RECEIPT_NAME in remote or FIXTURE_NAME in remote or CLEANUP_NAME in remote:
            raise ValueError("receipt-promotion frontier drift")
        return "receipt"
    raise ValueError("unknown Stage35 migration frontier")


def _remove_remote(ledger: dict, names: set[str]) -> None:
    ledger["remote_migrations"] = [
        row for row in ledger.get("remote_migrations", [])
        if not (isinstance(row, dict) and row.get("name") in names)
    ]


def _remote_only(ledger: dict) -> list[dict]:
    return clone({"rows": divergences(ledger)[0]})["rows"]


def to_cleanup_promotion(ledger: dict) -> dict:
    kind = state(ledger)
    if kind == "cleanup_promotion":
        return clone(ledger)
    if kind != "final":
        raise ValueError(f"cannot project {kind} to cleanup_promotion")
    projected = clone(ledger)
    projected["baseline_main_sha"] = CLEANUP_BASELINE
    projected["observed_at_utc"] = CLEANUP_OBSERVED
    _remove_remote(projected, {CLEANUP_NAME})
    projected["declared_divergences"] = _remote_only(ledger) + [clone(CLEANUP_REPO_ONLY)]
    state(projected)
    return projected


def to_reconciled(ledger: dict) -> dict:
    kind = state(ledger)
    if kind == "reconciled":
        return clone(ledger)
    if kind == "final":
        ledger = to_cleanup_promotion(ledger)
        kind = "cleanup_promotion"
    if kind != "cleanup_promotion":
        raise ValueError(f"cannot project {kind} to reconciled")
    projected = clone(ledger)
    projected["baseline_main_sha"] = RECONCILED_BASELINE
    projected["observed_at_utc"] = RECONCILED_OBSERVED
    projected["declared_divergences"] = _remote_only(ledger)
    state(projected)
    return projected


def to_fixture(ledger: dict) -> dict:
    kind = state(ledger)
    if kind == "fixture":
        return clone(ledger)
    if kind in {"final", "cleanup_promotion"}:
        ledger = to_reconciled(ledger)
        kind = "reconciled"
    if kind != "reconciled":
        raise ValueError(f"cannot project {kind} to fixture")
    projected = clone(ledger)
    projected["baseline_main_sha"] = FIXTURE_BASELINE
    projected["observed_at_utc"] = FIXTURE_OBSERVED
    _remove_remote(projected, {RECEIPT_NAME, FIXTURE_NAME})
    projected["declared_divergences"] = _remote_only(ledger) + [clone(RECEIPT_REPO_ONLY), clone(FIXTURE_REPO_ONLY)]
    state(projected)
    return projected


def to_receipt(ledger: dict) -> dict:
    kind = state(ledger)
    if kind == "receipt":
        return clone(ledger)
    if kind != "fixture":
        ledger = to_fixture(ledger)
    projected = clone(ledger)
    projected["baseline_main_sha"] = RECEIPT_BASELINE
    projected["observed_at_utc"] = RECEIPT_OBSERVED
    projected["declared_divergences"] = [
        row for row in projected.get("declared_divergences", [])
        if not (isinstance(row, dict) and row.get("direction") == "repo_only" and row.get("name") == FIXTURE_NAME)
    ]
    state(projected)
    return projected


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def json_dump(value: dict) -> str:
    return json.dumps(value, indent=2) + "\n"
