"""Company job posts (app/companies/): companies post jobs, an admin verifies them, students apply.

Runs on a temporary SQLite database; the Auth Service is replaced by a fixed set of tokens.
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update

from app.companies import auth, store
from app.companies.auth import Caller
from app.database.companies import application_cvs, company_vacancies, vacancy_applications
from app.database.contract import metadata, role_profile_requirements, role_profiles
from app.main import app

PEOPLE = {
    "hr": Caller(uuid.uuid4(), "Ishara Fernando", "hr@nuwaradigital.example", "hr"),
    "hr2": Caller(uuid.uuid4(), "Kasun Jayawardena", "talent@coralstone.example", "hr"),
    "student": Caller(uuid.uuid4(), "Sachini Wijesinghe", "sachini.w@student.example", "user"),
    "student2": Caller(uuid.uuid4(), "Nimesha Rathnayake", "nimesha.r@student.example", "user"),
    "admin": Caller(uuid.uuid4(), "Admin", "admin@skillaro.example", "admin"),
}
PDF = b"%PDF-1.4\n% a tiny test CV\n%%EOF\n"
DESCRIPTION = (
    "We are looking for a Junior Full-Stack Developer to join our product team.\n\n"
    "What you'll do:\n- Build web features with React and Node.js\n- Write REST APIs and work with PostgreSQL\n\n"
    "What we need:\n- A Bachelor's degree in Computer Science or IT\n- 1+ years of experience with JavaScript\n"
    "- Good communication and teamwork\n\n"
    "Nice to have:\n- Docker and AWS experience\n- A driving licence"
)
COMPANY = {"name": "Nuwara Digital Labs", "website": "nuwaradigital.example", "sector": "IT", "city": "Kandy"}


@pytest.fixture
def db(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'jobs.db'}"
    engine = create_engine(url)
    metadata.create_all(engine)
    monkeypatch.setenv("SKILLBRIDGE_DATABASE_URL", url)
    monkeypatch.setenv("SKILLBRIDGE_AUTH_URL", "http://auth.test/auth")
    monkeypatch.setenv("SKILLBRIDGE_SSKS_URL", "")
    monkeypatch.setattr(auth, "caller_from_token", lambda token, url: PEOPLE.get(token))
    store._shared["ids"] = None
    return engine


@pytest.fixture
def client(db):
    return TestClient(app)


def as_(who):
    return {"Authorization": f"Bearer {who}"}


def job(**changes):
    body = {
        "title": "Junior Full-Stack Developer", "career_level": "JUNIOR", "employment_type": "FULL_TIME",
        "location": "Kandy (hybrid)", "closing_date": str(date.today() + timedelta(days=30)),
        "apply_url": "nuwaradigital.example/careers", "description": DESCRIPTION, "status": "PUBLISHED",
        "skills": [{"name": "React", "importance": "REQUIRED"}, {"name": "node.js", "importance": "REQUIRED"},
                   {"name": "Docker & Kubernetes", "importance": "PREFERRED"}],
        "education": "Bachelor's degree", "minimum_years": 1, "certifications": ["Driving licence"],
    }
    return {**body, **changes}


def company_with_job(client, verify=True, **changes):
    assert client.post("/jobs/company", json=COMPANY, headers=as_("hr")).status_code == 201
    posted = client.post("/jobs/company/vacancies", json=job(**changes), headers=as_("hr"))
    assert posted.status_code == 201, posted.text
    if verify:
        company_id = client.get("/jobs/company", headers=as_("hr")).json()["company_id"]
        assert client.post(f"/jobs/admin/companies/{company_id}/verify", headers=as_("admin")).status_code == 200
    return posted.json()["vacancy_id"]


def apply(client, vacancy_id, who="student", cv=PDF, **fields):
    data = {"phone": "077 000 4412", "consent": "true", "education": "BSc (Hons) in IT, final year", **fields}
    files = {"cv": ("Sachini CV.pdf", cv, "application/pdf")} if cv is not None else None
    return client.post(f"/jobs/vacancies/{vacancy_id}/applications", data=data, files=files, headers=as_(who))


# --- logging in --------------------------------------------------------------------------------------------


def test_needs_a_login(client):
    assert client.get("/jobs/vacancies").status_code == 401
    assert client.get("/jobs/vacancies", headers=as_("nobody")).status_code == 401


def test_needs_the_auth_service_setting(client, monkeypatch):
    monkeypatch.setenv("SKILLBRIDGE_AUTH_URL", "")
    assert client.get("/jobs/vacancies", headers=as_("student")).status_code == 503


# --- companies -----------------------------------------------------------------------------------------------


def test_a_company_signs_up_and_waits_for_verification(client):
    created = client.post("/jobs/company", json=COMPANY, headers=as_("hr"))

    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "PENDING"
    assert (body["contact_name"], body["contact_email"]) == ("Ishara Fernando", "hr@nuwaradigital.example")
    assert client.post("/jobs/company", json=COMPANY, headers=as_("hr")).status_code == 409


def test_only_company_accounts_make_companies(client):
    assert client.post("/jobs/company", json=COMPANY, headers=as_("student")).status_code == 403
    assert client.get("/jobs/company", headers=as_("hr")).status_code == 404  # no company yet


def test_changing_the_name_sends_a_verified_company_back(client):
    company_with_job(client)
    assert client.get("/jobs/company", headers=as_("hr")).json()["status"] == "VERIFIED"

    assert client.patch("/jobs/company", json={"city": "Colombo"}, headers=as_("hr")).json()["status"] == "VERIFIED"
    changed = client.patch("/jobs/company", json={"name": "Nuwara Labs"}, headers=as_("hr")).json()

    assert changed["status"] == "PENDING"
    assert client.get("/jobs/vacancies", headers=as_("student")).json() == []


# --- finding skills -------------------------------------------------------------------------------------------


def test_finds_skills_education_years_and_certificates(client):
    client.post("/jobs/company", json=COMPANY, headers=as_("hr"))

    found = client.post("/jobs/company/skills", json={"title": "Junior Full-Stack Developer", "description": DESCRIPTION},
                        headers=as_("hr")).json()

    importance = {s["name"]: s["importance"] for s in found["skills"]}
    assert importance["React"] == "REQUIRED"
    assert importance["Communication"] == "REQUIRED"
    assert importance["Docker & Kubernetes"] == "PREFERRED"
    assert found["education"] == "Bachelor's degree"
    assert found["minimum_years"] == 1
    assert found["certifications"] == ["Driving licence"]


# --- posting and verifying ------------------------------------------------------------------------------------


def test_a_job_goes_live_only_after_the_company_is_verified(client):
    vacancy_id = company_with_job(client, verify=False)

    mine = client.get("/jobs/company/vacancies", headers=as_("hr")).json()
    assert [(v["state"], v["required"], v["preferred"]) for v in mine] == [
        ("WAITING", ["React", "Node.js"], ["Docker & Kubernetes"])]
    assert client.get("/jobs/vacancies", headers=as_("student")).json() == []

    company_id = client.get("/jobs/company", headers=as_("hr")).json()["company_id"]
    pending = client.get("/jobs/admin/companies", headers=as_("admin")).json()
    assert [(c["name"], c["status"], c["published"]) for c in pending] == [("Nuwara Digital Labs", "PENDING", 1)]
    assert client.post(f"/jobs/admin/companies/{company_id}/verify", headers=as_("student")).status_code == 403
    client.post(f"/jobs/admin/companies/{company_id}/verify", headers=as_("admin"))

    live = client.get("/jobs/vacancies", headers=as_("student")).json()
    assert [v["vacancy_id"] for v in live] == [vacancy_id]
    assert live[0]["state"] == "LIVE"
    assert live[0]["education"] == "Bachelor's degree" and live[0]["minimum_years"] == 1
    assert live[0]["certifications"] == ["Driving licence"]
    assert live[0]["apply_url"] is None  # shown only after applying


def test_rejecting_hides_the_jobs_and_reopen_undoes_it(client):
    company_with_job(client)
    company_id = client.get("/jobs/company", headers=as_("hr")).json()["company_id"]

    client.post(f"/jobs/admin/companies/{company_id}/reject", headers=as_("admin"))
    assert client.get("/jobs/vacancies", headers=as_("student")).json() == []
    assert client.get("/jobs/company/vacancies", headers=as_("hr")).json()[0]["state"] == "HIDDEN"

    reopened = client.post(f"/jobs/admin/companies/{company_id}/reopen", headers=as_("admin")).json()
    assert reopened["status"] == "PENDING"


def test_the_skills_are_a_vacancy_role_profile(client, db):
    vacancy_id = company_with_job(client)

    with db.connect() as conn:
        profile = conn.execute(select(role_profiles).where(role_profiles.c.vacancy_id == uuid.UUID(vacancy_id))).one()
        reqs = conn.execute(select(role_profile_requirements.c.standard_name, role_profile_requirements.c.demand_weight)
                            .where(role_profile_requirements.c.profile_id == profile.profile_id)).all()
    assert (profile.profile_type, profile.profile_status, profile.profile_version) == ("VACANCY", "PUBLISHED", "v1")
    assert profile.career_level == "JUNIOR"
    assert sorted((n, float(w)) for n, w in reqs) == [("Docker & Kubernetes", 0.5), ("Node.js", 1.0), ("React", 1.0)]


def test_editing_writes_a_new_profile_version(client, db):
    vacancy_id = company_with_job(client)

    edited = client.put(f"/jobs/company/vacancies/{vacancy_id}",
                        json=job(skills=[{"name": "Python", "importance": "REQUIRED"}]), headers=as_("hr"))

    assert edited.json()["required"] == ["Python"]
    with db.connect() as conn:
        versions = conn.execute(select(role_profiles.c.profile_version, role_profiles.c.profile_status)
                                .where(role_profiles.c.vacancy_id == uuid.UUID(vacancy_id))).all()
    assert sorted(versions) == [("v1", "ARCHIVED"), ("v2", "PUBLISHED")]


def test_publishing_needs_a_description_and_skills(client):
    client.post("/jobs/company", json=COMPANY, headers=as_("hr"))

    no_skills = client.post("/jobs/company/vacancies", json=job(skills=[]), headers=as_("hr"))
    no_text = client.post("/jobs/company/vacancies", json=job(description="Apply now"), headers=as_("hr"))
    past = client.post("/jobs/company/vacancies", json=job(closing_date=str(date.today() - timedelta(days=1))),
                       headers=as_("hr"))
    bad_link = client.post("/jobs/company/vacancies", json=job(apply_url="not a link"), headers=as_("hr"))
    draft = client.post("/jobs/company/vacancies", json=job(skills=[], description="", status="DRAFT"), headers=as_("hr"))

    assert [r.status_code for r in (no_skills, no_text, past, bad_link)] == [422, 422, 422, 422]
    assert draft.status_code == 201 and draft.json()["state"] == "DRAFT"
    publish = client.patch(f"/jobs/company/vacancies/{draft.json()['vacancy_id']}", json={"status": "PUBLISHED"},
                           headers=as_("hr"))
    assert publish.status_code == 422


def test_a_job_past_its_closing_date_is_not_live(client, db):
    vacancy_id = company_with_job(client)
    with db.begin() as conn:
        conn.execute(update(company_vacancies).values(closing_date=date.today() - timedelta(days=1)))

    assert client.get("/jobs/vacancies", headers=as_("student")).json() == []
    assert client.get(f"/jobs/vacancies/{vacancy_id}", headers=as_("student")).status_code == 404
    assert client.get("/jobs/company/vacancies", headers=as_("hr")).json()[0]["state"] == "EXPIRED"


def test_closing_and_reopening(client):
    vacancy_id = company_with_job(client)

    closed = client.patch(f"/jobs/company/vacancies/{vacancy_id}", json={"status": "CLOSED"}, headers=as_("hr"))
    assert closed.json()["state"] == "CLOSED"
    assert client.get("/jobs/vacancies", headers=as_("student")).json() == []
    reopened = client.patch(f"/jobs/company/vacancies/{vacancy_id}", json={"status": "PUBLISHED"}, headers=as_("hr"))
    assert reopened.json()["state"] == "LIVE"


def test_companies_only_see_their_own_jobs(client):
    vacancy_id = company_with_job(client)
    client.post("/jobs/company", json={**COMPANY, "name": "Coralstone Data Labs"}, headers=as_("hr2"))

    assert client.get("/jobs/company/vacancies", headers=as_("hr2")).json() == []
    assert client.get(f"/jobs/company/vacancies/{vacancy_id}", headers=as_("hr2")).status_code == 404


# --- applying ---------------------------------------------------------------------------------------------------


def test_a_student_applies_and_the_company_sees_the_applicant(client):
    vacancy_id = company_with_job(client)

    applied = apply(client, vacancy_id, note="I built two React projects.")
    assert applied.status_code == 201, applied.text
    assert applied.json()["status"] == "NEW"

    listed = client.get("/jobs/company/applications", headers=as_("hr")).json()
    assert [(a["full_name"], a["email"], a["phone"], a["status"], a["cv_file_name"]) for a in listed] == [
        ("Sachini Wijesinghe", "sachini.w@student.example", "077 000 4412", "NEW", "Sachini CV.pdf")]
    application_id = listed[0]["application_id"]
    assert client.get("/jobs/company", headers=as_("hr")).json()["new_applicants"] == 1

    read = client.get(f"/jobs/company/applications/{application_id}", headers=as_("hr")).json()
    assert read["status"] == "NEW" and read["note"] == "I built two React projects."  # reading changes nothing
    opened = client.patch(f"/jobs/company/applications/{application_id}", json={"status": "SEEN"}, headers=as_("hr")).json()
    assert opened["status"] == "SEEN"
    assert client.get("/jobs/applications", headers=as_("student")).json()["applications"][0]["status"] == "SEEN"

    shortlisted = client.patch(f"/jobs/company/applications/{application_id}", json={"status": "SHORTLISTED"},
                               headers=as_("hr"))
    assert shortlisted.json()["status"] == "SHORTLISTED"
    again = client.patch(f"/jobs/company/applications/{application_id}", json={"status": "SEEN"}, headers=as_("hr"))
    assert again.json()["status"] == "SHORTLISTED"  # opening it again doesn't undo the decision
    cv = client.get(f"/jobs/company/applications/{application_id}/cv", headers=as_("hr"))
    assert cv.content == PDF and cv.headers["content-type"] == "application/pdf"

    detail = client.get(f"/jobs/vacancies/{vacancy_id}", headers=as_("student")).json()
    assert detail["application_status"] == "SHORTLISTED"
    assert detail["apply_url"] == "https://nuwaradigital.example/careers"  # shown after applying


def test_other_companies_and_students_cant_see_an_application(client):
    vacancy_id = company_with_job(client)
    apply(client, vacancy_id)
    client.post("/jobs/company", json={**COMPANY, "name": "Coralstone Data Labs"}, headers=as_("hr2"))
    application_id = client.get("/jobs/company/applications", headers=as_("hr")).json()[0]["application_id"]

    assert client.get("/jobs/company/applications", headers=as_("hr2")).json() == []
    assert client.get(f"/jobs/company/applications/{application_id}/cv", headers=as_("hr2")).status_code == 404
    assert client.get("/jobs/company/applications", headers=as_("student")).status_code == 403
    assert client.delete(f"/jobs/applications/{application_id}", headers=as_("student2")).status_code == 404


def test_applying_checks_the_form(client):
    vacancy_id = company_with_job(client)

    assert apply(client, vacancy_id, consent="false").status_code == 422
    assert apply(client, vacancy_id, phone="call me").status_code == 422
    assert apply(client, vacancy_id, cv=b"not a pdf").status_code == 422
    assert apply(client, vacancy_id, cv=b"%PDF-" + b"0" * (2 * 1024 * 1024)).status_code == 413
    assert apply(client, vacancy_id, cv=None).status_code == 422  # no CV and none to reuse
    assert apply(client, vacancy_id, who="hr").status_code == 403
    assert apply(client, vacancy_id).status_code == 201
    assert apply(client, vacancy_id).status_code == 409


def test_a_second_application_can_reuse_the_last_cv(client):
    first = company_with_job(client)
    apply(client, first)
    second = client.post("/jobs/company/vacancies", json=job(title="QA Engineer"), headers=as_("hr")).json()["vacancy_id"]

    mine = client.get("/jobs/applications", headers=as_("student")).json()
    assert mine["last_cv"] == {"file_name": "Sachini CV.pdf", "size_bytes": len(PDF)}
    assert mine["last_phone"] == "077 000 4412"
    assert apply(client, second, cv=None).status_code == 201


def test_withdrawing_removes_the_details(client, db):
    vacancy_id = company_with_job(client)
    application_id = apply(client, vacancy_id).json()["application_id"]

    assert client.delete(f"/jobs/applications/{application_id}", headers=as_("student")).status_code == 204

    assert client.get("/jobs/company/applications", headers=as_("hr")).json() == []
    with db.connect() as conn:
        assert conn.execute(select(vacancy_applications)).all() == []
        assert conn.execute(select(application_cvs)).all() == []


def test_students_cant_apply_to_a_job_that_isnt_live(client):
    vacancy_id = company_with_job(client, verify=False)

    assert apply(client, vacancy_id).status_code == 404
