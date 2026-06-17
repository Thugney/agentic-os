import sqlite3
from pathlib import Path
from typing import Iterable
from backend.app.core.settings import get_settings

def connect() -> sqlite3.Connection:
    db = get_settings().db_path
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def rows(sql: str, params: Iterable = ()): 
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]

def one(sql: str, params: Iterable = ()): 
    with connect() as conn:
        r = conn.execute(sql, tuple(params)).fetchone()
        return dict(r) if r else None

def execute(sql: str, params: Iterable = ()): 
    with connect() as conn:
        cur = conn.execute(sql, tuple(params))
        conn.commit()
        return cur.lastrowid
