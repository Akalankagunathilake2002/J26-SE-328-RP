"""Collects candidate interview questions for generate_interview_bank.py.

    <venv>/bin/python scripts/datasets/extract_interview_candidates.py [RAW_DIR]

Two kinds of candidate, written to RAW_DIR/../interview-candidates.jsonl:
  - questions from openly licensed interview sets, with the set's own answer where it has one
    (test-your-sysadmin-skills, reactjs-interview-questions, h5bp front-end questions: MIT;
    system-design-primer: CC BY 4.0)
  - curriculum documents from services/learning-service/data/external to write a question from,
    for roles no open question set covers (Database Engineer above all)
The LLM step later rejects unsuitable questions, sets the level and writes answers and rubrics.
"""
import html
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAW = Path(sys.argv[1] if len(sys.argv) > 1 else "/Volumes/Dilmith Ext/datasets/raw")
CORPUS = REPO / "services" / "learning-service" / "data"
OUT = RAW.parent / "interview-candidates.jsonl"
rng = random.Random(42)


def plain(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(re.sub(r"\s+", " ", text)).replace("***", "").strip()


def sysadmin():
    text = (RAW / "sysadmin-skills" / "README.md").read_text(encoding="utf-8")
    levels = {"junior-sysadmin": "Entry Level", "regular-sysadmin": "Mid Level",
              "senior-sysadmin": "Senior Level", "guru-sysadmin": "Senior Level"}
    by_level: dict[str, list] = {}
    marks = [(m.start(), levels[m.group(1)]) for m in re.finditer(r'<a name="([a-z-]+-sysadmin)">', text)
             if m.group(1) in levels]
    for i, (start, level) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        for q in re.finditer(r"<summary><b>(.*?)</b></summary><br>(.*?)</details>", text[start:end], re.S):
            answer = re.sub(r"\n{3,}", "\n\n", q.group(2)).strip()
            if len(answer) < 200 or "To be completed" in answer:
                continue
            by_level.setdefault(level, []).append(dict(question=plain(q.group(1)), source_answer=answer[:3000]))
    for level, items in by_level.items():
        for item in rng.sample(items, min(20, len(items))):
            yield dict(item, kind="question", role="DevOps Engineer", level=level,
                       source="test-your-sysadmin-skills (trimstray)", license="MIT",
                       url="https://github.com/trimstray/test-your-sysadmin-skills")


def react():
    text = (RAW / "reactjs-interview-questions" / "README.md").read_text(encoding="utf-8")
    parts = re.split(r"^\s*\d+\.\s+### (.+)$", text, flags=re.M)
    items = []
    for i in range(1, len(parts) - 1, 2):
        answer = re.sub(r"\*\*\[⬆ Back to Top\]\(#table-of-contents\)\*\*", "", parts[i + 1])
        answer = re.sub(r"^ {4}", "", answer, flags=re.M).strip()
        if len(answer) >= 200:
            items.append(dict(question=plain(parts[i]), source_answer=answer[:3000]))
    for item in rng.sample(items, min(35, len(items))):
        yield dict(item, kind="question", role="Full-Stack Developer", level=None,
                   source="reactjs-interview-questions (Sudheer Jonna)", license="MIT",
                   url="https://github.com/sudheerj/reactjs-interview-questions")


def h5bp():
    items = []
    for name in ("general", "html", "css", "javascript", "network", "performance", "testing"):
        text = (RAW / "h5bp-fe-questions" / "src" / "questions" / f"{name}-questions.md").read_text(encoding="utf-8")
        for m in re.finditer(r"^\* (.+)$", text, flags=re.M):          # top-level bullets only
            q = plain(m.group(1))
            if len(q) > 25 and not re.search(r"favorite|your |you ", q, re.I):
                items.append(dict(question=q, source_answer=None))
    for item in rng.sample(items, min(25, len(items))):
        yield dict(item, kind="question", role="Full-Stack Developer", level=None,
                   source="Front-end Developer Interview Questions (h5bp)", license="MIT",
                   url="https://github.com/h5bp/Front-end-Developer-Interview-Questions")


def system_design():
    root = RAW / "system-design-primer"
    for path in sorted((root / "solutions" / "system_design").glob("*/README.md")):
        text = path.read_text(encoding="utf-8")
        title = re.search(r"^#\s+(.+)$", text, flags=re.M)
        role = "DevOps Engineer" if "aws" in path.parent.name else "Backend Developer"
        # The design itself is in Steps 2-4; Step 1 is only use cases and constraints
        design = text[text.find("## Step 2"):] if "## Step 2" in text else text
        design = re.sub(r"!\[[^\]]*\]\([^)]*\)|\*\*Clarify with your interviewer:\*\*.*", "", design)
        yield dict(kind="design", question=plain(title.group(1)) if title else path.parent.name,
                   source_answer=design[:6000], role=role, level="Senior Level",
                   source="The System Design Primer (Donne Martin)", license="CC BY 4.0",
                   url=f"https://github.com/donnemartin/system-design-primer/tree/master/solutions/system_design/{path.parent.name}")
    # Listed design questions without a worked solution: answered from the corpus instead
    readme = (root / "README.md").read_text(encoding="utf-8")
    block = re.search(r"### Additional system design interview questions(.*?)\n#{2,3} ", readme, re.S)
    rows = re.findall(r"^\| ([^|]+?) \|", block.group(1), flags=re.M) if block else []
    questions = [plain(r) for r in rows if not set(r.strip()) <= set("-") and r.strip().lower() != "question"
                 and not r.strip().lower().startswith("add a")]
    for q in rng.sample(questions, min(15, len(questions))):
        yield dict(kind="design", question=q, source_answer=None, role="Backend Developer", level="Senior Level",
                   source="The System Design Primer (Donne Martin)", license="CC BY 4.0",
                   url="https://github.com/donnemartin/system-design-primer#additional-system-design-interview-questions")


FROM_DOCS = (  # (role, file glob under learning-service/data, count)
    ("Database Engineer", "external/postgresql__*.md", 24),
    ("Database Engineer", "external/sqlite__*.md", 10),
    ("Database Engineer", "database/*.md", 6),
    ("Backend Developer", "external/azure__patterns__*.md", 10),
    ("Backend Developer", "external/mdn__http__guides__*.md", 8),
    ("Backend Developer", "external/genai__*.md", 6),
    ("Backend Developer", "external/github__actions__*.md", 3),
    ("Backend Developer", "external/github__get-started__*.md", 3),
    ("DevOps Engineer", "external/prometheus__*.md", 6),
    ("DevOps Engineer", "external/kubernetes__*.md", 8),
    ("DevOps Engineer", "external/docker__*.md", 4),
    ("DevOps Engineer", "external/og-aws__*.md", 4),
    ("DevOps Engineer", "external/github__actions__*.md", 3),
    ("Full-Stack Developer", "external/mdn__javascript__*.md", 4),
    ("Full-Stack Developer", "external/mdn__performance__*.md", 2),
    ("Full-Stack Developer", "external/mdn__security__*.md", 2),
    ("Full-Stack Developer", "external/github__get-started__*.md", 3),
)
LEVELS = ["Entry Level", "Mid Level", "Senior Level"]


def from_docs():
    n = 0
    for role, pattern, count in FROM_DOCS:
        docs = sorted(p for p in CORPUS.glob(pattern) if p.stat().st_size > 2500)
        for path in rng.sample(docs, min(count, len(docs))):
            text = path.read_text(encoding="utf-8")
            meta = dict(re.findall(r"<!--\s*(\w+):\s*(.+?)\s*-->", text))
            yield dict(kind="document", question=None, source_answer=None, role=role, level=LEVELS[n % 3],
                       document=re.sub(r"<!--.*?-->\n?", "", text)[:5000],
                       source=meta.get("source", "SkillBridge curriculum"), license=meta.get("license", "project"),
                       url=meta.get("url", ""))
            n += 1


ROLE_PROFILES = json.loads((REPO / "services/interview-service/app/core/role_profiles.json").read_text())["roles"]
COMPETENCIES_PER_ROLE, KNOWLEDGE_PER_ROLE = 12, 10


def doc_roles(path: Path) -> str:
    m = re.search(r"<!--\s*role:\s*(.+?)\s*-->", path.read_text(encoding="utf-8")[:300])
    return m.group(1) if m else ""


def non_technical():
    """Behavioural / situational questions from O*NET core tasks, knowledge questions from the role's documents."""
    import csv
    base = next((RAW / "onet" / "extracted").glob("*/"))
    with open(base / "Task Statements.txt", encoding="utf-8") as f:
        tasks = list(csv.DictReader(f, delimiter="\t"))
    n = 0
    for role, profile in ROLE_PROFILES.items():
        core = list(dict.fromkeys(t["Task"] for t in tasks if t["O*NET-SOC Code"] in profile["onet"]
                                  and t["Task Type"] == "Core"))
        for task in rng.sample(core, min(COMPETENCIES_PER_ROLE, len(core))):
            yield dict(kind="competency", technical=False, question=None, source_answer=None, competency=task,
                       role=role, level=LEVELS[n % 3], source="O*NET 31.0 Database (U.S. Department of Labor, ETA)",
                       license="CC BY 4.0", url=f"https://www.onetonline.org/link/summary/{profile['onet'][0]}")
            n += 1
        docs = [p for p in sorted((CORPUS / "external").glob("*.md"))
                if p.stat().st_size > 2500 and not p.name.startswith("onet__") and role in doc_roles(p)]
        for path in rng.sample(docs, min(KNOWLEDGE_PER_ROLE, len(docs))):
            text = path.read_text(encoding="utf-8")
            meta = dict(re.findall(r"<!--\s*(\w+):\s*(.+?)\s*-->", text))
            yield dict(kind="document", technical=False, question=None, source_answer=None, role=role,
                       level=LEVELS[n % 3], document=re.sub(r"<!--.*?-->\n?", "", text)[:5000],
                       source=meta.get("source", ""), license=meta.get("license", ""), url=meta.get("url", ""))
            n += 1


def main():
    # New sources go at the end so earlier candidate ids (and their generated results) stay valid
    candidates = [*sysadmin(), *react(), *h5bp(), *system_design(), *from_docs(), *non_technical()]
    for i, c in enumerate(candidates):
        c["id"] = f"c{i:04d}"
    with open(OUT, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")
    from collections import Counter
    print(Counter((c["role"], c["kind"]) for c in candidates))
    print(f"{len(candidates)} candidates -> {OUT}")


if __name__ == "__main__":
    main()
