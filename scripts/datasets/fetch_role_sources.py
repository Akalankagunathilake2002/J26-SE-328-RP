"""Downloads the web sources for the non-technical roles (called by fetch_datasets.sh).

    python3 scripts/datasets/fetch_role_sources.py RAW_DIR

Reads services/interview-service/app/core/role_profiles.json and saves, under RAW_DIR:
  wikipedia/<title>.json      plain-text article via the MediaWiki API (CC BY-SA 4.0)
  role-pages/<source>/*.html  official pages: Google Search Central (CC BY 4.0), EEOC and OPM (US public domain)
Existing files are kept, so reruns only fetch what is missing.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAW = Path(sys.argv[1])
PROFILES = json.loads((REPO / "services/interview-service/app/core/role_profiles.json").read_text())["roles"]
# Wikimedia's API policy asks for a descriptive user agent with a contact URL
UA = ("SkillBridge-research-corpus/1.0 (https://github.com/Akalankagunathilake2002/J26-SE-328-RP; "
      "university project, non-commercial) python-urllib")

PAGES = {
    "google-search": [f"https://developers.google.com/search/docs/{p}" for p in (
        "fundamentals/seo-starter-guide", "fundamentals/how-search-works", "fundamentals/creating-helpful-content",
        "essentials", "essentials/spam-policies", "appearance/title-link", "appearance/snippet",
        "appearance/structured-data/intro-structured-data", "crawling-indexing/sitemaps/overview",
        "crawling-indexing/robots/intro", "appearance/page-experience", "appearance/core-web-vitals",
        "monitor-debug/search-console-start", "specialty/international/managing-multi-regional-sites",
        "crawling-indexing/url-structure", "crawling-indexing/links-crawlable", "appearance/google-images",
        "fundamentals/using-gen-ai-content")],
    "eeoc": [f"https://www.eeoc.gov/{p}" for p in (
        "prohibited-employment-policiespractices", "harassment", "retaliation", "pregnancy-discrimination",
        "disability-discrimination")],
    # PHP manual (CC BY 3.0 or later, PHP Documentation Group): language, OOP, security, web features, PDO
    "php-manual": [f"https://www.php.net/manual/en/{p}.php" for p in (
        "language.types.intro", "language.types.type-juggling", "language.types.declarations", "language.types.array",
        "language.types.string", "language.variables.scope", "language.constants", "language.operators.comparison",
        "control-structures.match", "functions.arguments", "functions.arrow", "language.oop5.basic",
        "language.oop5.properties", "language.oop5.visibility", "language.oop5.inheritance", "language.oop5.interfaces",
        "language.oop5.traits", "language.oop5.abstract", "language.oop5.static", "language.oop5.magic",
        "language.oop5.autoload", "language.namespaces.rationale", "class.exception", "language.generators.overview",
        "language.attributes.overview", "language.enumerations.overview", "language.references.whatare",
        "session.examples.basic", "features.cookies", "features.file-upload.post-method", "features.http-auth",
        "security.intro", "security.database.sql-injection", "security.filesystem", "security.variables",
        "pdo.prepared-statements", "pdo.connections", "pdo.transactions", "faq.passwords", "function.password-hash",
        "function.htmlspecialchars", "filter.examples.validation", "migration80.new-features",
        "migration81.new-features", "migration82.new-features")],
    "opm": [f"https://www.opm.gov/policy-data-oversight/{p}/" for p in (
        "performance-management", "performance-management/performance-management-cycle",
        "human-capital-management")],
}


def get(url: str, attempts: int = 5) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == attempts - 1:
                raise
            # Rate limited: wait as long as the server asks (or back off exponentially)
            time.sleep(float(e.headers.get("Retry-After") or 0) or 10 * 2 ** attempt)


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


def wikipedia():
    out = RAW / "wikipedia"
    out.mkdir(parents=True, exist_ok=True)
    titles = sorted({t for p in PROFILES.values() for t in p["wikipedia"]})
    missing = []
    for title in titles:
        path = out / f"{slug(title)}.json"
        if path.exists():
            continue
        params = {"action": "query", "prop": "extracts|info", "explaintext": 1, "redirects": 1, "inprop": "url",
                  "titles": title, "format": "json", "formatversion": 2}
        page = json.loads(get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)))["query"]["pages"][0]
        if page.get("missing") or not page.get("extract"):
            missing.append(title)
            continue
        path.write_text(json.dumps({"requested": title, "title": page["title"], "url": page["fullurl"],
                                    "revision": page.get("lastrevid"), "text": page["extract"]}))
        time.sleep(2)
    print(f"wikipedia: {len(list(out.glob('*.json')))} articles" + (f", missing: {missing}" if missing else ""))


def pages():
    for source, urls in PAGES.items():
        out = RAW / "role-pages" / source
        out.mkdir(parents=True, exist_ok=True)
        index = {}                                    # file name -> original URL, for citations
        for url in urls:
            path = out / f"{slug(urllib.parse.urlparse(url).path)}.html"
            index[path.name] = url
            if not path.exists():
                try:
                    path.write_bytes(get(url))
                except Exception as e:
                    print(f"  missing {url}: {e}")
                time.sleep(0.5)
        (out / "index.json").write_text(json.dumps(index, indent=1))
        print(f"{source}: {len(list(out.glob('*.html')))} pages")


if __name__ == "__main__":
    wikipedia()
    pages()
