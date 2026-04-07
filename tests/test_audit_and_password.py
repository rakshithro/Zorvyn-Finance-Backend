from tests.conftest import make_user, login, auth_headers
from app.models.user import UserRole


# ── change password
def test_change_password_success(client, db):
    make_user(db, email="user@test.com", password="oldpass1")
    token = login(client, "user@test.com", "oldpass1")

    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "oldpass1", "new_password": "newpass99"},
        headers=auth_headers(token),
    )
    assert r.status_code == 204

    # old password is not valid
    r2 = client.post("/api/v1/auth/login", json={"email": "user@test.com", "password": "oldpass1"})
    assert r2.status_code == 401

    # new password will be valid
    r3 = client.post("/api/v1/auth/login", json={"email": "user@test.com", "password": "newpass99"})
    assert r3.status_code == 200


def test_change_password_wrong_current(client, db):
    make_user(db, email="user@test.com", password="correct")
    token = login(client, "user@test.com", "correct")

    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrong", "new_password": "newpass99"},
        headers=auth_headers(token),
    )
    assert r.status_code == 400
    assert "incorrect" in r.json()["detail"].lower()


def test_change_password_same_as_current(client, db):
    make_user(db, email="user@test.com", password="samepass")
    token = login(client, "user@test.com", "samepass")

    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "samepass", "new_password": "samepass"},
        headers=auth_headers(token),
    )
    assert r.status_code == 400
    assert "differ" in r.json()["detail"].lower()


def test_change_password_too_short(client, db):
    make_user(db, email="user@test.com", password="validpass")
    token = login(client, "user@test.com", "validpass")

    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "validpass", "new_password": "ab"},
        headers=auth_headers(token),
    )
    assert r.status_code == 422


def test_change_password_requires_auth(client):
    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "a", "new_password": "b"},
    )
    assert r.status_code == 401


# ── audit logs
TX_PAYLOAD = {
    "amount": 500,
    "type": "expense",
    "category": "food",
    "date": "2024-06-01",
}


def test_audit_log_created_on_transaction_create(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    token = login(client, "admin@test.com")

    client.post("/api/v1/transactions/", json=TX_PAYLOAD, headers=auth_headers(token))

    r = client.get("/api/v1/audit-logs/", headers=auth_headers(token))
    assert r.status_code == 200
    logs = r.json()
    actions = [l["action"] for l in logs]
    assert "CREATE_TRANSACTION" in actions


def test_audit_log_created_on_update_and_delete(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    token = login(client, "admin@test.com")

    tx_id = client.post("/api/v1/transactions/", json=TX_PAYLOAD, headers=auth_headers(token)).json()["id"]
    client.patch(f"/api/v1/transactions/{tx_id}", json={"amount": 999}, headers=auth_headers(token))
    client.delete(f"/api/v1/transactions/{tx_id}", headers=auth_headers(token))

    r = client.get("/api/v1/audit-logs/", headers=auth_headers(token))
    actions = {l["action"] for l in r.json()}
    assert "UPDATE_TRANSACTION" in actions
    assert "DELETE_TRANSACTION" in actions


def test_audit_logs_require_admin(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")

    r = client.get("/api/v1/audit-logs/", headers=auth_headers(token))
    assert r.status_code == 403


def test_audit_log_filter_by_action(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    token = login(client, "admin@test.com")

    tx_id = client.post("/api/v1/transactions/", json=TX_PAYLOAD, headers=auth_headers(token)).json()["id"]
    client.patch(f"/api/v1/transactions/{tx_id}", json={"amount": 800}, headers=auth_headers(token))

    r = client.get("/api/v1/audit-logs/?action=CREATE_TRANSACTION", headers=auth_headers(token))
    logs = r.json()
    assert all(l["action"] == "CREATE_TRANSACTION" for l in logs)