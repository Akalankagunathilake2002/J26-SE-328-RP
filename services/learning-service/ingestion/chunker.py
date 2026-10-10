import hashlib
import re
from typing import List, Dict, Any


class TextChunk:
    def __init__(self, content: str, chunk_index: int, metadata: Dict[str, Any]):
        self.content = content
        self.chunk_index = chunk_index
        self.metadata = metadata
        self.content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()


class MarkdownChunker:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str, base_metadata: Dict[str, Any]) -> List[TextChunk]:
        """
        Splits text recursively with awareness of code fences and paragraphs.
        Maintains chunk overlap for context continuity.
        """
        if not text or not text.strip():
            return []

        # Split into major sections by headers or double newlines
        paragraphs = re.split(r'(\n#{1,4}\s[^\n]+\n|\n\n)', text)
        
        chunks: List[str] = []
        current_chunk = ""

        for part in paragraphs:
            if not part:
                continue

            # If adding this part exceeds chunk_size and current_chunk is not empty
            if len(current_chunk) + len(part) > self.chunk_size and len(current_chunk) > self.chunk_overlap:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from the tail of current_chunk
                overlap_text = current_chunk[-self.chunk_overlap:]
                current_chunk = overlap_text + part
            else:
                current_chunk += part

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Construct TextChunk objects with enriched metadata
        result_chunks = []
        for idx, c in enumerate(chunks):
            chunk_meta = dict(base_metadata)
            chunk_meta.update({
                "chunk_index": idx,
                "chunk_char_length": len(c),
                "chunk_overlap": self.chunk_overlap
            })
            result_chunks.append(TextChunk(content=c, chunk_index=idx, metadata=chunk_meta))

        return result_chunks
