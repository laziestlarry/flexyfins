from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from emitters.flexyfins import emit_event

APP_NAME = "GOLDEN_DELIVERY"
FLEXYFINS_URL = os.getenv("FLEXYFINS_URL", "").strip()

app = FastAPI(title=APP_NAME)


class RunPayload(BaseModel):
    mission_id: str = Field(..., description="VAL mission id")
    playbook: str = Field(default="chimera")
    mode: str = Field(default="LIVE")
    run_id: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/api/health")
def health():
    return {"ok": True, "app": APP_NAME, "ts": _utc_now(), "flexyfins_configured": bool(FLEXYFINS_URL)}


@app.post("/api/gd/run")
def run_mission(payload: RunPayload):
    """
    Scheduler-triggerable mission run stub.
    Replace internals with your real playbook runner as you integrate.
    """
    mission_id = payload.mission_id.strip()
    if not mission_id.startswith("VAL-"):
        raise HTTPException(status_code=400, detail="mission_id must start with VAL-")

    # Emit MISSION_STARTED
    emit_event(
        {
            "mission_id": mission_id,
            "event_type": "MISSION_STARTED",
            "status": "VERIFIED",
            "proof_ref": f"run:{payload.run_id or 'manual'}",
            "meta": {
                "mission_name": APP_NAME,
                "playbook": payload.playbook,
                "mode": payload.mode,
                "ts": _utc_now(),
            },
        }
    )

    # TODO: integrate real playbook execution here (listing, tagging, delivery, proof mint)
    # For now, emit PROOF_MINTED as placeholder completion signal
    emit_event(
        {
            "mission_id": mission_id,
            "event_type": "PROOF_MINTED",
            "status": "COMPLETED",
            "proof_ref": f"manifest:{mission_id}.md",
            "meta": {"note": "placeholder proof minted; wire real manifest path next", "ts": _utc_now()},
        }
    )

    return {"ok": True, "mission_id": mission_id}
