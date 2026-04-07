from tests.conftest import make_user, login, auth_headers
from app.models.user import UserRole


def test_register_success(client):
    r = client.post("/api/v1/auth/register", json={
        "full_name": "Alice",
        "email": "alice@test.com",
        "password": "secret123",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "alice@test.com"
    assert data["role"] == "viewer"
    assert "hashed_password" not in data


def test_register_duplicate_email(client, db):
    make_user(db, email="dup@test.com")
    r = client.post("/api/v1/auth/register", json={
        "full_name": "Dup",
        "email": "dup@test.com",
        "password": "secret123",
    })
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"]


def test_register_short_password(client):
    r = client.post("/api/v1/auth/register", json={
        "full_name": "Bob",
        "email": "bob@test.com",
        "password": "123",
    })
    assert r.status_code == 422


def test_login_success(client, db):
    make_user(db, email="user@test.com", password="pass1234")
    r = client.post("/api/v1/auth/login", json={"email": "user@test.com", "password": "pass1234"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["token_type"] == "bearer"


def test_login_wrong_password(client, db):
    make_user(db, email="user@test.com", password="correct")
    r = client.post("/api/v1/auth/login", json={"email": "user@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_me_returns_profile(client, db):
    make_user(db, email="me@test.com")
    token = login(client, "me@test.com")
    r = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert r.status_code == 200
    assert r.json()["email"] == "me@test.com"


def test_me_without_token(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401