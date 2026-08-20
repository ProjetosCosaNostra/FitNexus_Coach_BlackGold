from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
STAGE24 = BACKEND / "migrations" / "20260819192100_stage24_student_access_abuse_observability.sql"
STAGE27 = BACKEND / "migrations" / "20260820063000_stage27_student_network_origin_rate_limit.sql"
AUTHORITY = BACKEND / "student_access_network_rate_limit_authority.json"

FAILURE_CLASS = "BGF-POSTGRES-VIEW-COLUMN-ORDER-178"
VIEW_NAME = "private.student_access_security_posture_v1"


def fail(message: str) -> None:
    raise SystemExit(f"POSTGRES_VIEW_REPLACE_COMPATIBILITY_GUARD=FAIL\n{FAILURE_CLASS} {message}")


def read_text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def extract_view_aliases(sql: str) -> list[str]:
    lower = sql.lower()
    marker = f"create or replace view {VIEW_NAME}"
    try:
        start = lower.index(marker)
        end = lower.index(f";\n\nrevoke all on {VIEW_NAME}", start)
    except ValueError as exc:
        fail(f"cannot isolate {VIEW_NAME}: {exc}")

    segment = lower[start:end]
    split_marker = "\nas\nselect\n"
    if split_marker not in segment:
        fail(f"{VIEW_NAME} does not use the expected AS SELECT structure")
    select_body = segment.split(split_marker, 1)[1]
    return re.findall(r"\bas\s+([a-z_][a-z0-9_]*)\b", select_body)


def main() -> None:
    stage24 = read_text(STAGE24)
    stage27 = read_text(STAGE27)
    authority = json.loads(read_text(AUTHORITY))

    db = authority.get("database_contract", {})
    if db.get("posture_view_replace_policy") != "preserve_existing_columns_in_order_append_new_columns_only":
        fail("append-only CREATE OR REPLACE VIEW policy is missing from authority")

    stage24_aliases = extract_view_aliases(stage24)
    stage27_aliases = extract_view_aliases(stage27)

    declared_existing = db.get("posture_view_existing_columns")
    if declared_existing != stage24_aliases:
        fail(
            "authority no longer matches the Stage 24 live-layout source: "
            f"declared={declared_existing!r} source={stage24_aliases!r}"
        )

    appended = db.get("posture_view_stage27_appended_column")
    if not isinstance(appended, str) or not appended:
        fail("Stage 27 appended-column authority is missing")

    expected = stage24_aliases + [appended]
    if stage27_aliases != expected:
        fail(
            "CREATE OR REPLACE VIEW changed an existing name/order instead of appending: "
            f"expected={expected!r} actual={stage27_aliases!r}"
        )

    if FAILURE_CLASS not in stage27:
        fail("migration does not permanently register the failure class")

    print("POSTGRES_VIEW_REPLACE_COMPATIBILITY_GUARD=PASS")
    print(f"VIEW={VIEW_NAME}")
    print(f"EXISTING_COLUMNS_PRESERVED={len(stage24_aliases)}")
    print(f"APPENDED_COLUMN={appended}")
    print("REPLACEMENT_POLICY=PRESERVE_EXISTING_ORDER_APPEND_ONLY")


if __name__ == "__main__":
    main()
