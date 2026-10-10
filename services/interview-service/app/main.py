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
        print(f"[{settings.SERVICE_NAME}] Database tables verified successfully.")
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
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVICE_PORT, reload=True)
