from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.progress import StudentProgressResponse
from app.services.progress_service import progress_service

router = APIRouter(prefix="/progress", tags=["Student Learning Progress"])


@router.get("/{student_id}", response_model=StudentProgressResponse)
async def get_progress(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves student topics explored and completed without using a skill tree."""
    return await progress_service.get_student_progress(session=db, student_id=student_id)
