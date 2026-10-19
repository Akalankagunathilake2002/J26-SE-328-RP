from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.interview_router import router as interview_router
# Register models
import app.models.interview


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[{settings.SERVICE_NAME}] Starting up. Verifying database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # create_all doesn't add columns to existing tables
            from sqlalchemy import text
            await conn.execute(text(
                "ALTER TABLE interview_turns ADD COLUMN IF NOT EXISTS reference_answer TEXT, "
                "ADD COLUMN IF NOT EXISTS rubric_criteria JSONB, "
                "ADD COLUMN IF NOT EXISTS phase VARCHAR(20) NOT NULL DEFAULT 'core'"
            ))
            await conn.execute(text(
                "ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS candidate_name VARCHAR(100), "
                "ADD COLUMN IF NOT EXISTS duration_minutes INTEGER, "
                "ADD COLUMN IF NOT EXISTS candidate_intro TEXT"
            ))
        print(f"[{settings.SERVICE_NAME}] Database tables verified successfully.")

        # Auto-seed question rubrics if table has fewer than 20 items
        try:
            from sqlalchemy import func, select
            from app.models.interview import InterviewDocument
            from ingestion.ingest_rubrics import run_interview_ingestion, load_question_bank
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(func.count(InterviewDocument.id)))
                count = res.scalar() or 0
                on_disk = len(load_question_bank())
                if count < on_disk:
                    print(f"[{settings.SERVICE_NAME}] Seeding interview question bank ({count} in database, {on_disk} on disk)...")
                    await run_interview_ingestion()
        except Exception as e:
            print(f"[{settings.SERVICE_NAME}] Auto-ingestion notice: {e}")
    except Exception as e:
        print(f"[{settings.SERVICE_NAME}] Database connection warning: {e}")

    yield

    print(f"[{settings.SERVICE_NAME}] Shutting down database engine...")
    await engine.dispose()


app = FastAPI(
    title="AI Mock Interview Assistant Microservice",
    description="Speech-enabled mock interview and RAG evaluation service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT
    }

app.include_router(interview_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)

