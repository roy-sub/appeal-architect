-- Migration 003: the profile row a new user needs, created automatically.
--
-- Entitlement is read from profiles.plan_tier, so a user with no profile row
-- would read as no tier at all. A trigger creates the row at sign-up rather
-- than the application remembering to -- the application forgetting is exactly
-- the bug that would gate a paying user out of their own letter.

begin;

alter table profiles
  add constraint profiles_plan_tier_known
  check (plan_tier in ('free', 'appeal_package', 'subscription'));

create or replace function create_profile_for_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (user_id, plan_tier)
  values (new.id, 'free')
  on conflict (user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function create_profile_for_new_user();

-- Backfill anyone who signed up before this migration.
insert into public.profiles (user_id, plan_tier)
select id, 'free' from auth.users
on conflict (user_id) do nothing;

commit;
