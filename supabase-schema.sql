create table if not exists public.compass_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  profile_json jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.compass_profiles enable row level security;

create policy "Users can view their own Compass profile"
on public.compass_profiles
for select
to authenticated
using ((select auth.uid()) = user_id);

create policy "Users can insert their own Compass profile"
on public.compass_profiles
for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy "Users can update their own Compass profile"
on public.compass_profiles
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);
