from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from migration_ledger_lib import (
    ReconcileError,
    normalize_remote_payload,
    parse_repo_migrations,
    reconcile,
    verify_authority_contract,
)


def authority(remote_rows, declared=None):
    return {
        "schema_version": 1,
        "failure_class": "BGF-REMOTE-REPO-MIGRATION-DIVERGENCE-142",
        "project_ref": "mceukeondizkwlpfxzgf",
        "project_name": "FitNexus Coach BlackGold",
        "baseline_main_sha": "0" * 40,
        "comparison_key": "migration_name",
        "declared_divergences": declared or [],
        "remote_migrations": remote_rows,
    }


class MigrationLedgerReconcilerTests(unittest.TestCase):
    def make_repo(self, names):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for timestamp, name in names:
            (root / f"{timestamp}_{name}.sql").write_text("-- test\n", encoding="utf-8")
        return temp, parse_repo_migrations(root)

    def test_name_match_allows_repo_timestamp_to_differ_from_remote_version(self):
        temp, repo = self.make_repo(
            [("20260819062000", "stage20_controlled_launch_admission")]
        )
        self.addCleanup(temp.cleanup)
        remote = normalize_remote_payload(
            {
                "migrations": [
                    {
                        "version": "20260819085840",
                        "name": "stage20_controlled_launch_admission",
                    }
                ]
            }
        )
        result = reconcile(
            authority(
                [
                    {
                        "version": "20260819085840",
                        "name": "stage20_controlled_launch_admission",
                    }
                ]
            ),
            repo,
            remote,
        )
        self.assertEqual(result["status"], "PASS")

    def test_remote_only_migration_fails_closed(self):
        temp, repo = self.make_repo(
            [("20260818113806", "stage1_auth_tenancy_foundation")]
        )
        self.addCleanup(temp.cleanup)
        remote = normalize_remote_payload(
            {
                "migrations": [
                    {
                        "version": "20260818113806",
                        "name": "stage1_auth_tenancy_foundation",
                    },
                    {
                        "version": "20260819085840",
                        "name": "stage20_controlled_launch_admission",
                    },
                ]
            }
        )
        with self.assertRaisesRegex(ReconcileError, "REMOTE_ONLY"):
            reconcile(
                authority(
                    [
                        {
                            "version": "20260818113806",
                            "name": "stage1_auth_tenancy_foundation",
                        }
                    ]
                ),
                repo,
                remote,
            )

    def test_repo_only_migration_fails_closed_when_undeclared(self):
        temp, repo = self.make_repo(
            [
                ("20260818113806", "stage1_auth_tenancy_foundation"),
                ("20260819100000", "future_repo_migration"),
            ]
        )
        self.addCleanup(temp.cleanup)
        remote = normalize_remote_payload(
            {
                "migrations": [
                    {
                        "version": "20260818113806",
                        "name": "stage1_auth_tenancy_foundation",
                    }
                ]
            }
        )
        with self.assertRaisesRegex(ReconcileError, "REPO_ONLY"):
            reconcile(
                authority(
                    [
                        {
                            "version": "20260818113806",
                            "name": "stage1_auth_tenancy_foundation",
                        }
                    ]
                ),
                repo,
                remote,
            )

    def test_declared_repo_only_migration_is_allowed(self):
        temp, repo = self.make_repo(
            [
                ("20260818113806", "stage1_auth_tenancy_foundation"),
                ("20260819100000", "future_repo_migration"),
            ]
        )
        self.addCleanup(temp.cleanup)
        remote = normalize_remote_payload(
            {
                "migrations": [
                    {
                        "version": "20260818113806",
                        "name": "stage1_auth_tenancy_foundation",
                    }
                ]
            }
        )
        result = reconcile(
            authority(
                [
                    {
                        "version": "20260818113806",
                        "name": "stage1_auth_tenancy_foundation",
                    }
                ],
                declared=[
                    {
                        "direction": "repo_only",
                        "name": "future_repo_migration",
                        "reason": "merged before controlled remote apply",
                        "owner": "BlackGold Forge",
                    }
                ],
            ),
            repo,
            remote,
        )
        self.assertEqual(result["repo_only_declared"], ["future_repo_migration"])

    def test_declared_historical_remote_only_is_valid_contract(self):
        temp, repo = self.make_repo(
            [("20260818113806", "stage1_auth_tenancy_foundation")]
        )
        self.addCleanup(temp.cleanup)
        contract = authority(
            [
                {
                    "version": "20260818113806",
                    "name": "stage1_auth_tenancy_foundation",
                },
                {"version": "20260819080135", "name": "historical_noop"},
            ],
            declared=[
                {
                    "direction": "remote_only",
                    "name": "historical_noop",
                    "reason": "known historical no-op ledger row",
                    "owner": "BlackGold Forge",
                }
            ],
        )
        result = verify_authority_contract(
            contract,
            {"project_ref": "mceukeondizkwlpfxzgf"},
            repo,
        )
        self.assertEqual(result["baseline_remote_count"], 2)

    def test_known_remote_version_change_fails_closed(self):
        temp, repo = self.make_repo(
            [("20260818113806", "stage1_auth_tenancy_foundation")]
        )
        self.addCleanup(temp.cleanup)
        remote = normalize_remote_payload(
            {
                "migrations": [
                    {
                        "version": "20260818120000",
                        "name": "stage1_auth_tenancy_foundation",
                    }
                ]
            }
        )
        with self.assertRaisesRegex(ReconcileError, "REMOTE_VERSION_CHANGED"):
            reconcile(
                authority(
                    [
                        {
                            "version": "20260818113806",
                            "name": "stage1_auth_tenancy_foundation",
                        }
                    ]
                ),
                repo,
                remote,
            )

    def test_duplicate_repo_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "20260818110000_duplicate_name.sql").write_text(
                "-- a\n", encoding="utf-8"
            )
            (root / "20260818120000_duplicate_name.sql").write_text(
                "-- b\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ReconcileError, "duplicate migration names"):
                parse_repo_migrations(root)


if __name__ == "__main__":
    unittest.main()
