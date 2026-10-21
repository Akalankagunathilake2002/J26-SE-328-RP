"""Split cleaned CV text into standard sections (TAF task 3).

The section is the strongest clue for the evidence type in task 6. Headings were collected from
the Kaggle IT and HR resumes ("Skills", "Highlights", "Work History", ...).
"""
import re

from app.schemas.extraction import Section, SectionType

HEADINGS: dict[SectionType, set[str]] = {
    SectionType.SUMMARY: {
        "summary", "professional summary", "executive summary", "executive profile", "profile",
        "professional profile", "career overview", "career summary", "objective",
        "career objective", "about me", "personal statement",
    },
    SectionType.SKILLS: {
        "skills", "technical skills", "key skills", "skill highlights", "highlights",
        "core qualifications", "qualifications", "summary of qualifications", "core competencies",
        "competencies", "areas of expertise", "expertise", "computer skills", "it skills",
        "technical proficiencies", "technologies", "tools and technologies", "soft skills",
        "languages", "skills and abilities",
    },
    SectionType.EXPERIENCE: {
        "experience", "professional experience", "work experience", "work history",
        "employment history", "employment", "relevant experience", "career history",
        "internship", "internships", "industry experience",
    },
    SectionType.PROJECTS: {
        "projects", "project", "academic projects", "personal projects", "key projects",
        "project experience", "selected projects",
    },
    SectionType.EDUCATION: {
        "education", "education and training", "academic background", "academic qualifications",
        "educational qualifications", "coursework", "relevant coursework", "modules",
    },
    SectionType.CERTIFICATIONS: {
        "certifications", "certification", "certificates", "licenses",
        "certifications and licenses", "licenses and certifications", "professional certifications",
    },
    SectionType.ACCOMPLISHMENTS: {
        "accomplishments", "core accomplishments", "achievements", "awards", "honors",
        "activities and honors", "awards and honors", "publications",
    },
    SectionType.OTHER: {
        "additional information", "interests", "hobbies", "affiliations",
        "professional affiliations", "personal information", "references", "volunteer work",
        "volunteer experience", "activities", "extracurricular activities",
    },
}
HEADING_TO_SECTION = {heading: section for section, names in HEADINGS.items() for heading in names}
ALL_HEADINGS = set(HEADING_TO_SECTION)
NON_LETTERS = re.compile(r"[^a-z ]+")


def heading_type(line: str) -> SectionType | None:
    """Return the section a heading line starts, or None when the line is not a heading."""
    key = NON_LETTERS.sub(" ", line.lower().replace("&", " and "))
    key = " ".join(key.split())
    return HEADING_TO_SECTION.get(key)


def split_sections(text: str) -> list[Section]:
    """Split text into sections; text before the first heading is the header (name, job title)."""
    sections: list[Section] = []
    current_type, current_heading = SectionType.HEADER, ""
    body_lines: list[str] = []
    body_start = 0
    position = 0

    def close() -> None:
        body = "\n".join(body_lines)
        if body.strip():
            sections.append(Section(type=current_type, heading=current_heading, text=body,
                                    start=body_start))

    for line in text.split("\n"):
        found = heading_type(line)
        if found is not None:
            close()
            current_type, current_heading = found, line
            body_lines = []
            body_start = position + len(line) + 1
        else:
            if not body_lines:
                body_start = position
            body_lines.append(line)
        position += len(line) + 1
    close()
    return sections
