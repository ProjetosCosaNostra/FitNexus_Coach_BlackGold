from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "04_backend_supabase" / "migrations"
FLUTTER = ROOT / "03_app_flutter" / "fitnexus_app" / "lib" / "features" / "professor"


def fail(code: str, detail: str) -> None:
    print(f"DECISION_INTELLIGENCE_CONTRACT_GATE=FAIL")
    print(f"FAILURE_CLASS={code}")
    print(f"DETAIL={detail}")
    raise SystemExit(1)


def require(text: str, needle: str, code: str, detail: str) -> None:
    if needle not in text:
        fail(code, detail)


def read(path: Path, code: str) -> str:
    if not path.exists():
        fail(code, f"required file missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    migration_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(MIGRATIONS.glob("*.sql"))
    )
    data_repo = read(
        FLUTTER / "professor_data_repository.dart",
        "BGF-DECISION-CONTRACT-FILE-MISSING-016",
    )
    studio = read(
        FLUTTER / "training_decision_studio_page.dart",
        "BGF-DECISION-CONTRACT-FILE-MISSING-016",
    )
    intelligence_page = read(
        FLUTTER / "professor_decision_intelligence_page.dart",
        "BGF-DECISION-CONTRACT-FILE-MISSING-016",
    )

    checks = [
        (
            migration_text,
            "create_training_plan_from_decision_intelligence_v2",
            "BGF-DECISION-STUDENT-BINDING-015",
            "student-bound atomic intelligence commit RPC disappeared",
        ),
        (
            migration_text,
            "DECISION_INTELLIGENCE_STUDENT_BINDING_MISMATCH",
            "BGF-DECISION-STUDENT-BINDING-015",
            "server-side run/student mismatch interlock disappeared",
        ),
        (
            migration_text,
            "decision_intelligence_outcomes",
            "BGF-DECISION-AUDIT-SPLITBRAIN-014",
            "human decision outcome ledger disappeared",
        ),
        (
            migration_text,
            "outcome in ('accepted','modified','rejected','no_action')",
            "BGF-DECISION-AUDIT-SPLITBRAIN-014",
            "controlled human outcome vocabulary drifted",
        ),
        (
            migration_text,
            "private.normalize_training_exercises(p_exercises)",
            "BGF-DECISION-OUTCOME-TRUST-017",
            "server-side accepted/modified comparison disappeared",
        ),
        (
            migration_text,
            "get_decision_intelligence_calibration",
            "BGF-DECISION-CALIBRATION-018",
            "human calibration RPC disappeared",
        ),
        (
            migration_text,
            "Calibração de uso e decisão humana; não mede eficácia clínica",
            "BGF-DECISION-CALIBRATION-018",
            "calibration safety interpretation disappeared",
        ),
        (
            data_repo,
            "create_training_plan_from_decision_intelligence_v2",
            "BGF-DECISION-AUDIT-SPLITBRAIN-014",
            "Flutter no longer routes intelligence commits through atomic V2 RPC",
        ),
        (
            data_repo,
            "'p_student_id': studentId",
            "BGF-DECISION-STUDENT-BINDING-015",
            "Flutter stopped sending selected student to binding interlock",
        ),
        (
            studio,
            "_previewFingerprint != currentFingerprint",
            "BGF-DECISION-PREVIEW-DRIFT-019",
            "preview fingerprint invalidation disappeared",
        ),
        (
            intelligence_page,
            "initialSourceTemplateId: candidate.templateId",
            "BGF-DECISION-PROVENANCE-020",
            "Smart Template provenance stopped flowing into Decision Studio",
        ),
        (
            intelligence_page,
            "CALIBRAÇÃO HUMANA",
            "BGF-DECISION-CALIBRATION-018",
            "human calibration UI disappeared",
        ),
    ]

    for text, needle, code, detail in checks:
        require(text, needle, code, detail)

    # Public Stage 12 commands must stay invoker-based and anonymous execution must be revoked.
    for function_signature in (
        "public.create_training_plan_from_decision_intelligence_v2(uuid,uuid,text,text,text,jsonb,text)",
        "public.record_decision_intelligence_outcome(uuid,text,text)",
        "public.get_decision_intelligence_calibration(uuid)",
    ):
        require(
            migration_text,
            f"revoke execute on function {function_signature} from public, anon;",
            "BGF-DECISION-RPC-AUTHORITY-021",
            f"anonymous revoke missing for {function_signature}",
        )
        require(
            migration_text,
            f"grant execute on function {function_signature} to authenticated;",
            "BGF-DECISION-RPC-AUTHORITY-021",
            f"authenticated grant missing for {function_signature}",
        )

    print("DECISION_INTELLIGENCE_CONTRACT_GATE=PASS")
    print("ATOMIC_OUTCOME=PASS")
    print("STUDENT_BINDING=PASS")
    print("SERVER_OUTCOME_CLASSIFICATION=PASS")
    print("PREVIEW_FINGERPRINT=PASS")
    print("CALIBRATION_SAFETY=PASS")
    print("PROVENANCE=PASS")
    print("RPC_AUTHORITY=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
