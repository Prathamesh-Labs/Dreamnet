from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.database.connection import get_db, engine, Base
from app.api.questions import router as questions_router
from app.api.hypotheses import router as hypotheses_router
from app.api.research import router as research_router
from app.api.discoveries import router as discoveries_router
from app.api.telemetry import router as telemetry_router
import app.database.base  # Register models

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend engine for DREAMNET autonomous research loop"
)

app.include_router(questions_router)
app.include_router(questions_router, prefix="/api")
app.include_router(hypotheses_router)
app.include_router(hypotheses_router, prefix="/api")
app.include_router(research_router)
app.include_router(research_router, prefix="/api")
app.include_router(discoveries_router)
app.include_router(discoveries_router, prefix="/api")
app.include_router(telemetry_router)
app.include_router(telemetry_router, prefix="/api")




# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    try:
        # Attempt to create tables on startup if database is connected
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE hypotheses ADD COLUMN IF NOT EXISTS peer_review JSONB DEFAULT '[]'::jsonb"))
            conn.execute(text("ALTER TABLE hypotheses ADD COLUMN IF NOT EXISTS parent_discovery_id UUID DEFAULT NULL"))
            conn.execute(text("ALTER TABLE hypotheses ADD COLUMN IF NOT EXISTS parent_experiment_id UUID DEFAULT NULL"))
            
            conn.execute(text("ALTER TABLE experiments ADD COLUMN IF NOT EXISTS reproducibility_metadata JSONB DEFAULT '{}'::jsonb"))
            conn.execute(text("ALTER TABLE experiments ADD COLUMN IF NOT EXISTS reproduced_from_id UUID DEFAULT NULL"))
            
            conn.execute(text("ALTER TABLE experiment_results ADD COLUMN IF NOT EXISTS parameters JSONB DEFAULT '{}'::jsonb"))
            conn.execute(text("ALTER TABLE experiment_results ADD COLUMN IF NOT EXISTS environment_info JSONB DEFAULT '{}'::jsonb"))
            
            conn.execute(text("ALTER TABLE discoveries ADD COLUMN IF NOT EXISTS discovery_type VARCHAR"))
            conn.execute(text("ALTER TABLE discoveries ADD COLUMN IF NOT EXISTS source_experiment_id UUID DEFAULT NULL"))
            conn.execute(text("ALTER TABLE discoveries ADD COLUMN IF NOT EXISTS expected_value FLOAT DEFAULT NULL"))
            conn.execute(text("ALTER TABLE discoveries ADD COLUMN IF NOT EXISTS observed_value FLOAT DEFAULT NULL"))
            conn.execute(text("ALTER TABLE discoveries ADD COLUMN IF NOT EXISTS deviation FLOAT DEFAULT NULL"))
            conn.commit()
        print("Database tables and custom columns initialized successfully.")

        # Resume active sessions
        from app.database.connection import SessionLocal
        from app.models.research_session import ResearchSession
        from app.research.controller import ResearchController
        db_start = SessionLocal()
        try:
            active_sessions = db_start.query(ResearchSession).filter(
                ResearchSession.status.in_([
                    "RUNNING", "HYPOTHESIS_GENERATION", "EXPERIMENT_DESIGN", 
                    "EXECUTING", "EVALUATING", "DISCOVERY_SCAN"
                ])
            ).all()
            for session in active_sessions:
                print(f"[Startup] Resuming active research session {session.id}...")
                ResearchController.start_session(session.id, db_start)
        except Exception as resume_err:
            print(f"[Startup] Failed to resume sessions: {resume_err}")
        finally:
            db_start.close()

    except Exception as e:
        print(f"Database initialization failed on startup: {e}")

@app.get("/")
async def root():
    return {"message": "Welcome to DREAMNET API. System is online."}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    db_status = "disconnected"
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_error = str(e)
        
    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "database_error": db_error
    }
