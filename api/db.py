import sqlite3
import json
import os
import threading
from typing import Optional
from pydantic import BaseModel


def _json_serial(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


DB_PATH = os.path.join(os.path.dirname(__file__), "data", "maths_helper.db")

_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                problem TEXT NOT NULL,
                language TEXT DEFAULT 'zh-CN',
                parsed_problem TEXT,
                current_step INTEGER DEFAULT 0,
                nodes TEXT DEFAULT '[]',
                edges TEXT DEFAULT '[]',
                is_completed BOOLEAN DEFAULT 0,
                consecutive_errors INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS question_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT,
                answer TEXT,
                selected_option TEXT,
                feedback TEXT,
                is_correct BOOLEAN,
                step INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS ai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                provider TEXT,
                model TEXT,
                method TEXT,
                used_parsed_problem BOOLEAN DEFAULT 0,
                parsed_problem_title TEXT,
                request_summary TEXT,
                response_summary TEXT,
                duration_ms INTEGER,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS console_config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        _ensure_session_columns(conn)
        _ensure_ai_log_columns(conn)
        conn.commit()
    finally:
        conn.close()


def _ensure_session_columns(conn: sqlite3.Connection):
    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()
    }
    required_columns = {
        "language": "ALTER TABLE sessions ADD COLUMN language TEXT DEFAULT 'zh-CN'",
        "current_question_data": "ALTER TABLE sessions ADD COLUMN current_question_data TEXT",
    }

    for column, ddl in required_columns.items():
        if column not in existing_columns:
            conn.execute(ddl)


def _ensure_ai_log_columns(conn: sqlite3.Connection):
    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(ai_logs)").fetchall()
    }
    required_columns = {
        "used_parsed_problem": "ALTER TABLE ai_logs ADD COLUMN used_parsed_problem BOOLEAN DEFAULT 0",
        "parsed_problem_title": "ALTER TABLE ai_logs ADD COLUMN parsed_problem_title TEXT",
    }

    for column, ddl in required_columns.items():
        if column not in existing_columns:
            conn.execute(ddl)


def create_session(session_id: str, problem: str, language: str = "zh-CN") -> dict:
    with _lock:
        conn = _get_conn()
        try:
            conn.execute(
                "INSERT INTO sessions (id, problem, language) VALUES (?, ?, ?)",
                (session_id, problem, language),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return _row_to_session_dict(row)
        finally:
            conn.close()


def get_session(session_id: str) -> Optional[dict]:
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_session_dict(row)
    finally:
        conn.close()


def update_session(session_id: str, **kwargs):
    with _lock:
        conn = _get_conn()
        try:
            sets = []
            vals = []
            for key, value in kwargs.items():
                if key in ("nodes", "edges", "parsed_problem", "current_question_data"):
                    sets.append(f"{key} = ?")
                    vals.append(json.dumps(value, default=_json_serial) if value is not None else None)
                elif key == "is_completed":
                    sets.append(f"{key} = ?")
                    vals.append(1 if value else 0)
                else:
                    sets.append(f"{key} = ?")
                    vals.append(value)
            sets.append("last_active = CURRENT_TIMESTAMP")
            vals.append(session_id)
            conn.execute(
                f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?",
                vals,
            )
            conn.commit()
        finally:
            conn.close()


def list_sessions(limit: int = 20, offset: int = 0) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY last_active DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [_row_to_session_dict(r) for r in rows]
    finally:
        conn.close()


def delete_session(session_id: str):
    with _lock:
        conn = _get_conn()
        try:
            conn.execute(
                "DELETE FROM question_history WHERE session_id = ?",
                (session_id,),
            )
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
        finally:
            conn.close()


def cleanup_expired(timeout_seconds: int = 1800) -> int:
    with _lock:
        conn = _get_conn()
        try:
            cursor = conn.execute(
                "SELECT id FROM sessions WHERE last_active < datetime('now', ?)",
                (f"-{timeout_seconds} seconds",),
            )
            expired_ids = [row["id"] for row in cursor.fetchall()]
            for sid in expired_ids:
                conn.execute(
                    "DELETE FROM question_history WHERE session_id = ?", (sid,)
                )
                conn.execute("DELETE FROM sessions WHERE id = ?", (sid,))
            conn.commit()
            return len(expired_ids)
        finally:
            conn.close()


def add_question_history(
    session_id: str,
    question: str,
    answer: str,
    selected_option: str,
    feedback: str,
    is_correct: bool,
    step: int,
):
    with _lock:
        conn = _get_conn()
        try:
            conn.execute(
                "INSERT INTO question_history (session_id, question, answer, selected_option, feedback, is_correct, step) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, question, answer, selected_option, feedback, 1 if is_correct else 0, step),
            )
            conn.commit()
        finally:
            conn.close()


def get_question_history(session_id: str) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM question_history WHERE session_id = ? ORDER BY step ASC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_ai_log(
    session_id: str,
    provider: str,
    model: str,
    method: str,
    used_parsed_problem: bool,
    parsed_problem_title: Optional[str],
    request_summary: str,
    response_summary: str,
    duration_ms: int,
    success: bool,
    error_message: str,
):
    with _lock:
        conn = _get_conn()
        try:
            conn.execute(
                "INSERT INTO ai_logs (session_id, provider, model, method, used_parsed_problem, parsed_problem_title, request_summary, response_summary, duration_ms, success, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    provider,
                    model,
                    method,
                    1 if used_parsed_problem else 0,
                    parsed_problem_title,
                    request_summary,
                    response_summary,
                    duration_ms,
                    1 if success else 0,
                    error_message,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def get_ai_logs(limit: int = 50, offset: int = 0) -> list[dict]:
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM ai_logs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats() -> dict:
    conn = _get_conn()
    try:
        total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        completed_sessions = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE is_completed = 1"
        ).fetchone()[0]
        total_questions = conn.execute(
            "SELECT COUNT(*) FROM question_history"
        ).fetchone()[0]
        correct_questions = conn.execute(
            "SELECT COUNT(*) FROM question_history WHERE is_correct = 1"
        ).fetchone()[0]
        correct_rate = (
            round(correct_questions / total_questions * 100, 1)
            if total_questions > 0
            else 0.0
        )

        rows = conn.execute(
            "SELECT parsed_problem FROM sessions WHERE parsed_problem IS NOT NULL"
        ).fetchall()
        problem_type_distribution = {}
        for row in rows:
            try:
                parsed = json.loads(row["parsed_problem"])
                ptype = parsed.get("problem_type", "unknown")
            except (json.JSONDecodeError, TypeError):
                ptype = "unknown"
            problem_type_distribution[ptype] = problem_type_distribution.get(ptype, 0) + 1

        avg_steps = 0.0
        if completed_sessions > 0:
            row = conn.execute(
                "SELECT AVG(current_step) FROM sessions WHERE is_completed = 1"
            ).fetchone()
            avg_steps = round(row[0], 1) if row[0] is not None else 0.0

        recent_sessions = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE created_at > datetime('now', '-1 day')"
        ).fetchone()[0]

        exploration_count = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM question_history WHERE is_correct = 0"
        ).fetchone()[0]
        exploration_rate = round(exploration_count / total_sessions, 3) if total_sessions > 0 else 0.0

        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "total_questions": total_questions,
            "correct_rate": correct_rate,
            "problem_type_distribution": problem_type_distribution,
            "avg_steps": avg_steps,
            "recent_sessions": recent_sessions,
            "exploration_rate": exploration_rate,
        }
    finally:
        conn.close()


def get_config(key: str) -> Optional[str]:
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT value FROM console_config WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def set_config(key: str, value: str):
    with _lock:
        conn = _get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO console_config (key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()


def _row_to_session_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["nodes"] = json.loads(d["nodes"]) if d["nodes"] else []
    d["edges"] = json.loads(d["edges"]) if d["edges"] else []
    d["parsed_problem"] = (
        json.loads(d["parsed_problem"]) if d["parsed_problem"] else None
    )
    d["current_question_data"] = (
        json.loads(d["current_question_data"]) if d.get("current_question_data") else None
    )
    d["is_completed"] = bool(d["is_completed"])
    return d
