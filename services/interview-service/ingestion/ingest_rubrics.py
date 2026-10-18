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


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_question_bank(json_path: str = None) -> list:
    """All question files in data/ (the curated bank and public_question_bank.json), or one file."""
    paths = [json_path] if json_path else sorted(
        os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".json"))
    data = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            data += json.load(f)
    return data


async def run_interview_ingestion(json_path: str = None):
    print(f"[Interview Ingestion] Loading question bank from: {json_path or DATA_DIR}")
    data = load_question_bank(json_path)

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
                    "difficulty": difficulty,
                    # Public-bank items: where the question came from and which documents ground the answer
                    "provenance": item.get("provenance"),
                },
                embedding=vec
            )
            session.add(chunk)

        await session.commit()

    await engine.dispose()
    print(f"[Interview Ingestion Complete] Successfully ingested {len(data)} question records with vector embeddings!")


if __name__ == "__main__":
    asyncio.run(run_interview_ingestion())
