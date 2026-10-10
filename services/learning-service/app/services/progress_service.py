import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning import (
    StudentLearningSession,
    StudentLearningQuery,
    StudentTopicProgress
)
from app.schemas.progress import (
    TopicProgressItem,
    StudentProgressResponse
)


class ProgressService:
    @staticmethod
    async def record_query_progress(
        session: AsyncSession,
        student_id: str,
        target_role: str,
        question: str,
        answer: str,
        topic: str,
        learning_priority: Optional[str] = None,
        recommended_next_topic: Optional[str] = None,
        retrieved_chunk_ids: Optional[List[uuid.UUID]] = None,
        sources: Optional[list] = None
    ):
        """
        Records a learning query and updates topic exploration counts.
        Transitions topic to 'completed' when queries count >= 3.
        """
        # 1. Ensure or find session
        query_record = StudentLearningQuery(
            student_id=student_id,
            question=question,
            learning_priority=learning_priority,
            answer=answer,
            recommended_next_topic=recommended_next_topic,
            retrieved_chunk_ids=retrieved_chunk_ids or [],
            sources=sources or []
        )
        session.add(query_record)

        # 2. Update Topic Progress
        stmt = select(StudentTopicProgress).where(
            StudentTopicProgress.student_id == student_id,
            StudentTopicProgress.topic == topic,
            StudentTopicProgress.target_role == target_role
        )
        result = await session.execute(stmt)
        progress_record = result.scalar_one_or_none()

        if progress_record:
            progress_record.queries_count += 1
            progress_record.last_studied_at = datetime.utcnow()
            if progress_record.queries_count >= 3:
                progress_record.status = "completed"
        else:
            progress_record = StudentTopicProgress(
                student_id=student_id,
                topic=topic,
                target_role=target_role,
                queries_count=1,
                status="in_progress",
                last_studied_at=datetime.utcnow()
            )
            session.add(progress_record)

        await session.commit()

    @staticmethod
    async def get_student_progress(
        session: AsyncSession,
        student_id: str
    ) -> StudentProgressResponse:
        """Fetches total topics explored and completed by student."""
        stmt = select(StudentTopicProgress).where(
            StudentTopicProgress.student_id == student_id
        ).order_by(StudentTopicProgress.last_studied_at.desc())

        result = await session.execute(stmt)
        records = result.scalars().all()

        items = []
        target_role = "General"
        completed_count = 0

        for r in records:
            target_role = r.target_role
            if r.status == "completed":
                completed_count += 1
            items.append(TopicProgressItem(
                topic=r.topic,
                target_role=r.target_role,
                queries_count=r.queries_count,
                status=r.status,
                last_studied_at=r.last_studied_at
            ))

        return StudentProgressResponse(
            student_id=student_id,
            target_role=target_role,
            total_topics_explored=len(items),
            completed_topics_count=completed_count,
            topics=items
        )


progress_service = ProgressService()
