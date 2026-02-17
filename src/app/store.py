import json
import os
import sqlite3

DB_PATH = os.getenv("FLEXYFINS_DB_PATH", "flexyfins.db")


def ensure_tables():
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
    conn.commit()
    conn.close()


def insert_envelope(env: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO envelopes (mission_id, event_type, status, proof_ref, meta_json) VALUES (?, ?, ?, ?, ?)",
        (
            env.get("mission_id"),
            env.get("event_type"),
            env.get("status"),
            env.get("proof_ref"),
            json.dumps(env.get("meta") or {}),
        ),
    )
    conn.commit()
    conn.close()


def summary_counts() -> dict:
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM envelopes").fetchone()[0]
    ok = conn.execute(
        "SELECT COUNT(*) FROM envelopes WHERE status IN ('VERIFIED','COMPLETED','SETTLED','OK')"
    ).fetchone()[0]
    fail = conn.execute("SELECT COUNT(*) FROM envelopes WHERE status NOT IN ('VERIFIED','COMPLETED','SETTLED','OK')").fetchone()[0]
    conn.close()
    return {"total": total, "ok": ok, "fail": fail}
