from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MIGRATION_FILE_RE = re.compile(r"^(?P<timestamp>\d{14})_(?P<name>[a-z0-9][a-z0-9_]*)\.sql$")
REMOTE_VERSION_RE = re.compile(r"^\d{14}$")


class ReconcileError(ValueError):
    pass


@dataclass(frozen=True)
class RepoMigration:
    timestamp: str
    name: str
    path: str


@dataclass(frozen=True)
class RemoteMigration:
    version: str
    name: str


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReconcileError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReconcileError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReconcileError(f"expected JSON object in {path}")
    return value


def parse_repo_migrations(migrations_dir: Path) -> list[RepoMigration]:
    if not migrations_dir.is_dir():
        raise ReconcileError(f"migration directory not found: {migrations_dir}")

    result: list[RepoMigration] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        match = MIGRATION_FILE_RE.fullmatch(path.name)
        if match is None:
            raise ReconcileError(
                "migration filename must be <14-digit timestamp>_<snake_case_name>.sql: "
                f"{path.name}"
            )
        result.append(
            RepoMigration(
                timestamp=match.group("timestamp"),
                name=match.group("name"),
                path=path.as_posix(),
            )
        )
    _assert_unique_names((item.name for item in result), "repository")
    return result


def normalize_remote_payload(value: dict) -> list[RemoteMigration]:
    # Accept both the direct connector payload {"migrations":[...]} and
    # an exported wrapper {"text":"{\"migrations\":[...]}"}.
    if "migrations" not in value and isinstance(value.get("text"), str):
        try:
            value = json.loads(value["text"])
        except json.JSONDecodeError as exc:
            raise ReconcileError("remote payload text is not valid JSON") from exc

    rows = value.get("migrations")
    if not isinstance(rows, list):
        raise ReconcileError("remote payload must contain a migrations array")

    result: list[RemoteMigration] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ReconcileError(f"remote migration #{index} is not an object")
        version = str(row.get("version", "")).strip()
        name = str(row.get("name", "")).strip()
        if REMOTE_VERSION_RE.fullmatch(version) is None:
            raise ReconcileError(f"remote migration has invalid version: {version!r}")
        if re.fullmatch(r"[a-z0-9][a-z0-9_]*", name) is None:
            raise ReconcileError(f"remote migration has invalid name: {name!r}")
        result.append(RemoteMigration(version=version, name=name))

    _assert_unique_names((item.name for item in result), "remote")
    versions = [item.version for item in result]
    if len(versions) != len(set(versions)):
        raise ReconcileError("remote migration versions are not unique")
    return result


def manifest_remote_migrations(authority: dict) -> list[RemoteMigration]:
    rows = authority.get("remote_migrations")
    if not isinstance(rows, list):
        raise ReconcileError("authority remote_migrations must be an array")
    return normalize_remote_payload({"migrations": rows})


def declared_divergences(authority: dict) -> dict[tuple[str, str], dict]:
    rows = authority.get("declared_divergences", [])
    if not isinstance(rows, list):
        raise ReconcileError("authority declared_divergences must be an array")
    result: dict[tuple[str, str], dict] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ReconcileError(f"declared divergence #{index} is not an object")
        direction = str(row.get("direction", "")).strip()
        name = str(row.get("name", "")).strip()
        reason = str(row.get("reason", "")).strip()
        owner = str(row.get("owner", "")).strip()
        if direction not in {"repo_only", "remote_only"}:
            raise ReconcileError(
                f"declared divergence #{index} direction must be repo_only or remote_only"
            )
        if re.fullmatch(r"[a-z0-9][a-z0-9_]*", name) is None:
            raise ReconcileError(f"declared divergence #{index} has invalid name")
        if not reason or not owner:
            raise ReconcileError(
                f"declared divergence #{index} must include non-empty reason and owner"
            )
        key = (direction, name)
        if key in result:
            raise ReconcileError(f"duplicate declared divergence: {direction}:{name}")
        result[key] = row
    return result


def verify_authority_contract(
    authority: dict,
    project_identity: dict,
    repo_migrations: list[RepoMigration],
) -> dict:
    if authority.get("schema_version") != 1:
        raise ReconcileError("migration ledger authority schema_version must be 1")
    if authority.get("failure_class") != "BGF-REMOTE-REPO-MIGRATION-DIVERGENCE-142":
        raise ReconcileError("migration ledger authority has unexpected failure_class")

    project_ref = str(project_identity.get("project_ref", "")).strip()
    if authority.get("project_ref") != project_ref:
        raise ReconcileError(
            "migration ledger authority project_ref does not match project_identity.json"
        )

    baseline_main_sha = str(authority.get("baseline_main_sha", "")).strip()
    if re.fullmatch(r"[0-9a-f]{40}", baseline_main_sha) is None:
        raise ReconcileError("baseline_main_sha must be a 40-character lowercase git SHA")

    if authority.get("comparison_key") != "migration_name":
        raise ReconcileError(
            "comparison_key must remain migration_name; timestamps are not stable across "
            "repo filenames and tool-applied remote ledger versions"
        )

    remote_baseline = manifest_remote_migrations(authority)
    declared = declared_divergences(authority)

    repo_names = {item.name for item in repo_migrations}
    baseline_names = {item.name for item in remote_baseline}

    baseline_remote_only = sorted(baseline_names - repo_names)
    repo_only = sorted(repo_names - baseline_names)

    undeclared_baseline_remote_only = [
        name for name in baseline_remote_only if ("remote_only", name) not in declared
    ]
    undeclared_repo_only = [
        name for name in repo_only if ("repo_only", name) not in declared
    ]
    if undeclared_baseline_remote_only or undeclared_repo_only:
        details: list[str] = []
        if undeclared_baseline_remote_only:
            details.append(
                "BASELINE_REMOTE_ONLY=" + ",".join(undeclared_baseline_remote_only)
            )
        if undeclared_repo_only:
            details.append("REPO_ONLY=" + ",".join(undeclared_repo_only))
        raise ReconcileError(
            "authority contract contains undeclared divergence: " + " | ".join(details)
        )

    stale_declarations: list[str] = []
    for direction, name in declared:
        if direction == "remote_only" and name not in baseline_remote_only:
            stale_declarations.append(f"remote_only:{name}")
        if direction == "repo_only" and name not in repo_only:
            stale_declarations.append(f"repo_only:{name}")
    if stale_declarations:
        raise ReconcileError(
            "authority contract has stale declared divergence: "
            + ", ".join(sorted(stale_declarations))
        )

    return {
        "repo_count": len(repo_migrations),
        "baseline_remote_count": len(remote_baseline),
        "baseline_main_sha": baseline_main_sha,
        "project_ref": project_ref,
    }


def reconcile(
    authority: dict,
    repo_migrations: list[RepoMigration],
    actual_remote: list[RemoteMigration],
) -> dict:
    baseline_remote = manifest_remote_migrations(authority)
    declared = declared_divergences(authority)

    repo_by_name = {item.name: item for item in repo_migrations}
    remote_by_name = {item.name: item for item in actual_remote}
    baseline_by_name = {item.name: item for item in baseline_remote}

    remote_only = sorted(set(remote_by_name) - set(repo_by_name))
    repo_only = sorted(set(repo_by_name) - set(remote_by_name))

    undeclared_remote_only = [
        name for name in remote_only if ("remote_only", name) not in declared
    ]
    undeclared_repo_only = [
        name for name in repo_only if ("repo_only", name) not in declared
    ]

    version_changes: list[str] = []
    for name in sorted(set(remote_by_name) & set(baseline_by_name)):
        old = baseline_by_name[name].version
        new = remote_by_name[name].version
        if old != new:
            version_changes.append(f"{name}:{old}->{new}")

    if undeclared_remote_only or undeclared_repo_only or version_changes:
        details: list[str] = []
        if undeclared_remote_only:
            details.append("REMOTE_ONLY=" + ",".join(undeclared_remote_only))
        if undeclared_repo_only:
            details.append("REPO_ONLY=" + ",".join(undeclared_repo_only))
        if version_changes:
            details.append("REMOTE_VERSION_CHANGED=" + ",".join(version_changes))
        raise ReconcileError(
            "undeclared migration ledger divergence; fail closed: " + " | ".join(details)
        )

    stale_declarations: list[str] = []
    for (direction, name), _row in declared.items():
        if direction == "remote_only" and name not in remote_only:
            stale_declarations.append(f"remote_only:{name}")
        if direction == "repo_only" and name not in repo_only:
            stale_declarations.append(f"repo_only:{name}")
    if stale_declarations:
        raise ReconcileError(
            "stale declared divergence must be removed: "
            + ", ".join(sorted(stale_declarations))
        )

    return {
        "status": "PASS",
        "repo_count": len(repo_migrations),
        "remote_count": len(actual_remote),
        "remote_only_declared": remote_only,
        "repo_only_declared": repo_only,
        "project_ref": authority.get("project_ref"),
    }


def _assert_unique_names(names: Iterable[str], source: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for name in names:
        if name in seen:
            duplicates.add(name)
        seen.add(name)
    if duplicates:
        raise ReconcileError(
            f"duplicate migration names in {source}: " + ", ".join(sorted(duplicates))
        )
