-- Execute este arquivo no Supabase > SQL Editor.
-- As tabelas são acessadas pelo FastAPI usando uma chave secreta guardada no servidor.
-- Não coloque SUPABASE_SECRET_KEY no HTML/JavaScript.

create table if not exists public.players (
    identifier text primary key
        check (identifier ~ '^[A-Z]{3}-[0-9]{3}$'),
    created_at timestamptz not null default now()
);

create table if not exists public.player_used_powers (
    identifier text not null references public.players(identifier) on delete cascade,
    power_key text not null
        check (power_key in ('peek', 'freeze', 'hint', 'shield', 'turbo', 'time')),
    used_at timestamptz not null default now(),
    primary key (identifier, power_key)
);

create table if not exists public.phase_results (
    identifier text not null references public.players(identifier) on delete cascade,
    phase smallint not null check (phase between 1 and 7),
    score integer not null default 0 check (score >= 0),
    elapsed_seconds integer not null check (elapsed_seconds >= 1),
    moves integer not null default 0 check (moves >= 0),
    won boolean not null default false,
    completed_at timestamptz not null default now(),
    primary key (identifier, phase)
);

create index if not exists phase_results_ranking_idx
    on public.phase_results (score desc, elapsed_seconds asc);

-- Ranking geral: uma linha por jogador, somando todas as fases registradas.
create or replace view public.general_ranking
with (security_invoker = true) as
select
    p.identifier,
    count(r.phase)::integer as phases_played,
    count(r.phase) filter (where r.won)::integer as phases_won,
    coalesce(sum(r.score), 0)::bigint as total_score,
    coalesce(sum(r.elapsed_seconds), 0)::bigint as total_seconds
from public.players p
left join public.phase_results r on r.identifier = p.identifier
group by p.identifier;

-- Habilita RLS e remove acesso direto das chaves públicas.
-- O FastAPI usa a chave secreta apenas no servidor.
alter table public.players enable row level security;
alter table public.player_used_powers enable row level security;
alter table public.phase_results enable row level security;

revoke all on table public.players from anon, authenticated;
revoke all on table public.player_used_powers from anon, authenticated;
revoke all on table public.phase_results from anon, authenticated;
revoke all on table public.general_ranking from anon, authenticated;

grant all on table public.players to service_role;
grant all on table public.player_used_powers to service_role;
grant all on table public.phase_results to service_role;
grant select on table public.general_ranking to service_role;
