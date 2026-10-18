"""Role types. Roles listed in role_profiles.json are non-technical (behavioural and situational questions,
competency-based grading); every other role is technical."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

PROFILE_PATH = Path(__file__).with_name("role_profiles.json")


@lru_cache
def non_technical_profiles() -> dict:
    return json.loads(PROFILE_PATH.read_text())["roles"]


def is_technical(role: Optional[str]) -> bool:
    return (role or "") not in non_technical_profiles()
