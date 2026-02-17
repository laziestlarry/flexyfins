import re
import html
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, field_validator

from src.app.store import ensure_tables, insert_envelope, recent_envelopes, summary_counts

app = FastAPI(title="FlexyFins - Networked Mission Control")

SUCCESS_STATUSES = {"VERIFIED", "COMPLETED", "SETTLED", "OK"}


class EventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_id: str
    event_type: str
    status: str
    proof_ref: Optional[str] = None
    meta: Dict[str, Any] = {}

    @field_validator("mission_id")
    @classmethod
    def mission_id_is_val(cls, v: str) -> str:
        if not re.fullmatch(r"VAL-\d+", v):
            raise ValueError("mission_id must match VAL-<digits>")
        return v

    @field_validator("status")
    @classmethod
    def status_upper(cls, v: str) -> str:
        return v.upper()


# Ensure tables exist on import. In Cloud Run this runs once per cold-start.
ensure_tables()


@app.get("/")
async def index():
    return {"ok": True, "counts": summary_counts()}


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/gd/ingest")
async def ingest(envelope: EventEnvelope):
    try:
        inserted = insert_envelope(envelope.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"ok": True, "inserted": inserted, "counts": summary_counts()}


@app.get("/api/gd/events")
async def events(limit: int = 25):
    return {"ok": True, "items": recent_envelopes(limit=limit)}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    counts = summary_counts()
    items = recent_envelopes(limit=25)

    rows = []
    for i in items:
        rows.append(
            f"<tr><td>{html.escape(str(i.get('ts', '')))}</td>"
            f"<td>{html.escape(i.get('mission_id', ''))}</td>"
            f"<td>{html.escape(i.get('event_type', ''))}</td>"
            f"<td>{html.escape(i.get('status', ''))}</td>"
            f"<td>{html.escape(i.get('proof_ref', '') or '')}</td>"
            f"<td>{html.escape(str(i.get('meta', '') or ''))}</td></tr>"
        )

    html_doc = f"""
    <html><head><title>FlexyFins Dashboard</title></head>
    <body>
      <h1>FlexyFins Dashboard</h1>
      <p>Total: {counts['total']} OK: {counts['ok']} FAIL: {counts['fail']}</p>
      <table border='1' cellpadding='4'>
        <thead><tr><th>ts</th><th>mission</th><th>type</th><th>status</th><th>proof</th><th>meta</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </body></html>
    """

    return HTMLResponse(content=html_doc, media_type="text/html")
