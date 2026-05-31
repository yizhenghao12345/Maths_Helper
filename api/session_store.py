from typing import Optional
import time

import db


SESSION_TIMEOUT = 30 * 60


class Session:
    def __init__(self, session_id: str, problem: str, language: str = "zh-CN"):
        self.session_id = session_id
        self.problem = problem
        self.language = language
        self.parsed_problem = None
        self.current_step = 0
        self.nodes = []
        self.edges = []
        self.questions = []
        self.is_completed = False
        self.consecutive_errors = 0
        self.question_history = []
        self.exploration_nodes = []
        self.created_at = time.time()
        self.last_active = time.time()

    def is_expired(self) -> bool:
        return time.time() - self.last_active > SESSION_TIMEOUT

    def touch(self):
        self.last_active = time.time()

    def save(self):
        db.update_session(
            self.session_id,
            problem=self.problem,
            language=self.language,
            parsed_problem=self.parsed_problem,
            current_step=self.current_step,
            nodes=self.nodes,
            edges=self.edges,
            is_completed=self.is_completed,
            consecutive_errors=self.consecutive_errors,
        )

    @classmethod
    def from_db(cls, data: dict) -> "Session":
        session = cls(data["id"], data["problem"], data.get("language", "zh-CN"))
        session.parsed_problem = data.get("parsed_problem")
        session.current_step = data.get("current_step", 0)
        session.nodes = data.get("nodes", [])
        session.edges = data.get("edges", [])
        session.is_completed = data.get("is_completed", False)
        session.consecutive_errors = data.get("consecutive_errors", 0)
        session.question_history = _load_question_history(data["id"])
        session.exploration_nodes = []
        return session


class SessionStore:
    def __init__(self):
        self.sessions: dict[str, Session] = {}

    def create_session(self, session_id: str, problem: str, language: str = "zh-CN") -> Session:
        db.create_session(session_id, problem, language)
        session = Session(session_id, problem, language)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if not session.is_expired():
                session.touch()
                return session
            else:
                del self.sessions[session_id]
                return None

        data = db.get_session(session_id)
        if data is None:
            return None
        session = Session.from_db(data)
        session.touch()
        self.sessions[session_id] = session
        return session

    def update_session(self, session_id: str, **kwargs):
        session = self.get_session(session_id)
        if session:
            session.touch()
            for key, value in kwargs.items():
                setattr(session, key, value)
            db.update_session(session_id, **kwargs)

    def cleanup_expired(self):
        expired_ids = [
            sid for sid, session in self.sessions.items() if session.is_expired()
        ]
        for sid in expired_ids:
            del self.sessions[sid]
        db.cleanup_expired(SESSION_TIMEOUT)
        if expired_ids:
            print(f"清理了 {len(expired_ids)} 个过期会话")


session_store = SessionStore()


def _load_question_history(session_id: str) -> list[dict]:
    rows = db.get_question_history(session_id)
    return [
        {
            "question": row.get("question", ""),
            "answer": row.get("answer", ""),
            "selected_option": row.get("selected_option", ""),
            "feedback": row.get("feedback", ""),
            "is_correct": bool(row.get("is_correct", False)),
        }
        for row in rows
    ]
