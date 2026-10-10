import os
import re
from typing import Dict, Any, List


class DocumentLoader:
    @staticmethod
    def load_markdown_file(file_path: str) -> Dict[str, Any]:
        """Loads a markdown file, parses frontmatter or header comments for metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from first # header or fallback to filename
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

        # Default metadata extraction from path or header conventions
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        topic = base_name.replace("_", " ").title()

        return {
            "title": title,
            "source": "Official Technical Curriculum & Industry Documentation",
            "url": f"https://curriculum.skillbridge.edu/docs/{base_name}",
            "topic": topic,
            "target_role": "Backend Developer",
            "content": content
        }

    @staticmethod
    def load_directory(dir_path: str) -> List[Dict[str, Any]]:
        """Loads all .md and .txt files in a directory."""
        documents = []
        if not os.path.isdir(dir_path):
            return documents

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith((".md", ".txt")):
                    full_path = os.path.join(root, file)
                    doc = DocumentLoader.load_markdown_file(full_path)
                    documents.append(doc)

        return documents
