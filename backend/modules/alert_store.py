import sqlite3
import json
from typing import Optional

DB_PATH = "alerts.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            type TEXT,
            source TEXT,
            severity TEXT,
            confidence REAL,
            status TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            resolved_AT INTEGER,
            signals TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def upsert_alert(alert: dict):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO alerts (
            id, type, source, severity, confidence,
            status, created_at, updated_at, resolved_at, signals
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (id) DO UPDATE SET
        severity=excluded.severity,
        confidence=excluded.confidence,
        status=excluded.status,
        updated_at=excluded.updated_at,
        resolved_at=excluded.resolved_at,
        signals=excluded.signals
    """, (
        alert["id"], 
        alert["type"], 
        alert["source"], 
        str(alert["severity"]), 
        alert["confidence"], 
        str(alert["status"]), 
        alert["created_at"], 
        alert["updated_at"], 
        alert["resolved_at"], 
        json.dump(alert["signals"]),
    ))
    
    conn.commit()
    conn.close()

def load_active_alert() -> Optional[dict]:
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT id, type, source, severity, confidence,
           status, created_at, updated_at, resolved_at, signals
    FROM alerts
    WHERE status IN ('NEW', 'ACTIVE')
    ORDER BY created_at DESC
    LIMIT 1
    """)
    
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "id": row[0],
        "type": row[1],
        "source": row[2],
        "severity": row[3],
        "confidence": row[4],
        "status": row[5],
        "created_at": row[6],
        "updated_at": row[7],
        "resolved_at": row[8],
        "signals": json.load(row[9]),
    }