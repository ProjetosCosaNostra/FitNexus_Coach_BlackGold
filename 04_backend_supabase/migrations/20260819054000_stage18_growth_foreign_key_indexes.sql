create index if not exists growth_attribution_first_actor_user_id_idx
  on private.growth_attribution(first_actor_user_id)
  where first_actor_user_id is not null;

create index if not exists growth_attribution_last_actor_user_id_idx
  on private.growth_attribution(last_actor_user_id)
  where last_actor_user_id is not null;
