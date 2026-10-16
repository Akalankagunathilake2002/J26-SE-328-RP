import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.models.learning import LearningDocument, LearningChunk, Base
from app.services.embedding_service import embedding_service
from ingestion.loader import DocumentLoader
from ingestion.chunker import MarkdownChunker


async def run_ingestion(data_dir: str = None):
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    print(f"[Ingestion] Loading educational documents from: {data_dir}")
    documents = DocumentLoader.load_directory(data_dir)
    if not documents:
        print("[Ingestion Warning] No documents found to ingest!")
        return

    print(f"[Ingestion] Found {len(documents)} document(s). Connecting to database...")
    engine = create_async_engine(settings.async_database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        # Ensure schema tables exist
        await conn.run_sync(Base.metadata.create_all)

    chunker = MarkdownChunker(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

    total_chunks_ingested = 0

    async with session_factory() as session:
        for doc_data in documents:
            title = doc_data["title"]
            topic = doc_data["topic"]
            target_role = doc_data["target_role"]

            # Check if document already exists
            stmt = select(LearningDocument).where(
                LearningDocument.title == title,
                LearningDocument.topic == topic,
                LearningDocument.target_role == target_role
            )
            res = await session.execute(stmt)
            existing_doc = res.scalar_one_or_none()

            if existing_doc:
                print(f"[Ingestion] Updating existing document: '{title}'")
                doc_record = existing_doc
                # Clean old chunks
                await session.execute(delete(LearningChunk).where(LearningChunk.document_id == doc_record.id))
            else:
                print(f"[Ingestion] Creating new document: '{title}'")
                doc_record = LearningDocument(
                    title=title,
                    source=doc_data["source"],
                    url=doc_data["url"],
                    topic=topic,
                    target_role=target_role
                )
                session.add(doc_record)
                await session.flush()  # Populates doc_record.id

            # Chunk document
            chunks = chunker.split_text(
                text=doc_data["content"],
                base_metadata={
                    "title": title,
                    "topic": topic,
                    "target_role": target_role,
                    "source": doc_data["source"]
                }
            )

            print(f"  -> Generated {len(chunks)} chunk(s). Computing embeddings...")
            chunk_texts = [c.content for c in chunks]
            embeddings = embedding_service.embed_batch(chunk_texts)

            for c, emb in zip(chunks, embeddings):
                chunk_record = LearningChunk(
                    document_id=doc_record.id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    chunk_metadata=c.metadata,
                    embedding=emb
                )
                session.add(chunk_record)

            total_chunks_ingested += len(chunks)

        await session.commit()

    await engine.dispose()
    print(f"[Ingestion Complete] Successfully ingested {len(documents)} documents ({total_chunks_ingested} chunks) into pgvector!")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
