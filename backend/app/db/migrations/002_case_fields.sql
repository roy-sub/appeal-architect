-- Migration 002: fields the case row needs that 001 did not carry.
--
-- `filer` moved onto the case because who is filing is something the user tells
-- us directly rather than something extracted from a letter, and it changes a
-- required element (a representative must attach authorisation).
--
-- `final_adverse_date` is what makes the external-review step datable. Until the
-- insurer gives its final internal answer there is nothing to count from, and
-- the engine refuses to invent a trigger -- so this column being null is a
-- meaningful state, not a missing value.

begin;

create type filer_kind as enum ('member', 'authorized_rep', 'provider');

alter table cases
  add column filer filer_kind not null default 'member',
  add column final_adverse_date date;

comment on column cases.final_adverse_date is
  'Date of the insurer''s final internal denial. Null until the internal appeal '
  'is answered, which is why the external-review step is undated before then.';

commit;
