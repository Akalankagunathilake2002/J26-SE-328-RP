"""Turns the raw documentation from fetch_datasets.sh into learning-service curriculum files.

    <venv>/bin/python scripts/datasets/build_learning_corpus.py [RAW_DIR]

Writes services/learning-service/data/external/<source>/<slug>.md. Each file starts with comment
headers the learning-service loader reads (role, topic, source, license, url), then clean markdown:
front matter, Hugo shortcodes, MDN macros, link targets and boilerplate sections are removed.
A focused subset of each source is kept (see the *_INCLUDE rules), not the whole site.
"""
import html
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "services" / "learning-service" / "data" / "external"
RAW = Path(sys.argv[1] if len(sys.argv) > 1 else "/Volumes/Dilmith Ext/datasets/raw")
MIN_CHARS = 600            # shorter pages (stubs, section indexes) add noise, not knowledge

BACKEND_FULLSTACK = "Backend Developer / Full-Stack Developer"
DATABASE_BACKEND = "Database Engineer / Backend Developer"

# ---------- markup cleaning ----------

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def front_matter(text: str) -> tuple[dict, str]:
    """Top-level `key: value` pairs of YAML front matter (enough for title/slug/description)."""
    m = FRONT_MATTER.match(text)
    if not m:
        return {}, text
    meta, key = {}, None
    for line in m.group(1).splitlines():
        top = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if top:
            key, value = top.group(1), top.group(2).strip()
            meta[key] = "" if value in (">", ">-", "|", "|-") else value.strip("'\"")
        elif key and line.startswith("  ") and key in ("description",):
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta, text[m.end():]


def clean_hugo(text: str) -> str:
    """Kubernetes / Docker docs (Hugo)."""
    def tooltip(m):
        args = m.group(1)
        t = re.search(r'text="([^"]+)"', args)
        if t:
            return t.group(1)
        term = re.search(r'term_id="([^"]+)"', args)
        return term.group(1).replace("-", " ") if term else ""
    text = re.sub(r"\{\{<\s*glossary_tooltip(.*?)>\}\}", tooltip, text)
    text = re.sub(r'\{\{%\s*heading\s+"([^"]+)"\s*%\}\}',
                  lambda m: "## " + {"whatsnext": "What's next"}.get(m.group(1), m.group(1).capitalize()), text)
    text = re.sub(r"\{\{[<%]\s*(note|caution|warning|tip|important)\s*[%>]\}\}",
                  lambda m: f"**{m.group(1).capitalize()}:**", text)
    text = re.sub(r'\{\{[<%]\s*tab\s+name="([^"]+)".*?[%>]\}\}', r"**\1:**", text)
    text = re.sub(r"\{\{[<%].*?[%>]\}\}", "", text, flags=re.S)       # every other shortcode
    return text


MDN_MACRO = re.compile(r"\{\{\s*([A-Za-z_-]+)\s*(?:\((.*?)\))?\s*\}\}", re.S)


def clean_mdn(text: str) -> str:
    def macro(m):
        args = re.findall(r'"([^"]*)"|\'([^\']*)\'', m.group(2) or "")
        args = [a or b for a, b in args]
        if not args:
            return ""                                   # {{Specifications}}, {{Compat}}, badges
        # Display text is the second argument when given (Glossary("Cache", "cached"))
        shown = args[1] if len(args) > 1 and args[1] and not args[1].isdigit() else args[0]
        return shown.split("/")[-1] if m.group(1).lower() in ("domxref", "jsxref") else shown
    text = MDN_MACRO.sub(macro, text)
    # Reference tables and link lists carry no explanation
    return drop_sections(text, ("Specifications", "Browser compatibility", "See also"))


def drop_sections(text: str, titles: tuple[str, ...]) -> str:
    out, skipping = [], False
    for line in text.splitlines():
        h = re.match(r"^(#{2,3})\s+(.*)$", line)
        if h:
            skipping = h.group(2).strip() in titles
        if not skipping:
            out.append(line)
    return "\n".join(out)


def clean_markdown(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)                  # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)                # links -> their text
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)               # reference links
    text = re.sub(r"^\s*\[[^\]]+\]:\s*\S+.*$", "", text, flags=re.M)    # link definitions
    text = re.sub(r"<(?!/?(?:code|pre)\b)[^>\n]+>", "", text)           # stray HTML tags
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def postgres_markdown(raw_html: str) -> tuple[str, str]:
    return html_markdown(raw_html, "#docContent", ".navheader, .navfooter, .toc")


def html_markdown(raw_html: str, content: str, junk: str, title_from_page: bool = False) -> tuple[str, str]:
    """title_from_page: use <title>, for sites whose first heading is generic ("Overview")."""
    from bs4 import BeautifulSoup
    from markdownify import markdownify
    soup = BeautifulSoup(raw_html, "html.parser")
    body = soup.select_one(content) or soup.body
    for el in body.select(f"{junk}, script, style, form"):
        el.decompose()
    heading = body.find(["h1", "h2"])
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    # Headings end with a "#" permalink anchor
    title = re.sub(r"^[\d.]+\.?\s*|\s*#$", "", heading.get_text(" ", strip=True)) if heading else ""
    if heading:
        heading.decompose()
    md = markdownify(str(body), heading_style="ATX", code_language="sql", strip=["a", "img"])
    if title_from_page and page_title:
        title = page_title
    md = re.sub(r"^(#+)\s*[\d.]+\.?\s+", r"\1 ", md, flags=re.M)        # "## 11.2. Index Types" -> "## Index Types"
    md = re.sub(r"^(.{1,120}?)\s+#$", r"\1", md, flags=re.M)          # permalinks on headings and terms
    return title, md

# ---------- sources ----------


def k8s_docs():
    root = RAW / "kubernetes-website" / "content" / "en" / "docs" / "concepts"
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if rel.parts[0] in ("windows", "extend-kubernetes"):
            continue
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        url_path = "/".join(rel.parts[:-1]) if path.name == "_index.md" else str(rel.with_suffix(""))
        section = rel.parts[0].replace("-", " ").title() if len(rel.parts) > 1 else "Overview"
        yield dict(
            title=meta.get("title") or path.stem, description=meta.get("description", ""),
            body=clean_hugo(body), role="DevOps Engineer", topic=f"Kubernetes {section}",
            source="Kubernetes Documentation", license="CC BY 4.0",
            url=f"https://kubernetes.io/docs/concepts/{url_path}/".replace("//", "/").replace(":/", "://"),
            key=f"kubernetes/{url_path or 'index'}",
        )


DOCKER_INCLUDE = (
    "get-started/docker-concepts/", "get-started/docker-overview",
    "manuals/build/building/", "manuals/build/cache/", "manuals/build/concepts/", "manuals/build/buildkit/",
    "manuals/compose/intro/", "manuals/compose/how-tos/",
    "manuals/engine/network/", "manuals/engine/storage/", "manuals/engine/containers/",
    "manuals/engine/security/", "manuals/engine/logging/", "manuals/engine/manage-resources/",
)


def docker_docs():
    root = RAW / "docker-docs" / "content"
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if not rel.startswith(DOCKER_INCLUDE):
            continue
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        url_path = rel.removeprefix("manuals/").removesuffix(".md").removesuffix("/_index").removesuffix("_index")
        parts = rel.split("/")
        area = parts[1] if parts[0] == "manuals" else "get started"
        sub = parts[2] if parts[0] == "manuals" and len(parts) > 3 else ""
        topic = f"Docker {area.title()}" + (f": {sub.replace('-', ' ').title()}" if sub else "")
        yield dict(
            title=meta.get("title") or path.stem, description=meta.get("description", ""),
            body=clean_hugo(body), role="DevOps Engineer", topic=topic,
            source="Docker Documentation", license="Apache-2.0",
            url=f"https://docs.docker.com/{url_path}/", key=f"docker/{url_path}",
        )


MDN_HEADERS = {
    "cache-control", "etag", "if-none-match", "if-modified-since", "last-modified", "vary", "age", "expires",
    "authorization", "www-authenticate", "set-cookie", "cookie", "content-type", "accept", "accept-encoding",
    "content-encoding", "content-length", "transfer-encoding", "connection", "keep-alive", "location",
    "retry-after", "forwarded", "x-forwarded-for", "origin", "referer", "user-agent", "range", "content-range",
    "strict-transport-security", "content-security-policy", "x-content-type-options", "x-frame-options",
    "access-control-allow-origin", "access-control-allow-credentials", "access-control-allow-methods",
    "access-control-allow-headers", "access-control-max-age", "access-control-request-method",
}
MDN_AREAS = (  # (path prefix under files/en-us/web, role, topic)
    ("http/guides/", BACKEND_FULLSTACK, "HTTP Guides"),
    ("http/reference/methods/", BACKEND_FULLSTACK, "HTTP Methods"),
    ("http/reference/status/", BACKEND_FULLSTACK, "HTTP Status Codes"),
    ("http/reference/headers/", BACKEND_FULLSTACK, "HTTP Headers"),
    ("security/", BACKEND_FULLSTACK, "Web Security"),
    ("javascript/guide/", "Full-Stack Developer", "JavaScript Guide"),
    ("api/fetch_api/", "Full-Stack Developer", "Fetch API"),
    ("api/web_storage_api/", "Full-Stack Developer", "Web Storage API"),
    ("performance/", "Full-Stack Developer", "Web Performance"),
)


def mdn_docs():
    root = RAW / "mdn-content" / "files" / "en-us" / "web"
    for path in sorted(root.rglob("index.md")):
        rel = path.relative_to(root).as_posix()
        area = next((a for a in MDN_AREAS if rel.startswith(a[0])), None)
        if not area:
            continue
        if area[2] == "HTTP Headers" and path.parent.name not in MDN_HEADERS:
            continue
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        slug = meta.get("slug") or rel.removesuffix("/index.md")
        yield dict(
            title=meta.get("title") or path.parent.name, description="",
            body=clean_mdn(body), role=area[1], topic=area[2],
            source="MDN Web Docs (Mozilla Contributors)", license="CC BY-SA 2.5",
            url=f"https://developer.mozilla.org/en-US/docs/{slug}", key=f"mdn/{rel.removesuffix('/index.md')}",
        )


PG_TOPICS = (  # (page name prefix, topic)
    ("indexes", "PostgreSQL Indexes"), ("mvcc", "PostgreSQL Concurrency Control"),
    ("transaction-iso", "PostgreSQL Concurrency Control"), ("explicit-locking", "PostgreSQL Concurrency Control"),
    ("applevel-consistency", "PostgreSQL Concurrency Control"), ("locking-indexes", "PostgreSQL Concurrency Control"),
    ("using-explain", "PostgreSQL Performance"), ("planner-stats", "PostgreSQL Performance"),
    ("explicit-joins", "PostgreSQL Performance"), ("populate", "PostgreSQL Performance"),
    ("non-durability", "PostgreSQL Performance"), ("ddl", "PostgreSQL Data Definition"),
    ("routine-vacuuming", "PostgreSQL Maintenance & WAL"), ("wal", "PostgreSQL Maintenance & WAL"),
    ("different-replication", "PostgreSQL Replication & High Availability"),
    ("warm-standby", "PostgreSQL Replication & High Availability"),
    ("hot-standby", "PostgreSQL Replication & High Availability"),
    ("logical-replication", "PostgreSQL Replication & High Availability"),
    ("backup", "PostgreSQL Backup & Restore"), ("continuous-archiving", "PostgreSQL Backup & Restore"),
    ("tutorial", "PostgreSQL SQL Queries"), ("queries", "PostgreSQL SQL Queries"),
    ("datatype-json", "PostgreSQL SQL Queries"), ("textsearch", "PostgreSQL SQL Queries"),
    ("client-authentication", "PostgreSQL Security"), ("auth", "PostgreSQL Security"),
)


def postgres_docs():
    pages = sorted(RAW.glob("postgresql-docs-*/*.html"))
    for path in pages:
        version = path.parent.name.rsplit("-", 1)[-1]
        title, body = postgres_markdown(path.read_text(encoding="utf-8"))
        topic = next((t for prefix, t in PG_TOPICS if path.stem.startswith(prefix)), "PostgreSQL")
        yield dict(
            title=title or path.stem, description="", body=body, role=DATABASE_BACKEND, topic=topic,
            source=f"PostgreSQL {version} Documentation", license="PostgreSQL Licence",
            url=f"https://www.postgresql.org/docs/{version}/{path.name}", key=f"postgresql/{path.stem}",
        )


ALL_ROLES = "All Roles"                 # the learning-service role filter matches "%all%" for every role
BACKEND_DEVOPS = "Backend Developer / DevOps Engineer"
BACKEND_FULLSTACK_AI = "Backend Developer / Full-Stack Developer"


def clean_azure(text: str) -> str:
    text = re.sub(r"^:::.*$", "", text, flags=re.M)                                   # :::image ...::: directives
    text = re.sub(r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", r"> **\1:**", text, flags=re.M)
    return re.sub(r"\[!INCLUDE[^\]]*\]\([^)]*\)", "", text)


GITHUB_VARS = {
    "prodname_dotcom": "GitHub", "prodname_actions": "GitHub Actions", "prodname_desktop": "GitHub Desktop",
    "prodname_cli": "GitHub CLI", "prodname_ghe_server": "GitHub Enterprise Server", "prodname_codespaces": "Codespaces",
    "product_name_short": "Git LFS", "product_url": "github.com", "github": "GitHub",
}


def clean_github(text: str) -> str:
    def var(m):
        return GITHUB_VARS.get(m.group(1).split(".")[-1], "GitHub")
    text = re.sub(r"\{%-?\s*data\s+variables\.([a-z_.]+)\s*-?%\}", var, text)
    text = re.sub(r"\{%-?.*?-?%\}", "", text)                                         # reusables, ifversion, octicons
    return re.sub(r"\{\{.*?\}\}", "", text)


def split_guide(path: Path, title_prefix: str, max_chars: int = 15000):
    """One document per '## ' section of a single-file guide; very long sections split on '### '."""
    text = path.read_text(encoding="utf-8")
    def sections(body: str, level: str):
        parts = re.split(rf"^{level} (.+)$", body, flags=re.M)
        return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
    # Some guides (og-aws) use ### as their top level
    top = "##" if re.search(r"^## ", text, flags=re.M) else "###"
    for heading, body in sections(text, top):
        if top == "##" and len(body) > max_chars and re.search(r"^### ", body, flags=re.M):
            for sub, sub_body in sections(body, "###"):
                yield f"{title_prefix}: {heading} - {sub}", sub_body, f"{heading}-{sub}"
        else:
            yield f"{title_prefix}: {heading}", body, heading


def anchor(heading: str) -> str:
    return re.sub(r"[^a-z0-9 -]", "", heading.lower()).strip().replace(" ", "-")


AZURE_AREAS = (("patterns/", "Cloud Design Patterns"), ("guide/architecture-styles/", "Architecture Styles"),
               ("best-practices/", "Cloud Best Practices"), ("microservices/", "Microservices Architecture"))


def azure_docs():
    root = RAW / "azure-architecture-center" / "docs"
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        area = next((t for prefix, t in AZURE_AREAS if rel.startswith(prefix)), None)
        if not area or path.stem in ("index", "toc", "includes") or "/includes/" in rel:
            continue
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        h1 = re.search(r"^#\s+(.+)$", body, flags=re.M)
        body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.M)
        yield dict(
            title=(h1.group(1) if h1 else meta.get("title") or path.stem).strip(), description=meta.get("description", ""),
            body=clean_azure(body), role=BACKEND_DEVOPS, topic=area,
            source="Azure Architecture Center (Microsoft)", license="CC BY 4.0",
            url=f"https://learn.microsoft.com/en-us/azure/architecture/{rel.removesuffix('.md')}",
            key=f"azure/{rel.removesuffix('.md')}",
        )


def guide_docs():
    guides = (  # (file, title prefix, role, topic, source, licence, base url)
        ("og-aws/README.md", "AWS Guide", "DevOps Engineer", "AWS Cloud Services", "The Open Guide to AWS",
         "CC BY 4.0", "https://github.com/open-guides/og-aws"),
        ("art-of-command-line/README.md", "Command Line", "DevOps Engineer", "Linux Command Line",
         "The Art of Command Line (Joshua Levy and contributors)", "CC BY-SA 4.0",
         "https://github.com/jlevy/the-art-of-command-line"),
        ("system-design-primer/README.md", "System Design", BACKEND_DEVOPS, "System Design",
         "The System Design Primer (Donne Martin)", "CC BY 4.0", "https://github.com/donnemartin/system-design-primer"),
    )
    skip = re.compile(r"license|contribut|credits|contact|disclaimer|translation|table of contents|index of|"
                      r"anki|motivation|meta|appendix|under development|how to approach|study guide|please help|"
                      r"certifications|getting help|related topics|"
                      r"additional system design|real world architectures|company architectures|company engineering",
                      re.I)
    for file, prefix, role, topic, source, lic, base in guides:
        for title, body, heading in split_guide(RAW / file, prefix):
            if skip.search(heading):
                continue
            yield dict(title=title, description="", body=body, role=role, topic=topic, source=source,
                       license=lic, url=f"{base}#{anchor(heading.split('-')[-1] if '-' in heading else heading)}",
                       key=f"{file.split('/')[0]}/{anchor(heading)[:80]}")
    # Worked system design interview solutions
    for path in sorted((RAW / "system-design-primer" / "solutions" / "system_design").glob("*/README.md")):
        text = path.read_text(encoding="utf-8")
        h1 = re.search(r"^#\s+(.+)$", text, flags=re.M)
        yield dict(title=h1.group(1).strip() if h1 else path.parent.name, description="",
                   body=re.sub(r"^#\s+.+$", "", text, count=1, flags=re.M), role=BACKEND_DEVOPS,
                   topic="System Design Case Studies", source="The System Design Primer (Donne Martin)",
                   license="CC BY 4.0",
                   url=f"https://github.com/donnemartin/system-design-primer/tree/master/solutions/system_design/{path.parent.name}",
                   key=f"system-design-primer/solution-{path.parent.name}")


GENAI_LESSONS = ("01", "02", "03", "04", "05", "06", "07", "08", "11", "13", "14", "15", "16", "17", "18")


def genai_docs():
    root = RAW / "generative-ai-for-beginners"
    for path in sorted(root.glob("[0-2][0-9]-*/README.md")):
        lesson = path.parent.name
        if lesson[:2] not in GENAI_LESSONS:
            continue
        text = path.read_text(encoding="utf-8")
        h1 = re.search(r"^#\s+(.+)$", text, flags=re.M)
        yield dict(title=(h1.group(1).strip() if h1 else lesson), description="",
                   body=re.sub(r"^#\s+.+$", "", text, count=1, flags=re.M), role=BACKEND_FULLSTACK_AI,
                   topic="Generative AI & RAG", source="Generative AI for Beginners (Microsoft)", license="MIT",
                   url=f"https://github.com/microsoft/generative-ai-for-beginners/tree/main/{lesson}",
                   key=f"genai/{lesson}")


PROMETHEUS_AREAS = ("introduction", "concepts", "practices", "instrumenting", "alerting", "guides", "operating")


def prometheus_docs():
    root = RAW / "prometheus-docs" / "docs"
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if rel.parts[0] not in PROMETHEUS_AREAS:
            continue
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        url_path = rel.with_suffix("").as_posix().removesuffix("/index")
        yield dict(title=meta.get("title") or path.stem, description="", body=clean_hugo(body),
                   role="DevOps Engineer", topic="Prometheus Monitoring", source="Prometheus Documentation",
                   license="Apache-2.0", url=f"https://prometheus.io/docs/{url_path}/", key=f"prometheus/{url_path}")


def hardway_docs():
    for path in sorted((RAW / "kubernetes-the-hard-way" / "docs").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        h1 = re.search(r"^#\s+(.+)$", text, flags=re.M)
        yield dict(title=f"Kubernetes the Hard Way: {h1.group(1).strip() if h1 else path.stem}", description="",
                   body=re.sub(r"^#\s+.+$", "", text, count=1, flags=re.M), role="DevOps Engineer",
                   topic="Kubernetes the Hard Way", source="Kubernetes the Hard Way (Kelsey Hightower)",
                   license="Apache-2.0",
                   url=f"https://github.com/kelseyhightower/kubernetes-the-hard-way/blob/master/docs/{path.name}",
                   key=f"k8s-hard-way/{path.stem}")


GITHUB_AREAS = (("get-started/using-git/", ALL_ROLES, "Git & Version Control"),
                ("get-started/git-basics/", ALL_ROLES, "Git & Version Control"),
                ("pull-requests/get-started/", ALL_ROLES, "Pull Requests & Code Review"),
                ("pull-requests/concepts/", ALL_ROLES, "Pull Requests & Code Review"),
                ("actions/concepts/", BACKEND_DEVOPS, "GitHub Actions CI/CD"),
                ("actions/get-started/", BACKEND_DEVOPS, "GitHub Actions CI/CD"),
                ("actions/tutorials/", BACKEND_DEVOPS, "GitHub Actions CI/CD"))


def github_docs():
    root = RAW / "github-docs" / "content"
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        area = next((a for a in GITHUB_AREAS if rel.startswith(a[0])), None)
        if not area or path.name == "index.md":
            continue
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        title = clean_github(meta.get("title") or path.stem).strip()
        yield dict(title=title, description=clean_github(meta.get("intro", "")), body=clean_github(body),
                   role=area[1], topic=area[2], source="GitHub Docs", license="CC BY 4.0",
                   url=f"https://docs.github.com/en/{rel.removesuffix('.md')}", key=f"github/{rel.removesuffix('.md')}")


def sqlite_docs():
    for path in sorted((RAW / "sqlite-docs").glob("*.html")):
        title, body = html_markdown(path.read_text(encoding="utf-8"), "body",
                                    ".menu, .searchmenu, .nosearch, #document_title, .fancy_toc, #toc",
                                    title_from_page=True)
        title = re.sub(r"^SQLite\s*[:-]?\s*", "", title or path.stem)
        yield dict(title=f"SQLite: {title}", description="", body=body, role=DATABASE_BACKEND,
                   topic="SQLite", source="SQLite Documentation", license="Public Domain",
                   url=f"https://www.sqlite.org/{path.name}", key=f"sqlite/{path.stem}")


# ---------- non-technical roles (services/interview-service/app/core/role_profiles.json) ----------

ROLE_PROFILES = json.loads((REPO / "services/interview-service/app/core/role_profiles.json").read_text())["roles"]
ROLE_TOPIC = {"HR Manager": "Human Resource Management", "Digital Marketing Executive": "Digital Marketing",
              "Finance Executive": "Finance & Accounting", "English Copywriter": "Copywriting & Content",
              "Graphic Designer": "Graphic Design", "Assistant Brand Manager": "Brand Management"}
WIKI_DROP = ("See also", "References", "Further reading", "External links", "Notes", "Bibliography", "Sources",
             "Citations", "Footnotes", "Notes and references")


def clean_jekyll(text: str) -> str:
    text = re.sub(r"\{%.*?%\}|\{\{.*?\}\}", "", text, flags=re.S)
    return re.sub(r"\{:[^}\n]*\}", "", text)                         # kramdown attributes, e.g. ![x](y){: role="img"}


def onet_profiles():
    """One profile per role from O*NET: description, core tasks, key knowledge, skills and technology."""
    import csv
    base = next((RAW / "onet" / "extracted").glob("*/"))
    def rows(name):
        with open(base / f"{name}.txt", encoding="utf-8") as f:
            return list(csv.DictReader(f, delimiter="\t"))
    occupations = {r["O*NET-SOC Code"]: r for r in rows("Occupation Data")}
    tasks, knowledge, skills = rows("Task Statements"), rows("Knowledge"), rows("Essential Skills") + rows("Transferable Skills")
    software = rows("Software Skills")
    def top(table, codes, threshold):
        scores = {}
        for r in table:
            if r["O*NET-SOC Code"] in codes and r["Scale ID"] == "IM" and float(r["Data Value"]) >= threshold:
                scores[r["Element Name"]] = max(scores.get(r["Element Name"], 0), float(r["Data Value"]))
        return [f"{name} (importance {score:.1f}/5)" for name, score in sorted(scores.items(), key=lambda x: -x[1])]
    for role, profile in ROLE_PROFILES.items():
        codes = set(profile["onet"])
        parts = [f"Profile of the {role} role, compiled from the O*NET occupations "
                 + ", ".join(f"{occupations[c]['Title']} ({c})" for c in profile["onet"]) + "."]
        for c in profile["onet"]:
            parts.append(f"## {occupations[c]['Title']}\n\n{occupations[c]['Description']}")
        core = [r["Task"] for r in tasks if r["O*NET-SOC Code"] in codes and r["Task Type"] == "Core"]
        parts.append("## Core tasks\n\n" + "\n".join(f"- {t}" for t in dict.fromkeys(core)))
        parts.append("## Most important knowledge areas\n\n" + "\n".join(f"- {k}" for k in top(knowledge, codes, 3.0)))
        parts.append("## Most important skills\n\n" + "\n".join(f"- {k}" for k in top(skills, codes, 3.25)))
        tech = sorted({r["Element Name"] for r in software if r["O*NET-SOC Code"] in codes and r["Hot Technology"] == "Y"})
        if tech:
            parts.append("## Common technology\n\n" + ", ".join(tech) + ".")
        yield dict(title=f"Role profile: {role}", description="", body="\n\n".join(parts), role=role,
                   topic="Role Profile", source="O*NET 31.0 Database (U.S. Department of Labor, ETA)",
                   license="CC BY 4.0", url=f"https://www.onetonline.org/link/summary/{profile['onet'][0]}",
                   key=f"onet/{re.sub(r'[^a-z0-9]+', '-', role.lower())}")


def wikipedia_docs():
    roles_of = {}
    for role, profile in ROLE_PROFILES.items():
        for title in profile["wikipedia"]:
            roles_of.setdefault(title, []).append(role)
    for path in sorted((RAW / "wikipedia").glob("*.json")):
        article = json.loads(path.read_text())
        roles = roles_of.get(article["requested"])
        if not roles:
            continue
        text = re.sub(r"^===\s*(.+?)\s*===\s*$", r"### \1", article["text"], flags=re.M)
        text = re.sub(r"^==\s*(.+?)\s*==\s*$", r"## \1", text, flags=re.M)
        text = re.sub(r"^=+\s*(.+?)\s*=+\s*$", r"#### \1", text, flags=re.M)
        yield dict(title=article["title"], description="", body=drop_sections(text, WIKI_DROP),
                   role=" / ".join(roles), topic=ROLE_TOPIC[roles[0]],
                   source="Wikipedia (Wikipedia contributors)", license="CC BY-SA 4.0", url=article["url"],
                   key=f"wikipedia/{path.stem}")


ROLE_PAGES = (  # (folder under role-pages, role, topic, source, licence, content selector)
    ("google-search", "Digital Marketing Executive", "SEO (Google Search Central)", "Google Search Central",
     "CC BY 4.0", ".devsite-article-body", "nav, aside, .devsite-article-meta, .devsite-page-rating"),
    ("eeoc", "HR Manager", "Employment Law & HR Practice (US)", "U.S. Equal Employment Opportunity Commission",
     "Public Domain", "article", "nav, aside, form, .rdf-meta"),
    # OPM's <main> wraps menus and the "Resources For" sidebar around the content
    ("opm", "HR Manager", "Employment Law & HR Practice (US)", "U.S. Office of Personnel Management",
     "Public Domain", "main", "nav, header, footer, aside, form, [class*=nav], [class*=menu], [class*=sidebar], "
     "[class*=breadcrumb], [class*=skip], [class*=resources]"),
)
PAGE_JUNK_LINES = re.compile(r"^\s*(#+\s*)?(resources for\b.*|skip to main content|opm\.gov /.*|\d+\. home|"
                             r"[*-] (new / prospective employees|federal employees|hr professionals|managers))\s*$",
                             re.I | re.M)


def role_page_docs():
    for folder, role, topic, source, lic, selector, junk in ROLE_PAGES:
        root = RAW / "role-pages" / folder
        urls = json.loads((root / "index.json").read_text())
        for path in sorted(root.glob("*.html")):
            title, body = html_markdown(path.read_text(encoding="utf-8", errors="ignore"), selector, junk,
                                        title_from_page=folder != "google-search")   # Google: title is the h1
            title = re.split(r"\s+[|\-–]\s+", title)[0].strip()
            yield dict(title=title or path.stem, description="", body=PAGE_JUNK_LINES.sub("", body), role=role,
                       topic=topic, source=source, license=lic, url=urls.get(path.name, ""),
                       key=f"{folder}/{path.stem}")


JEKYLL_GUIDES = (  # (folder, path globs, role, topic, source, licence, base url)
    ("uswds-site", ("pages/design-principles/**/*.md", "pages/design-tokens/**/*.md", "pages/patterns/**/*.md"),
     "Graphic Designer", "Visual Design Systems", "U.S. Web Design System (GSA)", "Public Domain (CC0)",
     "https://designsystem.digital.gov"),
    ("plainlanguage", ("_pages/guidelines/**/*.md",), "English Copywriter", "Plain Language Writing",
     "PlainLanguage.gov (GSA)", "Public Domain (CC0)", "https://www.plainlanguage.gov"),
    ("18f-content-guide", ("_pages/our-approach/*.md", "_pages/our-style/*.md"), "English Copywriter",
     "Content Style", "18F Content Guide (GSA)", "Public Domain", "https://guides.18f.gov/content-guide"),
    ("18f-brand", ("pages/introduction.md", "pages/principles.md", "pages/logo.md", "pages/color-palette.md",
                   "pages/typography.md", "pages/icons.md", "pages/templates.md"),
     "Graphic Designer / Assistant Brand Manager", "Brand Guidelines", "18F Brand Guidelines (GSA)",
     "Public Domain", "https://brand.18f.gov"),
)


def jekyll_guide_docs():
    for folder, globs, role, topic, source, lic, base in JEKYLL_GUIDES:
        root = RAW / folder
        for path in sorted({p for g in globs for p in root.glob(g)}):
            meta, body = front_matter(path.read_text(encoding="utf-8"))
            permalink = meta.get("permalink") or "/" + path.relative_to(root).with_suffix("").as_posix()
            yield dict(title=meta.get("title") or path.stem, description=meta.get("lead", ""),
                       body=clean_jekyll(body), role=role, topic=topic, source=source, license=lic,
                       url=base.rstrip("/") + permalink, key=f"{folder}/{path.relative_to(root).with_suffix('').as_posix()}")

# ---------- output ----------


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    written, seen, skipped = Counter(), Counter(), Counter()
    for source in (k8s_docs, docker_docs, mdn_docs, postgres_docs, azure_docs, guide_docs, genai_docs,
                   prometheus_docs, hardway_docs, github_docs, sqlite_docs,
                   onet_profiles, wikipedia_docs, role_page_docs, jekyll_guide_docs):
        for doc in source():
            body = clean_markdown(doc["body"])
            if doc["description"] and doc["description"] not in body:
                body = f"{clean_markdown(doc['description'])}\n\n{body}"
            if len(body) < MIN_CHARS:
                skipped[source.__name__] += 1
                continue
            # The loader matches documents on (title, topic, role): keep titles unique
            title = doc["title"].strip()
            seen[(title, doc["topic"])] += 1
            if seen[(title, doc["topic"])] > 1:
                title = f"{title} ({doc['key'].split('/')[-1].replace('-', ' ').replace('_', ' ')})"
            header = "\n".join(f"<!-- {k}: {doc[k]} -->" for k in ("role", "topic", "source", "license", "url"))
            target = OUT / f"{doc['key'].replace('/', '__')}.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"{header}\n# {title}\n\n{body}\n", encoding="utf-8")
            written[doc["source"]] += 1
    (OUT / "ATTRIBUTION.md").write_text(ATTRIBUTION, encoding="utf-8")
    for name, n in written.items():
        print(f"{n:5d}  {name}")
    print(f"skipped (under {MIN_CHARS} chars): {dict(skipped)}")
    size = sum(p.stat().st_size for p in OUT.glob("*.md"))
    print(f"{sum(written.values())} documents, {size / 1e6:.1f} MB -> {OUT.relative_to(REPO)}")


ATTRIBUTION = """# Attribution for external curriculum documents

Generated by scripts/datasets/build_learning_corpus.py. Each file's header names its source page,
licence and URL; the text was converted to plain markdown (markup and link targets removed).

- Kubernetes Documentation, (c) The Kubernetes Authors, CC BY 4.0 - https://github.com/kubernetes/website
- Docker Documentation, (c) Docker Inc., Apache-2.0 - https://github.com/docker/docs
- MDN Web Docs, by Mozilla Contributors, CC BY-SA 2.5 - https://github.com/mdn/content
  (share-alike: redistributed derivatives of these files must keep CC BY-SA)
- PostgreSQL Documentation, (c) The PostgreSQL Global Development Group, PostgreSQL Licence -
  https://www.postgresql.org/about/licence/
- Azure Architecture Center, (c) Microsoft, CC BY 4.0 - https://github.com/MicrosoftDocs/architecture-center
- The Open Guide to AWS, by its contributors, CC BY 4.0 - https://github.com/open-guides/og-aws
- The System Design Primer, (c) Donne Martin, CC BY 4.0 - https://github.com/donnemartin/system-design-primer
- The Art of Command Line, by Joshua Levy and contributors, CC BY-SA 4.0 -
  https://github.com/jlevy/the-art-of-command-line (share-alike)
- Generative AI for Beginners, (c) Microsoft, MIT - https://github.com/microsoft/generative-ai-for-beginners
- Prometheus Documentation, (c) Prometheus Authors, Apache-2.0 - https://github.com/prometheus/docs
- Kubernetes the Hard Way, (c) Kelsey Hightower, Apache-2.0 - https://github.com/kelseyhightower/kubernetes-the-hard-way
- GitHub Docs, (c) GitHub Inc., CC BY 4.0 - https://github.com/github/docs
- SQLite Documentation, public domain - https://www.sqlite.org/copyright.html
- O*NET 31.0 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA),
  used under the CC BY 4.0 licence; O*NET(R) is a trademark of USDOL/ETA - https://www.onetcenter.org/license_db.html
- Wikipedia articles, by Wikipedia contributors, CC BY-SA 4.0 (share-alike); each file links its article -
  https://en.wikipedia.org/wiki/Wikipedia:Text_of_the_Creative_Commons_Attribution-ShareAlike_4.0_International_License
- Google Search Central documentation, (c) Google, CC BY 4.0 - https://developers.google.com/search
- U.S. Web Design System, PlainLanguage.gov, 18F Content Guide and 18F Brand (GSA), public domain / CC0
- U.S. EEOC and OPM guidance pages, U.S. government works in the public domain (U.S. law context)
"""

if __name__ == "__main__":
    main()
