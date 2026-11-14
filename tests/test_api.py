from fastapi.testclient import TestClient

from api.app import app

DEMO_CREDENTIALS = {"username": "user126", "password": "refund-demo"}


def client() -> TestClient:
    return TestClient(app)


def authenticated_client() -> TestClient:
    test_client = client()
    response = test_client.post("/api/auth/login", json=DEMO_CREDENTIALS)
    assert response.status_code == 200
    return test_client


def test_login_creates_http_only_session_and_logout_revokes_it():
    test_client = client()
    response = test_client.post("/api/auth/login", json=DEMO_CREDENTIALS)
    assert response.status_code == 200
    assert response.json() == {"username": "user126", "demo": True}
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert test_client.get("/api/auth/session").status_code == 200
    assert test_client.delete("/api/auth/logout").status_code == 204
    assert test_client.get("/api/auth/session").status_code == 401


def test_invalid_login_and_protected_routes_are_rejected():
    test_client = client()
    assert test_client.get("/api/orders").status_code == 401
    response = test_client.post(
        "/api/auth/login", json={"username": "user123", "password": "refund-demo"}
    )
    assert response.status_code == 401


def test_authenticated_orders_are_scoped_to_session_customer():
    response = authenticated_client().get("/api/orders")
    assert response.status_code == 200
    orders = {order["name"]: order for order in response.json()}
    assert set(orders) == {"backpack", "water_bottle", "lunch_box"}
    assert orders["backpack"]["refundable"] is True
    assert orders["water_bottle"]["reason"] == "outside 30-day window"


def test_quote_and_ticket_revalidate_policy_amount():
    test_client = authenticated_client()
    items = [" backpack ", "water_bottle"]
    quote = test_client.post("/api/refunds/quote", json={"items": items})
    assert quote.status_code == 200
    assert quote.json()["amount"] == 45
    assert [line["reason"] for line in quote.json()["items"]] == [
        "eligible",
        "outside 30-day window",
    ]

    rejected = test_client.post("/api/refunds/tickets", json={"items": items, "refund_amount": 63})
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["expected_amount"] == 45

    ticket = test_client.post("/api/refunds/tickets", json={"items": items, "refund_amount": 45})
    assert ticket.status_code == 200
    assert ticket.json()["ticket_id"].startswith("RFD-")
    assert ticket.json()["simulated"] is True


def test_empty_quote_is_rejected():
    response = authenticated_client().post("/api/refunds/quote", json={"items": []})
    assert response.status_code == 422
