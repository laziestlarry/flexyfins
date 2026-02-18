import json
import os
import sqlite3
from typing import Any, Dict, List

DB_PATH = os.getenv("FLEXYFINS_DB_PATH", "flexyfins.db")
SUCCESS_STATUSES = {"VERIFIED", "COMPLETED", "SETTLED", "OK"}


def ensure_tables() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS envelopes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
            mission_id TEXT,
            event_type TEXT,
            status TEXT,
            proof_ref TEXT,
            meta_json TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_envelopes_key
        ON envelopes(mission_id, event_type, proof_ref)
        """
    )
    conn.commit()
    conn.close()


def _normalize_proof_ref(v: Any) -> str:
    return "" if v is None else str(v)


def _status_is_final(status: str) -> bool:
    return status.upper() in SUCCESS_STATUSES


def insert_envelope(env: Dict[str, Any]) -> bool:
    mission_id = str(env.get("mission_id", ""))
    event_type = str(env.get("event_type", ""))
    status = str(env.get("status", "")).upper()
    proof_ref = _normalize_proof_ref(env.get("proof_ref"))
    meta = env.get("meta") or {}

    conn = sqlite3.connect(DB_PATH)

    cur = conn.execute(
        """
        SELECT status FROM envelopes
        WHERE mission_id=? AND event_type=? AND proof_ref=?
        ORDER BY ts DESC LIMIT 1
        """,
        (mission_id, event_type, proof_ref),
    )
    row = cur.fetchone()

    if row:
        existing_status = str(row[0]).upper()
        # Idempotency + finality: do not override final states, and do not reinsert duplicates
        if existing_status == status or _status_is_final(existing_status):
            conn.close()
            return False

    conn.execute(
        """
        INSERT INTO envelopes (mission_id, event_type, status, proof_ref, meta_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (mission_id, event_type, status, proof_ref, json.dumps(meta)),
    )
    conn.commit()
    conn.close()
    return True


def summary_counts() -> Dict[str, int]:
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM envelopes").fetchone()[0]

    ok_statuses = tuple(SUCCESS_STATUSES)
    placeholders = ",".join("?" for _ in ok_statuses)
    ok = conn.execute(
        f"SELECT COUNT(*) FROM envelopes WHERE status IN ({placeholders})",
        ok_statuses,
    ).fetchone()[0]

    conn.close()
    return {"total": int(total), "ok": int(ok), "fail": int(total - ok)}


def recent_envelopes(limit: int = 25) -> List[Dict[str, Any]]:
    limit = max(1, int(limit))
    conn = sqlite3.connect(DB_PATH)

    rows = conn.execute(
        """
        SELECT ts, mission_id, event_type, status, proof_ref, meta_json
        FROM envelopes
        ORDER BY ts DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def mission_latest(limit: int = 200) -> List[Dict[str, Any]]:
    """
    Returns latest row per mission_id (best-effort using ts).
    """
    limit = max(1, int(limit))
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT e.ts, e.mission_id, e.event_type, e.status, e.proof_ref, e.meta_json
        FROM envelopes e
        INNER JOIN (
            SELECT mission_id, MAX(ts) AS max_ts
            FROM envelopes
            GROUP BY mission_id
        ) m ON e.mission_id = m.mission_id AND e.ts = m.max_ts
        ORDER BY e.ts DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    out: List[Dict[str, Any]] = []
    for ts, mission_id, event_type, status, proof_ref, meta_json in rows:
        try:
            meta = json.loads(meta_json) if meta_json else {}
        except Exception:
            meta = meta_json
        out.append(
            {
                "ts": ts,
                "mission_id": mission_id,
                "event_type": event_type,
                "status": status,
                "proof_ref": proof_ref,
                "meta": meta,
            }
        )
    return out


def mission_event_types(mission_id: str) -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT DISTINCT event_type FROM envelopes WHERE mission_id=?",
        (mission_id,),
    ).fetchall()
    conn.close()
    return [r[0] for r in rows if r and r[0]]

    
    conn.close()

    out = []
    for ts, mission_id, event_type, status, proof_ref, meta_json in rows:
        try:
            meta = json.loads(meta_json) if meta_json else {}
        except Exception:
            meta = meta_json

        out.append(
            {
                "ts": ts,
                "mission_id": mission_id,
                "event_type": event_type,
                "status": status,
                "proof_ref": proof_ref,
                "meta": meta,
            }
        )

    return out
