from tests.conftest import make_user, login, auth_headers
from app.models.user import UserRole


TX_INCOME = {"amount": 5000, "type": "income", "category": "salary", "date": "2024-03-01"}
TX_EXPENSE = {"amount": 1200, "type": "expense", "category": "rent", "date": "2024-03-05"}


# ── dashboard and summary
def test_dashboard_summary_structure(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")

    client.post("/api/v1/transactions/", json=TX_INCOME, headers=auth_headers(token))
    client.post("/api/v1/transactions/", json=TX_EXPENSE, headers=auth_headers(token))

    r = client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert r.status_code == 200
    data = r.json()

    assert data["total_income"] == 5000.0
    assert data["total_expenses"] == 1200.0
    assert data["net_balance"] == 3800.0
    assert data["total_transactions"] == 2
    assert len(data["monthly_trends"]) >= 1
    assert len(data["recent_transactions"]) == 2
    assert len(data["category_totals"]) == 2


def test_dashboard_empty_state(client, db):
    make_user(db, email="viewer@test.com", role=UserRole.viewer)
    token = login(client, "viewer@test.com")
    r = client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total_income"] == 0
    assert data["net_balance"] == 0
    assert data["recent_transactions"] == []


def test_viewer_dashboard_scoped(client, db):
    """Viewer's dashboard should only count their own records."""
    analyst = make_user(db, email="analyst@test.com", role=UserRole.analyst)
    viewer = make_user(db, email="viewer@test.com", role=UserRole.viewer)
    token_a = login(client, "analyst@test.com")
    token_v = login(client, "viewer@test.com")

    # Analyst adds 2 transactions
    client.post("/api/v1/transactions/", json=TX_INCOME, headers=auth_headers(token_a))
    client.post("/api/v1/transactions/", json=TX_EXPENSE, headers=auth_headers(token_a))

    # Viewer's dashboard should show 0
    r = client.get("/api/v1/dashboard/summary", headers=auth_headers(token_v))
    assert r.json()["total_transactions"] == 0


def test_dashboard_requires_auth(client):
    r = client.get("/api/v1/dashboard/summary")
    assert r.status_code == 401


# ── user Management 
def test_admin_can_list_users(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    make_user(db, email="other@test.com", role=UserRole.viewer)
    token = login(client, "admin@test.com")
    r = client.get("/api/v1/users/", headers=auth_headers(token))
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_viewer_cannot_list_users(client, db):
    make_user(db, email="viewer@test.com", role=UserRole.viewer)
    token = login(client, "viewer@test.com")
    r = client.get("/api/v1/users/", headers=auth_headers(token))
    assert r.status_code == 403


def test_admin_can_update_user_role(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    target = make_user(db, email="target@test.com", role=UserRole.viewer)
    token = login(client, "admin@test.com")

    r = client.patch(
        f"/api/v1/users/{target.id}",
        json={"role": "analyst"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["role"] == "analyst"


def test_admin_can_deactivate_user(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    target = make_user(db, email="target@test.com", role=UserRole.viewer)
    token = login(client, "admin@test.com")

    r = client.patch(
        f"/api/v1/users/{target.id}",
        json={"is_active": False},
        headers=auth_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_deactivated_user_cannot_login(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    target = make_user(db, email="target@test.com", role=UserRole.viewer)
    token = login(client, "admin@test.com")

    # Deactivate
    client.patch(
        f"/api/v1/users/{target.id}",
        json={"is_active": False},
        headers=auth_headers(token),
    )

    # Existing token should now fail
    r = client.get("/api/v1/auth/me", headers=auth_headers(login(client, "admin@test.com")))
    assert r.status_code == 200  # admin still works

    # Target can't use their token
    target_token = login.__wrapped__ if hasattr(login, "__wrapped__") else None
    r2 = client.post("/api/v1/auth/login", json={"email": "target@test.com", "password": "password123"})
    assert r2.status_code == 403


def test_admin_can_delete_user(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    target = make_user(db, email="delete@test.com", role=UserRole.viewer)
    token = login(client, "admin@test.com")

    r = client.delete(f"/api/v1/users/{target.id}", headers=auth_headers(token))
    assert r.status_code == 204

    r2 = client.get(f"/api/v1/users/{target.id}", headers=auth_headers(token))
    assert r2.status_code == 404