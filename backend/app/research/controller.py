import threading
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.research_session import ResearchSession
from app.research.loop import ResearchLoopEngine
from app.research.state import ResearchStateManager
from app.database.connection import SessionLocal

class ResearchController:
    @staticmethod
    def start_session(session_id: UUID, db: Session) -> ResearchSession:
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session:
            raise ValueError(f"Research session {session_id} not found.")

        if session.status == "RUNNING" and ResearchStateManager.is_running(session_id):
            return session

        session.status = "RUNNING"
        db.commit()

        # Run loop in a background thread so it doesn't block FastAPI
        def run_in_thread():
            db_thread = SessionLocal()
            try:
                ResearchLoopEngine.run_session_loop(session_id, db_thread)
            finally:
                db_thread.close()

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

        return session

    @staticmethod
    def pause_session(session_id: UUID, db: Session) -> ResearchSession:
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session:
            raise ValueError(f"Research session {session_id} not found.")

        session.status = "PAUSED"
        db.commit()
        return session

    @staticmethod
    def resume_session(session_id: UUID, db: Session) -> ResearchSession:
        # Resume is equivalent to starting the loop again after approval or pause
        return ResearchController.start_session(session_id, db)

    @staticmethod
    def stop_session(session_id: UUID, db: Session) -> ResearchSession:
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session:
            raise ValueError(f"Research session {session_id} not found.")

        session.status = "STOPPED"
        db.commit()
        return session
