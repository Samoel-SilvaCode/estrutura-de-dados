import os
import re
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "").strip()
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if origin.strip()
]

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise RuntimeError(
        "Configure SUPABASE_URL e SUPABASE_SECRET_KEY nas variáveis de ambiente."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

app = FastAPI(
    title="Contadinho API",
    version="0.1.0",
    description="API Python para progresso, poderes e ranking do Contadinho.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

PHASE_COUNT = 7
ALLOWED_POWERS = {"peek", "freeze", "hint", "shield", "turbo", "time"}
IDENTIFIER_RE = re.compile(r"^[A-Z]{3}-\d{3}$")


class PlayerCreate(BaseModel):
    identifier: str = Field(pattern=r"^[A-Z]{3}-\d{3}$")


class PhaseResult(BaseModel):
    score: int = Field(ge=0, le=1_000_000)
    elapsed_seconds: int = Field(ge=1, le=24 * 60 * 60)
    moves: int = Field(ge=0, le=100_000)
    won: bool


def normalize_identifier(identifier: str) -> str:
    value = identifier.strip().upper()
    if not IDENTIFIER_RE.fullmatch(value):
        raise HTTPException(
            status_code=422,
            detail="Identificação inválida. Use o formato ABC-123.",
        )
    return value


def player_exists(identifier: str) -> bool:
    response = (
        supabase.table("players")
        .select("identifier")
        .eq("identifier", identifier)
        .limit(1)
        .execute()
    )
    return bool(response.data)


@app.get("/")
def root():
    return {"service": "Contadinho API", "docs": "/docs", "status": "online"}


@app.get("/health")
def health():
    # Este endpoint verifica que o processo FastAPI está respondendo.
    return {"status": "ok"}


@app.post("/api/players")
def register_player(payload: PlayerCreate):
    identifier = normalize_identifier(payload.identifier)
    try:
        supabase.table("players").upsert(
            {"identifier": identifier}, on_conflict="identifier"
        ).execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível registrar o jogador.") from exc

    return get_player_progress(identifier)


@app.get("/api/players/{identifier}/progress")
def get_player_progress(
    identifier: str = Path(..., description="Identificação no formato ABC-123")
):
    identifier = normalize_identifier(identifier)
    try:
        if not player_exists(identifier):
            raise HTTPException(status_code=404, detail="Jogador não encontrado.")

        powers_response = (
            supabase.table("player_used_powers")
            .select("power_key")
            .eq("identifier", identifier)
            .execute()
        )
        phases_response = (
            supabase.table("phase_results")
            .select("phase, score, elapsed_seconds, moves, won, completed_at")
            .eq("identifier", identifier)
            .order("phase")
            .execute()
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Erro ao consultar o progresso.") from exc

    phases = phases_response.data or []
    completed_phases = [int(row["phase"]) for row in phases]
    next_phase = min(PHASE_COUNT + 1, (max(completed_phases) + 1) if completed_phases else 1)

    return {
        "identifier": identifier,
        "completed_phases": completed_phases,
        "next_phase": next_phase,
        "used_powers": [row["power_key"] for row in (powers_response.data or [])],
        "results": phases,
    }


@app.post("/api/players/{identifier}/powers/{power_key}/use")
def use_power(
    identifier: str = Path(...),
    power_key: str = Path(...),
):
    identifier = normalize_identifier(identifier)
    if power_key not in ALLOWED_POWERS:
        raise HTTPException(status_code=422, detail="Poder desconhecido.")
    if not player_exists(identifier):
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    # A chave primária (identifier, power_key) impede dois usos do mesmo poder.
    try:
        supabase.table("player_used_powers").insert(
            {"identifier": identifier, "power_key": power_key}
        ).execute()
    except Exception as exc:
        # A restrição UNIQUE/PRIMARY KEY do banco também protege contra chamadas simultâneas.
        try:
            already_used = (
                supabase.table("player_used_powers")
                .select("power_key")
                .eq("identifier", identifier)
                .eq("power_key", power_key)
                .limit(1)
                .execute()
            )
            if already_used.data:
                raise HTTPException(status_code=409, detail="Este poder já foi usado nesta campanha.")
        except HTTPException:
            raise
        except Exception:
            pass
        raise HTTPException(status_code=502, detail="Não foi possível registrar o uso do poder.") from exc

    return {"identifier": identifier, "power_key": power_key, "used": True}


@app.post("/api/players/{identifier}/phases/{phase}/finish")
def finish_phase(
    payload: PhaseResult,
    identifier: str = Path(...),
    phase: int = Path(..., ge=1, le=PHASE_COUNT),
):
    identifier = normalize_identifier(identifier)
    if not player_exists(identifier):
        raise HTTPException(status_code=404, detail="Jogador não encontrado.")

    try:
        existing = (
            supabase.table("phase_results")
            .select("phase")
            .eq("identifier", identifier)
            .eq("phase", phase)
            .limit(1)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=409, detail="Esta fase já foi encerrada e não pode ser repetida.")

        if phase > 1:
            previous = (
                supabase.table("phase_results")
                .select("phase")
                .eq("identifier", identifier)
                .eq("phase", phase - 1)
                .limit(1)
                .execute()
            )
            if not previous.data:
                raise HTTPException(status_code=409, detail="Conclua ou encerre a fase anterior primeiro.")

        supabase.table("phase_results").insert(
            {
                "identifier": identifier,
                "phase": phase,
                "score": payload.score,
                "elapsed_seconds": payload.elapsed_seconds,
                "moves": payload.moves,
                "won": payload.won,
            }
        ).execute()
    except HTTPException:
        raise
    except Exception as exc:
        # A chave primária (identifier, phase) impede registro duplicado.
        raise HTTPException(status_code=409, detail="Não foi possível registrar a fase. Verifique se ela já foi encerrada.") from exc

    return {
        "saved": True,
        "identifier": identifier,
        "phase": phase,
        "won": payload.won,
        "next_phase": min(PHASE_COUNT + 1, phase + 1),
    }


@app.get("/api/ranking")
def get_ranking():
    try:
        response = (
            supabase.table("general_ranking")
            .select("identifier, phases_played, phases_won, total_score, total_seconds")
            .order("total_score", desc=True)
            .order("total_seconds")
            .limit(100)
            .execute()
        )
        return {"ranking": response.data or []}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível carregar o ranking.") from exc
