import pytest
from tests.conftest import make_user, login, auth_headers
from app.models.user import UserRole


TX_PAYLOAD = {
    "amount": 1500.00,
    "type": "income",
    "category": "salary",
    "date": "2024-03-01",
    "notes": "March salary",
}


# ── Helpers
def create_tx(client, token, payload=None):
    return client.post(
        "/api/v1/transactions/",
        json=payload or TX_PAYLOAD,
        headers=auth_headers(token),
    )


# ── Create 
def test_analyst_can_create_transaction(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")
    r = create_tx(client, token)
    assert r.status_code == 201
    data = r.json()
    assert data["amount"] == 1500.00
    assert data["category"] == "salary"


def test_admin_can_create_transaction(client, db):
    make_user(db, email="admin@test.com", role=UserRole.admin)
    token = login(client, "admin@test.com")
    r = create_tx(client, token)
    assert r.status_code == 201


def test_viewer_cannot_create_transaction(client, db):
    make_user(db, email="viewer@test.com", role=UserRole.viewer)
    token = login(client, "viewer@test.com")
    r = create_tx(client, token)
    assert r.status_code == 403


def test_create_tx_invalid_amount(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")
    r = create_tx(client, token, {**TX_PAYLOAD, "amount": -100})
    assert r.status_code == 422


# ── Read 
def test_analyst_sees_all_transactions(client, db):
    a1 = make_user(db, email="a1@test.com", role=UserRole.analyst)
    a2 = make_user(db, email="a2@test.com", role=UserRole.analyst)
    token1 = login(client, "a1@test.com")
    token2 = login(client, "a2@test.com")
    create_tx(client, token1)
    create_tx(client, token2)

    # analyst2 should see both
    r = client.get("/api/v1/transactions/", headers=auth_headers(token2))
    assert r.json()["total"] == 2


def test_viewer_sees_only_own_transactions(client, db):
    analyst = make_user(db, email="analyst@test.com", role=UserRole.analyst)
    viewer = make_user(db, email="viewer@test.com", role=UserRole.viewer)

    token_a = login(client, "analyst@test.com")
    token_v = login(client, "viewer@test.com")

    # Analyst creates a transaction; viewer has none
    create_tx(client, token_a)

    r = client.get("/api/v1/transactions/", headers=auth_headers(token_v))
    assert r.json()["total"] == 0


def test_filter_by_type(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")
    create_tx(client, token, {**TX_PAYLOAD, "type": "income"})
    create_tx(client, token, {**TX_PAYLOAD, "type": "expense", "category": "food"})

    r = client.get("/api/v1/transactions/?type=income", headers=auth_headers(token))
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["type"] == "income"


def test_pagination(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")
    for _ in range(5):
        create_tx(client, token)

    r = client.get("/api/v1/transactions/?page=1&page_size=2", headers=auth_headers(token))
    body = r.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["total_pages"] == 3


# ── Update 
def test_analyst_can_update_own_transaction(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")
    tx_id = create_tx(client, token).json()["id"]

    r = client.patch(
        f"/api/v1/transactions/{tx_id}",
        json={"amount": 2000.00, "notes": "updated"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200
    assert r.json()["amount"] == 2000.00


def test_viewer_cannot_update_transaction(client, db):
    analyst = make_user(db, email="analyst@test.com", role=UserRole.analyst)
    viewer = make_user(db, email="viewer@test.com", role=UserRole.viewer)
    token_a = login(client, "analyst@test.com")
    tx_id = create_tx(client, token_a).json()["id"]

    token_v = login(client, "viewer@test.com")
    r = client.patch(
        f"/api/v1/transactions/{tx_id}",
        json={"amount": 999},
        headers=auth_headers(token_v),
    )
    assert r.status_code == 403


# ── Delete 
def test_soft_delete_hides_transaction(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")
    tx_id = create_tx(client, token).json()["id"]

    r = client.delete(f"/api/v1/transactions/{tx_id}", headers=auth_headers(token))
    assert r.status_code == 204

    # Should no longer appear in list
    r = client.get("/api/v1/transactions/", headers=auth_headers(token))
    assert r.json()["total"] == 0


def test_delete_nonexistent_transaction(client, db):
    make_user(db, email="analyst@test.com", role=UserRole.analyst)
    token = login(client, "analyst@test.com")
    r = client.delete("/api/v1/transactions/9999", headers=auth_headers(token))
    assert r.status_code == 404