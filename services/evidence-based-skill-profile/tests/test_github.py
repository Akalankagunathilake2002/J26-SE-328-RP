import httpx
import pytest
from httpx import AsyncClient

from app.collection.github import (
    GitHubError, GitHubReader, package_json_packages, parse_github_url,
    pyproject_packages, requirements_packages,
)
from app.extraction.matcher import SkillEntry
from app.normalisation.normaliser import Normaliser
from app.profile.builder import SubmittedDocument, build_profile
from app.schemas.evidence import EvidenceType, SourceType
from app.schemas.extraction import DocumentExtraction

ENTRIES = [
    SkillEntry("SK-1", "Python", ()), SkillEntry("SK-2", "JavaScript", ()),
    SkillEntry("SK-3", "Django", ()), SkillEntry("SK-4", "React", ()),
    SkillEntry("SK-5", "PyTorch", ()), SkillEntry("SK-6", "Machine Learning", ()),
    SkillEntry("SK-7", "Docker", ()),
]

REPOS = [
    {"full_name": "amal/attendance", "default_branch": "main", "size": 120, "fork": False,
     "topics": ["machine-learning"]},
    {"full_name": "amal/copied", "default_branch": "main", "size": 50, "fork": True},
    {"full_name": "amal/empty", "default_branch": "main", "size": 0, "fork": False},
]
FILES = {
    "requirements.txt": "Django>=4.2  # web\ntorch==2.1\nrequests\n-r dev.txt\n",
    "package.json": '{"dependencies": {"react": "^18", "react-dom": "^18"},'
                    ' "devDependencies": {"@types/node": "20"}}',
    "README.md": "Attendance system",
}


def github(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if url.endswith("/users/amal/repos?per_page=100&sort=pushed"):
        return httpx.Response(200, json=REPOS)
    if url.endswith("/repos/amal/attendance"):
        return httpx.Response(200, json=REPOS[0])
    if url.endswith("/repos/amal/attendance/languages"):
        return httpx.Response(200, json={"Python": 7000, "JavaScript": 2800, "Dockerfile": 200})
    if url.endswith("/repos/amal/attendance/contents/"):
        return httpx.Response(200, json=[{"name": n, "type": "file"} for n in FILES])
    if url.startswith("https://raw.githubusercontent.com/amal/attendance/main/"):
        return httpx.Response(200, text=FILES[url.rsplit("/", 1)[1]])
    if "ratelimited" in url:
        return httpx.Response(403)
    return httpx.Response(404)


@pytest.fixture
def reader():
    readme = lambda text: DocumentExtraction(  # noqa: E731
        source_type=SourceType.PROJECT_DESCRIPTION, sections=[], mentions=[], skills=[])
    return GitHubReader(httpx.Client(transport=httpx.MockTransport(github)), Normaliser(ENTRIES),
                        readme, max_repos=8, min_language_share=0.05)


def test_parse_github_url():
    assert parse_github_url("https://github.com/amal") == ("amal", None)
    assert parse_github_url("github.com/amal/attendance.git/") == ("amal", "attendance")
    with pytest.raises(GitHubError):
        parse_github_url("https://gitlab.com/amal")


def test_dependency_parsers():
    assert requirements_packages(FILES["requirements.txt"]) == ["Django", "torch", "requests"]
    assert package_json_packages(FILES["package.json"]) == ["react", "react-dom"]
    toml = ('[project]\ndependencies = ["fastapi>=0.1", "uvicorn"]\n'
            '[tool.poetry.dependencies]\npython = "^3.11"\nflask = "*"\n')
    assert pyproject_packages(toml) == ["fastapi", "uvicorn", "flask"]
    assert package_json_packages("not json") == [] and pyproject_packages("[[") == []


def test_reads_own_repositories_only(reader):
    found = reader.read("https://github.com/amal")
    # No forks, no empty repositories; the README is a separate project-description document.
    assert [(r.name, r.source) for r in found] == [
        ("amal/attendance", SourceType.PORTFOLIO_LINK),
        ("amal/attendance (README)", SourceType.PROJECT_DESCRIPTION)]


def test_languages_dependencies_and_topics_become_portfolio_evidence(reader):
    repo, _readme = reader.read("https://github.com/amal/attendance")
    mentions = repo.extraction.mentions
    assert {m.name for m in mentions} == {
        "Python", "JavaScript", "Django", "PyTorch", "React", "Machine Learning",
    }
    assert {m.evidence_type for m in mentions} == {EvidenceType.PORTFOLIO_SUPPORTED}
    python = next(m for m in mentions if m.name == "Python")
    assert python.sentence == "amal/attendance: written in Python (70% of the code)"
    assert sum(m.name == "React" for m in mentions) == 2  # react and react-dom, both in package.json
    # Dockerfile is only 2% of the code; "requests" and "@types/node" are not skills.
    assert "Docker" not in {m.name for m in mentions}


def test_errors(reader):
    with pytest.raises(GitHubError, match="could not find"):
        reader.read("https://github.com/nobody")
    with pytest.raises(GitHubError, match="rate limit"):
        reader.read("https://github.com/ratelimited")


def test_repositories_are_separate_portfolio_documents_in_the_profile(reader):
    profile = build_profile(
        [SubmittedDocument("cv.txt", b"", SourceType.CV)],
        extract=lambda d, n, s: DocumentExtraction(source_type=s, sections=[], mentions=[],
                                                   skills=[]),
        links=["https://github.com/amal"], read_link=reader.read)
    assert [(d.name, d.source_type) for d in profile.documents] == [
        ("cv.txt", "cv"), ("amal/attendance", "portfolio_link"),
        ("amal/attendance (README)", "project_description")]
    python = next(s for s in profile.skills if s.name == "Python")
    assert python.confidence_level == "strong"  # portfolio evidence is the strongest kind


@pytest.mark.anyio
async def test_build_endpoint_accepts_github_links(client: AsyncClient, reader):
    from app.main import app
    from app.profile.builder import default_link_reader

    app.dependency_overrides[default_link_reader] = lambda: reader.read
    try:
        response = await client.post("/api/v1/profile/build",
                                     data={"portfolio_links": ["https://github.com/amal"]})
        assert response.status_code == 200
        assert [d["name"] for d in response.json()["documents"]][0] == "amal/attendance"
        response = await client.post("/api/v1/profile/build",
                                     data={"portfolio_links": ["https://gitlab.com/x"]})
        assert response.status_code == 422
        response = await client.post("/api/v1/profile/build", data={})
        assert response.status_code == 422
        response = await client.post("/api/v1/profile/build", data={"portfolio_links": [""]})
        assert response.status_code == 422  # an empty link is ignored, so nothing was given
        response = await client.post(
            "/api/v1/profile/build", data={"portfolio_links": ["", "https://github.com/amal"]})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
