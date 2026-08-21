from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.database.connection import get_db, engine, Base
from app.api.questions import router as questions_router
from app.api.hypotheses import router as hypotheses_router
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
        print("Database tables initialized successfully.")
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
