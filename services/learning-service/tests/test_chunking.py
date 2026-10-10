import pytest
from ingestion.chunker import MarkdownChunker


def test_markdown_chunker_basic():
    sample_text = """# JWT Authentication
    
JSON Web Tokens are an open standard RFC 7519 for secure communication.
In modern web applications, JWTs are commonly used for stateless authorization.

## Structure
A JWT consists of three parts:
1. Header
2. Payload
3. Signature

Each part is separated by a dot and encoded in Base64Url format.
"""
    chunker = MarkdownChunker(chunk_size=150, chunk_overlap=30)
    chunks = chunker.split_text(sample_text, base_metadata={"topic": "Security"})

    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.content
        assert chunk.metadata["topic"] == "Security"
        assert len(chunk.content) > 0
        assert chunk.content_hash is not None


def test_markdown_chunker_empty():
    chunker = MarkdownChunker(chunk_size=200, chunk_overlap=50)
    assert chunker.split_text("", {}) == []
    assert chunker.split_text("   \n\n  ", {}) == []
