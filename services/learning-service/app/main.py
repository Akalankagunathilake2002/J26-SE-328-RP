import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_v1_router
# Import models to ensure they register on Base.metadata
import app.models.learning


async def _drop_corpus_if_dimension_changed(conn):
    """The curriculum tables are built from data/ at startup, so when EMBEDDING_DIMENSION changes
    (e.g. Gemini 1536 -> local bge-small 384) they are dropped and re-ingested with the new model.
    Student history tables are left alone."""
    from sqlalchemy import text
    current = (await conn.execute(text(
        "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
        "WHERE attrelid = to_regclass('learning_chunks') AND attname = 'embedding'"
    ))).scalar()
    if current and current != f"vector({settings.EMBEDDING_DIMENSION})":
        print(f"[{settings.SERVICE_NAME}] Embedding column is {current}, settings want "
              f"vector({settings.EMBEDDING_DIMENSION}): rebuilding the curriculum corpus...")
        await conn.execute(text("DROP TABLE learning_chunks"))
        await conn.execute(text("DROP TABLE IF EXISTS learning_documents"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist in learning_db
    print(f"[{settings.SERVICE_NAME}] Starting up. Verifying database tables...")
    try:
        async with engine.begin() as conn:
            await _drop_corpus_if_dimension_changed(conn)
            await conn.run_sync(Base.metadata.create_all)
        print(f"[{settings.SERVICE_NAME}] Database tables verified successfully.")

        # Auto-seed educational curriculum documents if corpus is empty or needs update
        try:
            from sqlalchemy import func, select
            from app.models.learning import LearningDocument
            from ingestion.ingest import run_ingestion
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                from ingestion.loader import DocumentLoader
                res = await session.execute(select(func.count(LearningDocument.id)))
                count = res.scalar() or 0
                # Re-ingest when data/ has documents the database doesn't (first start, new corpus)
                on_disk = len(DocumentLoader.load_directory(os.path.join(os.path.dirname(__file__), "..", "data")))
                if count < on_disk:
                    print(f"[{settings.SERVICE_NAME}] Seeding curriculum corpus ({count} in database, "
                          f"{on_disk} on disk) in the background...")
                    # A large corpus takes minutes to embed; the service answers from what's loaded meanwhile
                    app.state.ingestion = asyncio.create_task(run_ingestion(skip_existing=True))
                    app.state.ingestion.add_done_callback(
                        lambda t: t.cancelled() or not t.exception() or
                        print(f"[{settings.SERVICE_NAME}] Background ingestion failed: {t.exception()}"))
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

