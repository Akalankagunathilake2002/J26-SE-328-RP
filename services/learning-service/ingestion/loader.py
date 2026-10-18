import os
import re
from typing import Dict, Any, List


ROLE_TRACK_MAPPING = {
    "backend": "Backend Developer",
    "fullstack": "Full-Stack Developer",
    "devops": "DevOps Engineer",
    "database": "Database Engineer"
}


# Notes about the corpus itself, not curriculum
SKIP_FILES = {"ATTRIBUTION.md", "README.md"}


def _header(content: str, key: str):
    m = re.search(rf'<!--\s*{key}:\s*(.+?)\s*-->', content, re.IGNORECASE)
    return m.group(1).strip() if m else None


class DocumentLoader:
    @staticmethod
    def load_markdown_file(file_path: str) -> Dict[str, Any]:
        """Loads a markdown file, parses frontmatter or directory conventions for metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from first # header or fallback to filename
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

        # Detect track from parent directory name
        parent_dir = os.path.basename(os.path.dirname(file_path)).lower()
        target_role = ROLE_TRACK_MAPPING.get(parent_dir, "Software Engineer")

        # Explicit metadata in comment headers, e.g. <!-- role: Backend Developer -->. External
        # documents (scripts/datasets/build_learning_corpus.py) also carry source, license and url.
        target_role = _header(content, "role") or target_role

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        topic = _header(content, "topic") or base_name.replace("_", " ").title()

        source = _header(content, "source") or f"Industry Curriculum: {target_role} Specialization"
        license_name = _header(content, "license")
        if license_name:
            source = f"{source} ({license_name})"

        return {
            "title": title[:255],
            "source": source[:255],
            "url": _header(content, "url") or f"https://curriculum.skillbridge.edu/docs/{parent_dir}/{base_name}",
            "topic": topic[:100],
            "target_role": target_role[:100],
            # Headers are metadata; keep them out of the chunk text that gets embedded
            "content": re.sub(r'<!--.*?-->\n?', '', content, flags=re.S).strip()
        }

    @staticmethod
    def load_directory(dir_path: str) -> List[Dict[str, Any]]:
        """Loads all .md and .txt files recursively across career track directories."""
        documents = []
        if not os.path.isdir(dir_path):
            return documents

        for root, _, files in os.walk(dir_path):
            for file in sorted(files):
                if file.endswith((".md", ".txt")) and file not in SKIP_FILES:
                    full_path = os.path.join(root, file)
                    doc = DocumentLoader.load_markdown_file(full_path)
                    documents.append(doc)

        return documents
