import sqlite3


def login(client, email, password):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy", "service": "auth-service"}


def test_register_returns_the_new_user(client):
    response = client.post(
        "/auth/register",
        json={"full_name": "  Kasuni Silva ", "email": "Kasuni@Example.com", "password": "s3cure-pass"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Kasuni Silva"
    assert body["email"] == "kasuni@example.com"
    assert "password" not in body and "password_hash" not in body


def test_register_rejects_a_duplicate_email(client, registered_user):
    duplicate = {**registered_user, "email": registered_user["email"].upper()}

    response = client.post("/auth/register", json=duplicate)

    assert response.status_code == 409


def test_register_validates_input(client):
    bad_requests = [
        {"full_name": "A", "email": "a@example.com", "password": "long-enough"},
        {"full_name": "Valid Name", "email": "not-an-email", "password": "long-enough"},
        {"full_name": "Valid Name", "email": "a@example.com", "password": "short"},
    ]
    for body in bad_requests:
        assert client.post("/auth/register", json=body).status_code == 422, body


def test_password_is_stored_hashed(client, registered_user, tmp_path):
    with sqlite3.connect(tmp_path / "auth.db") as db:
        (stored,) = db.execute("SELECT password_hash FROM users").fetchone()

    assert stored != registered_user["password"]
    assert stored.startswith("$argon2")


def test_login_returns_a_token(client, registered_user):
    response = login(client, registered_user["email"], registered_user["password"])

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert body["access_token"]


def test_login_rejects_a_wrong_password_or_unknown_email(client, registered_user):
    assert login(client, registered_user["email"], "wrong-password").status_code == 401
    assert login(client, "nobody@example.com", "whatever-123").status_code == 401


def test_me_returns_the_logged_in_user(client, registered_user):
    token = login(client, registered_user["email"], registered_user["password"]).json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["full_name"] == registered_user["full_name"]


def test_me_rejects_missing_or_invalid_tokens(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
