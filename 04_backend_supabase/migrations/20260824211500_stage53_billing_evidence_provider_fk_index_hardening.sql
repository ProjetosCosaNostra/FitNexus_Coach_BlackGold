-- STAGE53 OPERATIONS CANDIDATE ONLY — DO NOT APPLY DIRECTLY
-- Purpose: close the Supabase performance lint for the provider_code foreign
-- key on private.billing_provider_external_evidence without changing data,
-- privileges, billing authority, provider state, or launch authority.
--
-- The existing primary key is (scope, provider_code, evidence_version), so it
-- does not provide a provider_code-leading access path for the standalone
-- provider_code foreign key. A dedicated btree index satisfies that boundary.
--
-- BGF-STAGE53-UNINDEXED-BILLING-EVIDENCE-PROVIDER-FK-494
-- BGF-STAGE53-INDEX-DROP-WITHOUT-WORKLOAD-EVIDENCE-496
-- BGF-STAGE53-CANDIDATE-DIRECT-APPLY-497

create index if not exists billing_provider_external_evidence_provider_code_idx
  on private.billing_provider_external_evidence (provider_code);
