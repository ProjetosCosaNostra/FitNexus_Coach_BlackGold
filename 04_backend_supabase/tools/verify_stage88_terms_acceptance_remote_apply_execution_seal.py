from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BACKEND=ROOT/"04_backend_supabase"
AUTHORITY=BACKEND/"stage88_terms_acceptance_remote_apply_execution_seal_authority.json"
PLAN=BACKEND/"operations"/"stage88_terms_acceptance_remote_apply_execution_plan.json"
STAGE87=BACKEND/"stage87_terms_acceptance_remote_apply_gate_preparation_authority.json"
GATE=BACKEND/"operations"/"stage87_terms_acceptance_remote_apply_gate_contract.json"
MIGRATION=BACKEND/"migrations"/"20260826180000_stage85_terms_acceptance_registry_ledger.sql"
LEDGER=BACKEND/"migration_ledger_authority.json"
BUILDER=BACKEND/"tools"/"build_stage88_terms_acceptance_remote_apply_execution_seal.py"
WORKFLOW=ROOT/".github"/"workflows"/"stage88_terms_acceptance_remote_apply_execution_seal.yml"
OPEN_DECISIONS=ROOT/"10_compliance"/"drafts"/"COMPLIANCE_OPEN_DECISIONS.json"
TERMS=ROOT/"10_compliance"/"drafts"/"TERMS_OF_USE_CANDIDATE_PTBR.md"
FAILURE="BGF-STAGE88-REMOTE-APPLY-EXECUTION-SEAL-GUARD-878"
FORBIDDEN_IMPORTS={"os","subprocess","socket","urllib","http","requests","psycopg","supabase"}
FORBIDDEN_WORKFLOW=("apply_migration","execute_sql","supabase db","service_role","supabase_access_token","database_url","curl ","wget ","workflow_dispatch","schedule:","deploy-pages")

def fail(d:str)->None: raise SystemExit(f"STAGE88_TERMS_ACCEPTANCE_REMOTE_APPLY_EXECUTION_SEAL_GUARD=FAIL\nFAILURE_CLASS={FAILURE}\nDETAIL={d}")
def load(p:Path)->dict:
    try:v=json.loads(p.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: fail(f"load failed {p.relative_to(ROOT)}:{type(e).__name__}")
    if not isinstance(v,dict):fail(f"expected object {p.relative_to(ROOT)}")
    return v
def blob(p:Path)->str:
    r=p.read_bytes();return hashlib.sha1(f"blob {len(r)}\0".encode()+r).hexdigest()

def main()->None:
    a=load(AUTHORITY); p=load(PLAN); s87=load(STAGE87); gate=load(GATE); ledger=load(LEDGER); decisions=load(OPEN_DECISIONS)
    if a.get("stage")!="STAGE88_TERMS_ACCEPTANCE_REMOTE_APPLY_EXECUTION_SEAL" or a.get("baseline_main_sha")!="f69ef0a74f03f98e767cd6dc3d84948bc4fac7ee": fail("Stage88 identity/baseline drift")
    up=a.get("upstream_stage87_green",{})
    expected={"merged_main_sha":"f69ef0a74f03f98e767cd6dc3d84948bc4fac7ee","green_head_sha":"f8e0e4447c556f2068e434c35334a3534d5de3aa","dedicated_ci_run_id":33000280847,"dedicated_ci_conclusion":"success","flutter_quality_gate_run_id":33000280670,"flutter_quality_gate_conclusion":"success","artifact_id":9618242758,"artifact_digest":"sha256:cef5c19cc903d505eda47e0c203dccfe3941884def95ce7d1f304b118fb8f3aa","artifact_is_remote_apply_evidence":False,"artifact_is_legal_or_gate_evidence":False}
    for k,v in expected.items():
        if up.get(k)!=v: fail(f"Stage87 GREEN provenance drift:{k}")
    if s87.get("stage")!="STAGE87_TERMS_ACCEPTANCE_REMOTE_APPLY_GATE_PREPARATION":fail("Stage87 authority drift")
    if "execution-seal stage" not in s87.get("next_after_green",{}).get("safe_internal_work",""):fail("Stage87 does not authorize Stage88 seal")
    pins=a.get("sealed_inputs",{})
    for key,path,expected_blob in (("stage87_authority_blob",STAGE87,"b844aa81e39ac6d6feb8b2916dc4af14ed2e0219"),("stage87_gate_contract_blob",GATE,"80e70b9bdfbb2a70a1b6c67c5b8af781c118aaef"),("migration_blob",MIGRATION,"a9a77ebbf61f464e5549f338362cdd3a59df8df1"),("migration_ledger_blob",LEDGER,"427f83c2ae6c8430cf9d050380e6f1cfa15c2c87"),("execution_plan_blob",PLAN,"5c1a138a416baaf3daef416d370e645435b49fab")):
        if pins.get(key)!=expected_blob or blob(path)!=expected_blob:fail(f"sealed input drift:{key}")
    receipt=a.get("fresh_pre_seal_remote_receipt",{})
    for k,v in {"observed_at_utc":"2026-08-26T18:35:53.356463Z","remote_migration_count":67,"target_remote_migration_present":False,"auth_users":0,"organizations":0,"organization_members":0,"terms_registry_exists":False,"acceptance_ledger_exists":False,"current_terms_rpc_exists":False,"accept_terms_rpc_exists":False,"acceptance_gate_rpc_exists":False,"is_org_member_helper_exists":True,"remote_mutation_performed":False}.items():
        if receipt.get(k)!=v:fail(f"fresh receipt drift:{k}")
    seal=a.get("execution_seal",{})
    for k,v in {"target_migration_name":"stage85_terms_acceptance_registry_ledger","target_migration_blob":"a9a77ebbf61f464e5549f338362cdd3a59df8df1","execution_plan_blob":"5c1a138a416baaf3daef416d370e645435b49fab","migration_ledger_state":"repo_only","remote_apply_count":0,"remote_version":None,"stage88_executes_remote_apply":False,"later_one_shot_execution_allowed_only_after_stage88_merge":True,"later_execution_requires_fresh_post_merge_preconditions":True,"later_execution_must_use_apply_migration_semantics":True,"later_execution_must_reconcile_remote_result_before_retry":True,"later_execution_blind_retry_allowed":False,"automatic_destructive_rollback_allowed":False}.items():
        if seal.get(k)!=v:fail(f"execution seal drift:{k}")
    ps=p.get("execution_seal",{})
    if ps.get("stage88_executes_remote_apply") is not False or ps.get("future_execution_is_one_shot") is not True or ps.get("future_apply_result_must_be_reconciled_before_any_retry") is not True or ps.get("future_apply_ambiguous_result_blind_retry_allowed") is not False:fail("execution plan one-shot/ambiguity policy drift")
    repo=[r for r in ledger.get("declared_divergences",[]) if isinstance(r,dict) and r.get("direction")=="repo_only"]
    if len(repo)!=1 or repo[0].get("name")!="stage85_terms_acceptance_registry_ledger":fail("target must remain unique repo-only migration")
    unresolved=decisions.get("unresolved"); target=next((r for r in unresolved if isinstance(r,dict) and r.get("id")=="TERMS_ACCEPTANCE_VERSIONING"),None) if isinstance(unresolved,list) else None
    if not isinstance(target,dict) or target.get("state")!="OPEN":fail("TERMS_ACCEPTANCE_VERSIONING must remain OPEN")
    t=TERMS.read_text(encoding="utf-8")
    if "DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE" not in t or "legal_terms_of_use = BLOCKED" not in t:fail("Terms draft/legal gate drift")
    if any(v is not False for v in a.get("hard_boundaries",{}).values()):fail("Stage88 hard boundary drift")
    if a.get("gates",{}).get("stage88_remote_apply_execution")!="FORBIDDEN_UNTIL_STAGE88_MERGED_AND_FRESH_PRECONDITIONS_RECHECKED":fail("Stage88 execution gate drift")
    try:src=BUILDER.read_text(encoding="utf-8"); tree=ast.parse(src)
    except (OSError,SyntaxError) as e:fail(f"builder invalid:{type(e).__name__}")
    for n in ast.walk(tree):
        roots=[]
        if isinstance(n,ast.Import): roots += [x.name.split('.')[0] for x in n.names]
        elif isinstance(n,ast.ImportFrom) and n.module: roots.append(n.module.split('.')[0])
        if any(r in FORBIDDEN_IMPORTS for r in roots):fail("builder imports remote execution module")
    wf=WORKFLOW.read_text(encoding="utf-8"); low=wf.lower()
    for token in FORBIDDEN_WORKFLOW:
        if token in low:fail(f"Stage88 workflow contains forbidden token:{token}")
    for marker in ("permissions:\n  contents: read","blackgold/stage88-terms-acceptance-remote-apply-execution-seal","Verify Stage88 Terms acceptance remote apply execution seal","Build deterministic Stage88 seal packet twice","ONE_SHOT_EXECUTION_SEALED=true","REMOTE_MIGRATION_APPLIED=false","SUPABASE_MUTATION=false","LEGAL_TERMS_GATE_READY=false"):
        if marker not in wf:fail(f"workflow marker missing:{marker}")
    print("STAGE88_TERMS_ACCEPTANCE_REMOTE_APPLY_EXECUTION_SEAL_GUARD=PASS")
    print("ONE_SHOT_EXECUTION_SEALED=true")
    print("REMOTE_MIGRATION_APPLIED=false")
    print("SUPABASE_MUTATION=false")
    print("LEGAL_TERMS_GATE_READY=false")

if __name__=="__main__":main()
