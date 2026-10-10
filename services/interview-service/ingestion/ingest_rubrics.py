import asyncio
import os
import sys
import json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.models.interview import InterviewDocument, InterviewChunk, Base
from app.services.embedding_service import embedding_service


async def run_interview_ingestion(json_path: str = None):
    if json_path is None:
        json_path = os.path.join(os.path.dirname(__file__), "..", "data", "backend_questions.json")

    print(f"[Interview Ingestion] Loading question bank from: {json_path}")
    if not os.path.exists(json_path):
        print(f"[Error] File not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[Interview Ingestion] Found {len(data)} question(s). Connecting to database...")
    engine = create_async_engine(settings.async_database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        for item in data:
            title = item["title"]
            role = item["role"]
            topic = item["topic"]
            difficulty = item["difficulty"]

            # Check existing doc
            stmt = select(InterviewDocument).where(
                InterviewDocument.title == title,
                InterviewDocument.role == role
            )
            res = await session.execute(stmt)
            existing_doc = res.scalar_one_or_none()

            if existing_doc:
                print(f"[Interview Ingestion] Updating existing item: '{title}'")
                doc = existing_doc
                await session.execute(delete(InterviewChunk).where(InterviewChunk.document_id == doc.id))
            else:
                print(f"[Interview Ingestion] Creating new question doc: '{title}'")
                doc = InterviewDocument(
                    title=title,
                    role=role,
                    topic=topic,
                    difficulty=difficulty,
                    source=item["source"]
                )
                session.add(doc)
                await session.flush()

            # Compute embedding over the question and topic
            embed_text = f"{title} {topic} {item['content']} {item.get('expected_answer', '')}"
            vec = embedding_service.embed_text(embed_text)

            chunk = InterviewChunk(
                document_id=doc.id,
                chunk_index=0,
                content=item["content"],
                expected_answer=item.get("expected_answer"),
                rubric=item.get("rubric", {}),
                chunk_metadata={
                    "title": title,
                    "role": role,
                    "topic": topic,
                    "difficulty": difficulty
                },
                embedding=vec
            )
            session.add(chunk)

        await session.commit()

    await engine.dispose()
    print(f"[Interview Ingestion Complete] Successfully ingested {len(data)} question records with vector embeddings!")


if __name__ == "__main__":
    asyncio.run(run_interview_ingestion())
