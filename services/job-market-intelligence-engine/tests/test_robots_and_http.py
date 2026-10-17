"""robots.txt rules and the polite HTTP client. No network: a fake session answers requests."""

from dataclasses import dataclass, field
from urllib.robotparser import RobotFileParser

import pytest
import requests

from app.collectors.http import (
    OffSiteURL,
    PoliteClient,
    RobotsDisallowed,
    SiteBlocked,
    build_user_agent,
)
from app.collectors.robots import RobotsPolicy

UA = build_user_agent("researcher@example.com")
BASE = "https://jobs.example"

# Shaped like ikman.lk's file: two separate "*" groups, with wildcards.
IKMAN_LIKE = """
User-agent: *
Disallow: /*?query=

User-agent: Googlebot
Allow: /

User-agent: *
Disallow: /*--
"""


# --- robots.txt ---------------------------------------------------------------------------------


def test_robotparser_alone_misses_wildcards_and_later_groups():
    parser = RobotFileParser()
    parser.parse(IKMAN_LIKE.splitlines())
    assert parser.can_fetch(UA, f"{BASE}/en/ads/jobs?query=it")  # the gap our policy closes


def test_policy_applies_wildcards_from_every_star_group():
    policy = RobotsPolicy.from_text(IKMAN_LIKE, UA)
    assert not policy.allowed(f"{BASE}/en/ads/jobs?query=it")
    assert not policy.allowed(f"{BASE}/en/ad/software-engineer--colombo")
    assert policy.allowed(f"{BASE}/en/ads/sri-lanka/jobs")


def test_end_anchor_and_longest_match():
    policy = RobotsPolicy.from_text(
        "User-agent: *\nAllow: /jobs/public\nDisallow: /jobs\nDisallow: /*.pdf$\n", UA
    )
    assert policy.allowed(f"{BASE}/jobs/public/1")
    assert not policy.allowed(f"{BASE}/jobs/private")
    assert not policy.allowed(f"{BASE}/files/cv.pdf")
    assert policy.allowed(f"{BASE}/files/cv.pdf?download=1")


def test_group_for_our_bot_replaces_the_star_groups():
    text = "User-agent: *\nDisallow: /\n\nUser-agent: SkillBridge-Research-Bot\nDisallow: /admin\n"
    policy = RobotsPolicy.from_text(text, UA)
    assert policy.allowed(f"{BASE}/jobs")
    assert not policy.allowed(f"{BASE}/admin/users")


def test_empty_disallow_allows_everything_and_crawl_delay_is_read():
    policy = RobotsPolicy.from_text("User-agent: *\nDisallow:\nCrawl-delay: 8\n", UA)
    assert policy.allowed(f"{BASE}/anything")
    assert policy.crawl_delay == 8


# --- PoliteClient -------------------------------------------------------------------------------


@dataclass
class FakeResponse:
    status_code: int = 200
    text: str = ""
    url: str = ""
    headers: dict = field(default_factory=dict)

    @property
    def content(self) -> bytes:
        return self.text.encode()


class FakeSession:
    """Answers each URL with a queue of responses (or exceptions); records every request."""

    def __init__(self, routes):
        self.routes = {url: list(answers) for url, answers in routes.items()}
        self.requested = []

    def get(self, url, *, headers, timeout):
        self.requested.append(url)
        answers = self.routes.get(url) or [FakeResponse(status_code=404)]
        answer = answers.pop(0) if len(answers) > 1 else answers[0]
        if isinstance(answer, Exception):
            raise answer
        answer.url = answer.url or url
        return answer


class FixedRandom:
    def uniform(self, low, high):
        return 4.0


def make_client(routes, robots="User-agent: *\nDisallow: /private\n"):
    routes = {f"{BASE}/robots.txt": [FakeResponse(text=robots)], **routes}
    sleeps = []
    client = PoliteClient(
        BASE,
        "researcher@example.com",
        session=FakeSession(routes),
        sleep=sleeps.append,
        clock=lambda: 0.0,
        rng=FixedRandom(),
    )
    return client, client.session, sleeps


def test_user_agent_names_the_project_with_an_optional_contact():
    assert build_user_agent() == "SkillBridge-Research-Bot/0.1 (SLIIT student project; academic research)"
    assert UA.endswith("; contact: researcher@example.com)")
    assert "contact" not in PoliteClient(BASE).user_agent


def test_robots_is_checked_before_fetching():
    client, session, _ = make_client({})
    with pytest.raises(RobotsDisallowed):
        client.get(f"{BASE}/private/page")
    assert session.requested == [f"{BASE}/robots.txt"]


def test_waits_between_requests():
    client, _, sleeps = make_client({f"{BASE}/a": [FakeResponse()], f"{BASE}/b": [FakeResponse()]})
    client.get(f"{BASE}/a")
    client.get(f"{BASE}/b")
    assert sleeps == [4.0, 4.0]  # before /a (after robots.txt) and before /b


def test_crawl_delay_longer_than_our_delay_is_respected():
    client, _, sleeps = make_client(
        {f"{BASE}/a": [FakeResponse()]}, robots="User-agent: *\nCrawl-delay: 10\n"
    )
    client.get(f"{BASE}/a")
    assert sleeps == [10.0]


def test_retries_server_errors_with_backoff():
    client, session, sleeps = make_client(
        {f"{BASE}/a": [FakeResponse(500), FakeResponse(503), FakeResponse(200, "ok")]}
    )
    assert client.get(f"{BASE}/a").text == "ok"
    assert session.requested.count(f"{BASE}/a") == 3
    assert 5.0 in sleeps and 10.0 in sleeps  # backoff 5 s, then 10 s


def test_retries_network_errors():
    client, _, _ = make_client(
        {f"{BASE}/a": [requests.ConnectionError("reset"), FakeResponse(200, "ok")]}
    )
    assert client.get(f"{BASE}/a").text == "ok"


@pytest.mark.parametrize("status", [403, 429])
def test_403_or_429_stops_the_whole_site(status):
    client, session, _ = make_client({f"{BASE}/a": [FakeResponse(status)]})
    with pytest.raises(SiteBlocked):
        client.get(f"{BASE}/a")
    with pytest.raises(SiteBlocked):
        client.get(f"{BASE}/b")
    assert f"{BASE}/b" not in session.requested


def test_other_hosts_are_never_requested():
    client, session, _ = make_client({})
    with pytest.raises(OffSiteURL):
        client.get("https://other.example/page")
    assert session.requested == []


def test_missing_robots_txt_means_no_restrictions():
    client, _, _ = make_client({f"{BASE}/private/a": [FakeResponse()]}, robots="")
    client.session.routes[f"{BASE}/robots.txt"] = [FakeResponse(status_code=404)]
    assert client.get(f"{BASE}/private/a").status_code == 200


def test_robots_txt_redirecting_to_an_html_error_page_means_no_restrictions():
    client, _, _ = make_client({f"{BASE}/private/a": [FakeResponse()]})
    client.session.routes[f"{BASE}/robots.txt"] = [
        FakeResponse(text="<html>Error</html>", headers={"Content-Type": "text/html"})
    ]
    assert client.get(f"{BASE}/private/a").status_code == 200


def test_unreachable_robots_txt_blocks_the_site():
    client, _, _ = make_client({f"{BASE}/a": [FakeResponse()]})
    client.session.routes[f"{BASE}/robots.txt"] = [FakeResponse(status_code=500)]
    with pytest.raises(RobotsDisallowed):
        client.get(f"{BASE}/a")
