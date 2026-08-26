from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "04_backend_supabase"
AUTHORITY = BACKEND / "stage88_terms_acceptance_remote_apply_execution_seal_authority.json"
PLAN = BACKEND / "operations" / "stage88_terms_acceptance_remote_apply_execution_plan.json"
MIGRATION = BACKEND / "migrations" / "20260826180000_stage85_terms_acceptance_registry_ledger.sql"
STAGE87 = BACKEND / "stage87_terms_acceptance_remote_apply_gate_preparation_authority.json"
GATE = BACKEND / "operations" / "stage87_terms_acceptance_remote_apply_gate_contract.json"
LEDGER = BACKEND / "migration_ledger_authority.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
FAILURE = "BGF-STAGE88-REMOTE-APPLY-EXECUTION-SEAL-GUARD-878"

def fail(detail: str) -> None:
    raise SystemExit(f"STAGE88_TERMS_ACCEPTANCE_REMOTE_APPLY_EXECUTION_SEAL=FAIL\nFAILURE_CLASS={FAILURE}\nDETAIL={detail}")

def load(path: Path) -> dict:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: fail(f"load failed {path.relative_to(ROOT)}:{type(exc).__name__}")
    if not isinstance(value,dict): fail(f"expected object {path.relative_to(ROOT)}")
    return value

def blob(path: Path) -> str:
    raw=path.read_bytes(); return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--source-sha",required=True); p.add_argument("--output",required=True,type=Path); a=p.parse_args()
    source=a.source_sha.strip().lower()
    if SHA40.fullmatch(source) is None: fail("invalid source sha")
    auth=load(AUTHORITY); plan=load(PLAN); ledger=load(LEDGER)
    pins=auth.get("sealed_inputs",{})
    for key,path in (("stage87_authority_blob",STAGE87),("stage87_gate_contract_blob",GATE),("migration_blob",MIGRATION),("migration_ledger_blob",LEDGER),("execution_plan_blob",PLAN)):
        if pins.get(key)!=blob(path): fail(f"sealed input drift:{key}")
    if plan.get("execution_seal",{}).get("stage88_executes_remote_apply") is not False: fail("Stage88 execution boundary drift")
    repo=[r for r in ledger.get("declared_divergences",[]) if isinstance(r,dict) and r.get("direction")=="repo_only"]
    if len(repo)!=1 or repo[0].get("name")!="stage85_terms_acceptance_registry_ledger": fail("target is not unique repo-only migration")
    out={
      "schema_version":1,"stage":"STAGE88_TERMS_ACCEPTANCE_REMOTE_APPLY_EXECUTION_SEAL",
      "output_kind":"NON_ATTESTING_REPO_ONLY_ONE_SHOT_REMOTE_APPLY_EXECUTION_SEAL_PACKET",
      "source_sha":source,
      "migration":{"name":"stage85_terms_acceptance_registry_ledger","git_blob_sha":blob(MIGRATION),"sha256":sha256(MIGRATION),"remote_applied":False},
      "execution_plan":{"git_blob_sha":blob(PLAN),"sha256":sha256(PLAN),"one_shot":True,"stage88_executes":False},
      "fresh_remote_receipt":auth.get("fresh_pre_seal_remote_receipt"),
      "hard_boundaries":{"remote_migration_applied":False,"supabase_mutation":False,"terms_registry_row_created":False,"real_acceptance_collected":False,"target_decision_closed":False,"legal_terms_gate_ready":False},
      "next_after_green":auth.get("next_after_green")}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE88_TERMS_ACCEPTANCE_REMOTE_APPLY_EXECUTION_SEAL=PASS")
    print("ONE_SHOT_EXECUTION_SEALED=true")
    print("REMOTE_MIGRATION_APPLIED=false")
    print("SUPABASE_MUTATION=false")
    print("LEGAL_TERMS_GATE_READY=false")

if __name__=="__main__": main()
