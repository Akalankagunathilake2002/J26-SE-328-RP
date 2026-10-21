"""Collect skill evidence from a GitHub link (TAF task 2: portfolio / GitHub source).

A GitHub link (a user, https://github.com/name, or one repository, https://github.com/name/repo)
is read through the public GitHub REST API. Each of the student's own repositories (forks and
archived ones are skipped, at most settings.github_max_repos, most recently pushed first) becomes
one portfolio document with evidence from:

    languages      languages with at least settings.github_min_language_share of the code
    dependencies   requirements.txt, pyproject.toml, package.json: the libraries the code uses
    topics         tags the owner gave the repository
    README         the repository description, through the normal extraction pipeline

Languages, dependencies and topics are matched to skills by exact name only (after the package
name map below), never by AI guessing, so a package such as "requests" cannot become a random skill.
They are portfolio evidence (the strongest kind with certificates): the code itself shows the
skill. The README is only the owner's description of the project, so it is returned as a separate
project-description document ("<repo> (README)"), the same kind as an uploaded project report.
Each repository is a separate document, so several repositories using a skill are independent proof.

Only public data is read. Without a token GitHub allows 60 API requests an hour; set
GITHUB_TOKEN for 5,000. File contents come from raw.githubusercontent.com, which does not count.
"""
import json
import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

import httpx

from app.config.settings import get_settings
from app.extraction.matcher import load_entries
from app.normalisation.normaliser import Normaliser
from app.schemas.evidence import EvidenceType, SourceType
from app.schemas.extraction import DocumentExtraction, SectionType, SkillMention
from app.schemas.normalisation import MatchMethod

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
DEPENDENCY_FILES = ("requirements.txt", "pyproject.toml", "package.json")
README_NAMES = ("readme.md", "readme.rst", "readme.txt", "readme")
METHOD = "github"
URL = re.compile(r"^(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9-]+)(?:/([A-Za-z0-9._-]+))?/?$")
PACKAGE_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")

# Package and language names that differ from the skill's dictionary name.
PACKAGE_ALIASES = {
    "torch": "PyTorch", "torchvision": "PyTorch", "sklearn": "Scikit-learn",
    "opencv-python": "OpenCV", "opencv-contrib-python": "OpenCV",
    "opencv-python-headless": "OpenCV", "tensorflow-gpu": "TensorFlow",
    "djangorestframework": "Django", "psycopg2": "PostgreSQL", "psycopg2-binary": "PostgreSQL",
    "psycopg": "PostgreSQL", "pymongo": "MongoDB", "mongoose": "MongoDB",
    "mysqlclient": "MySQL", "pymysql": "MySQL", "mysql2": "MySQL",
    "react-dom": "React", "@angular/core": "Angular", "vue": "Vue.js", "next": "Next.js",
    "tailwindcss": "Tailwind CSS", "dockerfile": "Docker", "spacy": "spaCy",
}


class GitHubError(ValueError):
    """The link cannot be read (not a GitHub link, not found, or the rate limit was hit)."""


@dataclass(frozen=True)
class RepositoryEvidence:
    name: str
    extraction: DocumentExtraction
    source: SourceType = SourceType.PORTFOLIO_LINK


def parse_github_url(url: str) -> tuple[str, str | None]:
    """(owner, repository or None) from a GitHub link."""
    found = URL.match(url.strip())
    if not found:
        raise GitHubError(f"Not a GitHub user or repository link: {url!r}")
    owner, repo = found.group(1), found.group(2)
    return owner, repo.removesuffix(".git") if repo else None


def requirements_packages(text: str) -> list[str]:
    names = []
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith(("-", "git+", "http")):
            found = PACKAGE_NAME.match(line)
            if found:
                names.append(found.group(1))
    return names


def pyproject_packages(text: str) -> list[str]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return []
    names = [m.group(1) for dep in data.get("project", {}).get("dependencies", [])
             if (m := PACKAGE_NAME.match(dep))]
    poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    return names + [name for name in poetry if name.lower() != "python"]


def package_json_packages(text: str) -> list[str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    names = []
    for key in ("dependencies", "devDependencies"):
        names += [name for name in data.get(key, {}) if not name.startswith("@types/")]
    return names


PARSERS: dict[str, Callable[[str], list[str]]] = {
    "requirements.txt": requirements_packages,
    "pyproject.toml": pyproject_packages,
    "package.json": package_json_packages,
}


class GitHubReader:
    def __init__(self, client: httpx.Client, normaliser: Normaliser,
                 extract_text: Callable[[str], DocumentExtraction] | None = None,
                 max_repos: int = 8, min_language_share: float = 0.05):
        self.client, self.normaliser, self.extract_text = client, normaliser, extract_text
        self.max_repos, self.min_language_share = max_repos, min_language_share

    def _get(self, url: str) -> httpx.Response:
        response = self.client.get(url)
        if response.status_code == 404:
            raise GitHubError(f"GitHub could not find {url.removeprefix(API)}")
        if response.status_code in (403, 429):
            raise GitHubError("GitHub rate limit reached; try later or set GITHUB_TOKEN")
        response.raise_for_status()
        return response

    def _raw(self, full_name: str, branch: str, path: str) -> str | None:
        response = self.client.get(f"{RAW}/{full_name}/{branch}/{path}")
        return response.text if response.status_code == 200 else None

    def repositories(self, owner: str, repo: str | None) -> list[dict]:
        if repo:
            return [self._get(f"{API}/repos/{owner}/{repo}").json()]
        listed = self._get(f"{API}/users/{owner}/repos?per_page=100&sort=pushed").json()
        own = [r for r in listed if not r.get("fork") and not r.get("archived")
               and r.get("size", 0) > 0]
        return own[:self.max_repos]

    def _mentions(self, full_name: str, items: list[tuple[str, str]]) -> list[SkillMention]:
        """Exact-name mentions for (term, sentence) pairs; terms with no skill are dropped."""
        terms = [PACKAGE_ALIASES.get(term.lower(), term) for term, _ in items]
        mentions, seen = [], set()
        for (term, sentence), result in zip(items, self.normaliser.normalise(terms)):
            if result.method not in (MatchMethod.EXACT, MatchMethod.CLEANED):
                continue
            if (result.skill_id, sentence) in seen:
                continue
            seen.add((result.skill_id, sentence))
            mentions.append(SkillMention(
                skill_id=result.skill_id, name=result.name, matched_text=term, start=0,
                end=len(term), section=SectionType.PROJECTS, sentence=sentence, method=METHOD,
                match_method=result.method, match_score=result.score,
                evidence_type=EvidenceType.PORTFOLIO_SUPPORTED,
            ))
        return mentions

    def repository_evidence(self, repo: dict) -> list[RepositoryEvidence]:
        full_name, branch = repo["full_name"], repo.get("default_branch", "main")
        items: list[tuple[str, str]] = []

        languages = self._get(f"{API}/repos/{full_name}/languages").json()
        total = sum(languages.values()) or 1
        for language, size in languages.items():
            share = size / total
            if share >= self.min_language_share:
                items.append((language, f"{full_name}: written in {language} "
                                        f"({share:.0%} of the code)"))
        items += [(topic.replace("-", " "), f"{full_name}: topic '{topic}'")
                  for topic in repo.get("topics", [])]

        listing = self._get(f"{API}/repos/{full_name}/contents/").json()
        files = {item["name"].lower(): item["name"] for item in listing
                 if item.get("type") == "file"}
        for dependency_file, parse in PARSERS.items():
            if dependency_file in files:
                text = self._raw(full_name, branch, files[dependency_file]) or ""
                items += [(package, f"{full_name}: uses {package} ({dependency_file})")
                          for package in parse(text)]

        found = [RepositoryEvidence(full_name, DocumentExtraction(
            source_type=SourceType.PORTFOLIO_LINK, sections=[SectionType.PROJECTS],
            mentions=self._mentions(full_name, items), skills=[],
        ))]
        readme = next((files[name] for name in README_NAMES if name in files), None)
        if readme and self.extract_text:
            text = self._raw(full_name, branch, readme)
            if text:
                found.append(RepositoryEvidence(f"{full_name} (README)", self.extract_text(text),
                                                SourceType.PROJECT_DESCRIPTION))
        return found

    def read(self, url: str) -> list[RepositoryEvidence]:
        owner, repo = parse_github_url(url)
        try:
            return [part for r in self.repositories(owner, repo)
                    for part in self.repository_evidence(r)]
        except httpx.HTTPError as error:
            raise GitHubError(f"Could not read {url}: {error}") from error


@lru_cache
def get_github_reader() -> GitHubReader:
    from app.extraction.pipeline import extract_from_text

    settings = get_settings()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "skillbridge-c02"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    client = httpx.Client(headers=headers, timeout=20, follow_redirects=True)
    return GitHubReader(
        client, Normaliser(load_entries(settings.dictionary_path), use_fuzzy=False),
        lambda text: extract_from_text(text, SourceType.PROJECT_DESCRIPTION),
        settings.github_max_repos, settings.github_min_language_share,
    )
