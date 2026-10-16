import os
import re
from typing import Dict, Any, List


ROLE_TRACK_MAPPING = {
    "backend": "Backend Developer",
    "fullstack": "Full-Stack Developer",
    "devops": "DevOps Engineer",
    "database": "Database Engineer"
}


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

        # Check for explicit metadata in comments, e.g. <!-- role: Backend Developer -->
        role_match = re.search(r'<!--\s*role:\s*(.+?)\s*-->', content, re.IGNORECASE)
        if role_match:
            target_role = role_match.group(1).strip()

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        topic = base_name.replace("_", " ").title()

        topic_match = re.search(r'<!--\s*topic:\s*(.+?)\s*-->', content, re.IGNORECASE)
        if topic_match:
            topic = topic_match.group(1).strip()

        return {
            "title": title,
            "source": f"Industry Curriculum: {target_role} Specialization",
            "url": f"https://curriculum.skillbridge.edu/docs/{parent_dir}/{base_name}",
            "topic": topic,
            "target_role": target_role,
            "content": content
        }

    @staticmethod
    def load_directory(dir_path: str) -> List[Dict[str, Any]]:
        """Loads all .md and .txt files recursively across career track directories."""
        documents = []
        if not os.path.isdir(dir_path):
            return documents

        for root, _, files in os.walk(dir_path):
            for file in sorted(files):
                if file.endswith((".md", ".txt")):
                    full_path = os.path.join(root, file)
                    doc = DocumentLoader.load_markdown_file(full_path)
                    documents.append(doc)

        return documents
