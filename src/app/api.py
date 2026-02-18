import re
import html
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, field_validator
from src.app.ops import EVIDENCE_TIERS, RUNBOOKS
from src.app.store import mission_latest

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


@app.get("/api/gd/proof-matrix")
def proof_matrix(limit: int = 200):
    """
    Mission financial maturity view.
    """
    items = mission_latest(limit=limit)
    out = []
    for it in items:
        tier = int(EVIDENCE_TIERS.get(it.get("event_type") or "", 0))
        out.append(
            {
                "mission_id": it.get("mission_id"),
                "last_event_type": it.get("event_type"),
                "last_status": it.get("status"),
                "tier": tier,
                "proof_ref": it.get("proof_ref"),
                "ts": it.get("ts"),
            }
        )
    return {"items": out}


@app.get("/api/gd/settlement-score")
def settlement_score(limit: int = 200):
    """
    Score per mission based on best evidence seen.
    """
    items = mission_latest(limit=limit)
    scored = []
    for it in items:
        tier = int(EVIDENCE_TIERS.get(it.get("event_type") or "", 0))
        # 25 points per tier
        score = tier * 25
        scored.append(
            {
                "mission_id": it.get("mission_id"),
                "tier": tier,
                "score": score,
                "last_event_type": it.get("event_type"),
                "ts": it.get("ts"),
            }
        )
    return {"items": scored}


@app.get("/api/gd/runbook")
def runbook(reason_code: str):
    reason_code = (reason_code or "").strip()
    if not reason_code:
        return {"ok": False, "error": "reason_code required"}
    if reason_code not in RUNBOOKS:
        return {"ok": False, "error": "unknown reason_code", "known": sorted(RUNBOOKS.keys())}
    title, steps = RUNBOOKS[reason_code]
    return {"ok": True, "reason_code": reason_code, "title": title, "steps": steps}

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
