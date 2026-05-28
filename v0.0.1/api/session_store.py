from typing import Optional
import time


SESSION_TIMEOUT = 30 * 60


class Session:
    def __init__(self, session_id: str, problem: str):
        self.session_id = session_id
        self.problem = problem
        self.current_step = 0
        self.nodes = []
        self.edges = []
        self.questions = []
        self.is_completed = False
        self.created_at = time.time()
        self.last_active = time.time()

    def is_expired(self) -> bool:
        return time.time() - self.last_active > SESSION_TIMEOUT

    def touch(self):
        self.last_active = time.time()


class SessionStore:
    def __init__(self):
        self.sessions: dict[str, Session] = {}

    def create_session(self, session_id: str, problem: str) -> Session:
        session = Session(session_id, problem)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        session = self.sessions.get(session_id)
        if session:
            session.touch()
        return session

    def update_session(self, session_id: str, **kwargs):
        session = self.sessions.get(session_id)
        if session:
            session.touch()
            for key, value in kwargs.items():
                setattr(session, key, value)

    def cleanup_expired(self):
        expired_ids = [
            sid for sid, session in self.sessions.items() if session.is_expired()
        ]
        for sid in expired_ids:
            del self.sessions[sid]
        if expired_ids:
            print(f"清理了 {len(expired_ids)} 个过期会话")


session_store = SessionStore()
