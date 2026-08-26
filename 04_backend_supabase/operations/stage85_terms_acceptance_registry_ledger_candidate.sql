-- FitNexus Coach BlackGold — Stage85 candidate only.
--
-- This file is NOT a migration and MUST NOT be executed from operations/.
-- It is the exact repository-first candidate for a later promotion lifecycle after
-- Stage85 preparation is merged and revalidated. Stage85 itself performs no remote DDL,
-- registers no Terms artifact and collects no real acceptance.
--
-- Canonical target remains OPEN: TERMS_ACCEPTANCE_VERSIONING.
-- Draft Terms remain DRAFT_UNREVIEWED_NOT_PUBLISHED_NOT_LEGAL_EVIDENCE.
--
-- Failure classes:
--   BGF-STAGE85-DRAFT-TERMS-REGISTRATION-841
--   BGF-STAGE85-MUTABLE-TERMS-REGISTRY-842
--   BGF-STAGE85-FORGED-OR-STALE-DIGEST-ACCEPTANCE-843
--   BGF-STAGE85-UNAUTHENTICATED-ACCEPTANCE-844
--   BGF-STAGE85-CROSS-TENANT-ACCEPTANCE-845
--   BGF-STAGE85-NON_IDEMPOTENT-ACCEPTANCE-846
--   BGF-STAGE85-MUTABLE-ACCEPTANCE-HISTORY-847
--   BGF-STAGE85-NO-CURRENT-TERMS-FAIL-OPEN-848
--   BGF-STAGE85-PREMATURE-CANDIDATE-EXECUTION-849
--   BGF-STAGE85-TERMS-ACCEPTANCE-MIGRATION-CANDIDATE-GUARD-850

-- Exact precondition: Stage84 proved these surfaces absent. Promotion must fail closed
-- if some other path materialized them before the canonical migration lifecycle.
do $$
begin
  if to_regclass('private.terms_document_registry') is not null
     or to_regclass('private.terms_acceptance_ledger') is not null
     or to_regprocedure('public.get_current_terms_v1(text)') is not null
     or to_regprocedure('public.accept_current_terms_v1(uuid,text,text,text,text,text)') is not null
     or to_regprocedure('public.get_my_terms_acceptance_gate_v1(uuid,text)') is not null then
    raise exception using errcode = 'P0001',
      message = 'STAGE85_TERMS_ACCEPTANCE_SURFACE_ALREADY_EXISTS';
  end if;

  if to_regprocedure('private.is_org_member(uuid)') is null then
    raise exception using errcode = 'P0001',
      message = 'STAGE85_REQUIRED_ORG_MEMBERSHIP_AUTHORITY_MISSING';
  end if;
end;
$$;

create table private.terms_document_registry (
  document_kind text not null,
  version text not null,
  sha256 text not null,
  effective_at timestamptz not null,
  public_url text not null,
  approval_reference text not null,
  publication_reference text not null,
  created_at timestamptz not null default now(),
  constraint terms_document_registry_pk primary key (document_kind, version),
  constraint terms_document_registry_kind_sha256_uk unique (document_kind, sha256),
  constraint terms_document_registry_kind_version_sha256_uk unique (document_kind, version, sha256),
  constraint terms_document_registry_kind_format_ck
    check (document_kind = btrim(document_kind) and document_kind ~ '^[a-z0-9_]{2,64}$'),
  constraint terms_document_registry_version_ck
    check (version = btrim(version) and char_length(version) between 1 and 120),
  constraint terms_document_registry_sha256_ck
    check (sha256 ~ '^[0-9a-f]{64}$'),
  constraint terms_document_registry_public_url_ck
    check (public_url = btrim(public_url) and public_url ~ '^https://[^[:space:]]+$'),
  constraint terms_document_registry_approval_reference_ck
    check (approval_reference = btrim(approval_reference) and char_length(approval_reference) between 1 and 500),
  constraint terms_document_registry_publication_reference_ck
    check (publication_reference = btrim(publication_reference) and char_length(publication_reference) between 1 and 500)
);

comment on table private.terms_document_registry is
  'Immutable metadata registry for independently approved and published Terms artifacts. Presence of a row requires real approval/publication authority outside this migration.';

create or replace function private.reject_terms_document_registry_mutation()
returns trigger
language plpgsql
security definer
set search_path to ''
as $$
begin
  raise exception using errcode = '42501',
    message = 'TERMS_DOCUMENT_REGISTRY_IS_IMMUTABLE';
end;
$$;

create trigger terms_document_registry_immutable_trg
before update or delete on private.terms_document_registry
for each row execute function private.reject_terms_document_registry_mutation();

alter table private.terms_document_registry enable row level security;
revoke all on table private.terms_document_registry from public, anon, authenticated;

create table private.terms_acceptance_ledger (
  acceptance_id uuid primary key default extensions.gen_random_uuid(),
  actor_user_id uuid not null,
  organization_id uuid not null,
  document_kind text not null,
  terms_version text not null,
  terms_sha256 text not null,
  accepted_at timestamptz not null default now(),
  acceptance_surface text not null,
  idempotency_key text not null,
  created_at timestamptz not null default now(),
  constraint terms_acceptance_registry_fk
    foreign key (document_kind, terms_version, terms_sha256)
    references private.terms_document_registry(document_kind, version, sha256)
    on update restrict on delete restrict,
  constraint terms_acceptance_idempotency_uk
    unique (actor_user_id, organization_id, document_kind, idempotency_key),
  constraint terms_acceptance_kind_format_ck
    check (document_kind = btrim(document_kind) and document_kind ~ '^[a-z0-9_]{2,64}$'),
  constraint terms_acceptance_version_ck
    check (terms_version = btrim(terms_version) and char_length(terms_version) between 1 and 120),
  constraint terms_acceptance_sha256_ck
    check (terms_sha256 ~ '^[0-9a-f]{64}$'),
  constraint terms_acceptance_surface_ck
    check (acceptance_surface = btrim(acceptance_surface) and char_length(acceptance_surface) between 1 and 120),
  constraint terms_acceptance_idempotency_key_ck
    check (idempotency_key = btrim(idempotency_key) and char_length(idempotency_key) between 8 and 200)
);

comment on table private.terms_acceptance_ledger is
  'Append-only evidence that an authenticated actor accepted one exact registered Terms version/digest for one organization.';

create index terms_acceptance_actor_current_lookup_idx
  on private.terms_acceptance_ledger
  (organization_id, actor_user_id, document_kind, terms_version, terms_sha256, accepted_at desc);

create or replace function private.reject_terms_acceptance_history_mutation()
returns trigger
language plpgsql
security definer
set search_path to ''
as $$
begin
  raise exception using errcode = '42501',
    message = 'TERMS_ACCEPTANCE_HISTORY_IS_APPEND_ONLY';
end;
$$;

create trigger terms_acceptance_ledger_append_only_trg
before update or delete on private.terms_acceptance_ledger
for each row execute function private.reject_terms_acceptance_history_mutation();

alter table private.terms_acceptance_ledger enable row level security;
revoke all on table private.terms_acceptance_ledger from public, anon, authenticated;

-- Public resolver exposes only the latest already-effective registry row. There is no
-- draft fallback and there is deliberately no mutable is_current flag.
create or replace function public.get_current_terms_v1(p_document_kind text)
returns table (
  document_kind text,
  terms_version text,
  terms_sha256 text,
  effective_at timestamptz,
  public_url text
)
language plpgsql
stable
security definer
set search_path to ''
as $$
declare
  v_kind text := btrim(coalesce(p_document_kind, ''));
begin
  if v_kind !~ '^[a-z0-9_]{2,64}$' then
    raise exception using errcode = '22023', message = 'TERMS_DOCUMENT_KIND_INVALID';
  end if;

  return query
  select r.document_kind, r.version, r.sha256, r.effective_at, r.public_url
  from private.terms_document_registry r
  where r.document_kind = v_kind
    and r.effective_at <= now()
  order by r.effective_at desc, r.created_at desc, r.version desc
  limit 1;

  if not found then
    raise exception using errcode = 'P0001',
      message = 'CURRENT_APPROVED_PUBLISHED_TERMS_NOT_AVAILABLE';
  end if;
end;
$$;

revoke all on function public.get_current_terms_v1(text) from public, anon, authenticated;
grant execute on function public.get_current_terms_v1(text) to anon, authenticated;

-- Acceptance is server-authoritative: actor identity comes from auth.uid(), tenant
-- membership is checked by the existing private authority, and client version/digest
-- are only optimistic concurrency expectations—not authority.
create or replace function public.accept_current_terms_v1(
  p_organization_id uuid,
  p_document_kind text,
  p_expected_version text,
  p_expected_sha256 text,
  p_acceptance_surface text,
  p_idempotency_key text
)
returns uuid
language plpgsql
security definer
set search_path to ''
as $$
declare
  v_uid uuid := auth.uid();
  v_kind text := btrim(coalesce(p_document_kind, ''));
  v_expected_version text := btrim(coalesce(p_expected_version, ''));
  v_expected_sha256 text := btrim(coalesce(p_expected_sha256, ''));
  v_surface text := btrim(coalesce(p_acceptance_surface, ''));
  v_idempotency text := btrim(coalesce(p_idempotency_key, ''));
  v_current_version text;
  v_current_sha256 text;
  v_acceptance_id uuid;
  v_existing record;
begin
  if v_uid is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if p_organization_id is null or not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORGANIZATION_ACCESS_DENIED';
  end if;
  if v_kind !~ '^[a-z0-9_]{2,64}$'
     or v_expected_version = ''
     or v_expected_sha256 !~ '^[0-9a-f]{64}$'
     or char_length(v_surface) not between 1 and 120
     or char_length(v_idempotency) not between 8 and 200 then
    raise exception using errcode = '22023', message = 'TERMS_ACCEPTANCE_INPUT_INVALID';
  end if;

  select r.version, r.sha256
    into v_current_version, v_current_sha256
  from private.terms_document_registry r
  where r.document_kind = v_kind
    and r.effective_at <= now()
  order by r.effective_at desc, r.created_at desc, r.version desc
  limit 1;

  if v_current_version is null then
    raise exception using errcode = 'P0001',
      message = 'CURRENT_APPROVED_PUBLISHED_TERMS_NOT_AVAILABLE';
  end if;
  if v_expected_version <> v_current_version or v_expected_sha256 <> v_current_sha256 then
    raise exception using errcode = '40001',
      message = 'TERMS_VERSION_OR_DIGEST_STALE_OR_FORGED';
  end if;

  insert into private.terms_acceptance_ledger (
    actor_user_id,
    organization_id,
    document_kind,
    terms_version,
    terms_sha256,
    acceptance_surface,
    idempotency_key
  ) values (
    v_uid,
    p_organization_id,
    v_kind,
    v_current_version,
    v_current_sha256,
    v_surface,
    v_idempotency
  )
  on conflict (actor_user_id, organization_id, document_kind, idempotency_key)
  do nothing
  returning acceptance_id into v_acceptance_id;

  if v_acceptance_id is not null then
    return v_acceptance_id;
  end if;

  select l.acceptance_id, l.terms_version, l.terms_sha256, l.acceptance_surface
    into v_existing
  from private.terms_acceptance_ledger l
  where l.actor_user_id = v_uid
    and l.organization_id = p_organization_id
    and l.document_kind = v_kind
    and l.idempotency_key = v_idempotency;

  if v_existing.acceptance_id is null then
    raise exception using errcode = 'P0001', message = 'TERMS_ACCEPTANCE_IDEMPOTENCY_RECONCILIATION_FAILED';
  end if;
  if v_existing.terms_version <> v_current_version
     or v_existing.terms_sha256 <> v_current_sha256
     or v_existing.acceptance_surface <> v_surface then
    raise exception using errcode = '22023',
      message = 'IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_ACCEPTANCE';
  end if;

  return v_existing.acceptance_id;
end;
$$;

revoke all on function public.accept_current_terms_v1(uuid,text,text,text,text,text) from public, anon, authenticated;
grant execute on function public.accept_current_terms_v1(uuid,text,text,text,text,text) to authenticated;

-- Version-aware gate for the signed-in actor. It fails closed if no approved/published
-- current Terms row exists and never treats the repository draft as customer authority.
create or replace function public.get_my_terms_acceptance_gate_v1(
  p_organization_id uuid,
  p_document_kind text
)
returns table (
  document_kind text,
  terms_version text,
  terms_sha256 text,
  effective_at timestamptz,
  public_url text,
  accepted boolean,
  accepted_at timestamptz
)
language plpgsql
stable
security definer
set search_path to ''
as $$
declare
  v_uid uuid := auth.uid();
  v_kind text := btrim(coalesce(p_document_kind, ''));
  v_version text;
  v_sha256 text;
  v_effective_at timestamptz;
  v_public_url text;
  v_accepted_at timestamptz;
begin
  if v_uid is null then
    raise exception using errcode = '42501', message = 'AUTH_REQUIRED';
  end if;
  if p_organization_id is null or not private.is_org_member(p_organization_id) then
    raise exception using errcode = '42501', message = 'ORGANIZATION_ACCESS_DENIED';
  end if;
  if v_kind !~ '^[a-z0-9_]{2,64}$' then
    raise exception using errcode = '22023', message = 'TERMS_DOCUMENT_KIND_INVALID';
  end if;

  select r.version, r.sha256, r.effective_at, r.public_url
    into v_version, v_sha256, v_effective_at, v_public_url
  from private.terms_document_registry r
  where r.document_kind = v_kind
    and r.effective_at <= now()
  order by r.effective_at desc, r.created_at desc, r.version desc
  limit 1;

  if v_version is null then
    raise exception using errcode = 'P0001',
      message = 'CURRENT_APPROVED_PUBLISHED_TERMS_NOT_AVAILABLE';
  end if;

  select l.accepted_at
    into v_accepted_at
  from private.terms_acceptance_ledger l
  where l.actor_user_id = v_uid
    and l.organization_id = p_organization_id
    and l.document_kind = v_kind
    and l.terms_version = v_version
    and l.terms_sha256 = v_sha256
  order by l.accepted_at desc, l.created_at desc
  limit 1;

  return query
  select v_kind, v_version, v_sha256, v_effective_at, v_public_url,
         (v_accepted_at is not null), v_accepted_at;
end;
$$;

revoke all on function public.get_my_terms_acceptance_gate_v1(uuid,text) from public, anon, authenticated;
grant execute on function public.get_my_terms_acceptance_gate_v1(uuid,text) to authenticated;
