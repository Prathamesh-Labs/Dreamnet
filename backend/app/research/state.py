from typing import Set
from uuid import UUID

class ResearchStateManager:
    _active_sessions: Set[UUID] = set()

    @classmethod
    def register_running(cls, session_id: UUID) -> None:
        cls._active_sessions.add(session_id)

    @classmethod
    def deregister_running(cls, session_id: UUID) -> None:
        if session_id in cls._active_sessions:
            cls._active_sessions.remove(session_id)

    @classmethod
    def is_running(cls, session_id: UUID) -> bool:
        return session_id in cls._active_sessions
