from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="FlexyFins - Networked Mission Control")


class EventEnvelope(BaseModel):
    mission_id: str
    event_type: str
    status: str
    proof_ref: str | None = None
    meta: dict | None = None


# In-memory store for now. Replace with DB (Postgres/SQLite) when ready.
EVENT_STORE: list[dict] = []


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/gd/ingest")
async def ingest(envelope: EventEnvelope):
    EVENT_STORE.append(envelope.model_dump())
    return {"ok": True, "stored": len(EVENT_STORE)}
