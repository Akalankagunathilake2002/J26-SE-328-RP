from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_v1_router
# Import models to ensure they register on Base.metadata
import app.models.learning


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist in learning_db
    print(f"[{settings.SERVICE_NAME}] Starting up. Verifying database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print(f"[{settings.SERVICE_NAME}] Database tables verified successfully.")

        # Auto-seed educational curriculum documents if corpus is empty or needs update
        try:
            from sqlalchemy import func, select
            from app.models.learning import LearningDocument
            from ingestion.ingest import run_ingestion
            from app.core.database import async_session_factory
            async with async_session_factory() as session:
                res = await session.execute(select(func.count(LearningDocument.id)))
                count = res.scalar() or 0
                if count < 25:
                    print(f"[{settings.SERVICE_NAME}] Seeding full multi-track curriculum corpus ({count} existing docs)...")
                    await run_ingestion()
        except Exception as e:
            print(f"[{settings.SERVICE_NAME}] Auto-ingestion notice: {e}")
    except Exception as e:
        print(f"[{settings.SERVICE_NAME}] Database connection warning during startup: {e}")

    yield

    # Shutdown: dispose of database connection pool
    print(f"[{settings.SERVICE_NAME}] Shutting down database engine...")
    await engine.dispose()


app = FastAPI(
    title="Personalized Learning Assistant Microservice",
    description="RAG-powered learning assistant for the Academic-to-Industry Skill Bridge Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT
    }

# Mount API V1 routes
app.include_router(api_v1_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)

