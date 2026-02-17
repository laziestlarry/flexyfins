from fastapi import FastAPI
from pydantic import BaseModel

from src.app.store import ensure_tables, insert_envelope, summary_counts


app = FastAPI(title="FlexyFins - Networked Mission Control")


class EventEnvelope(BaseModel):
    mission_id: str
    event_type: str
    status: str
    proof_ref: str | None = None
    meta: dict | None = None


# Ensure tables exist on import. In Cloud Run this will run once per cold-start.
ensure_tables()


@app.get("/")
async def index():
    return {
        "ok": True,
        "counts": summary_counts(),
    }


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/gd/ingest")
async def ingest(envelope: EventEnvelope):
    env = envelope.model_dump()
    insert_envelope(env)
    counts = summary_counts()
    return {"ok": True, "counts": counts}
