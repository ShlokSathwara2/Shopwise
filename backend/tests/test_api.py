"""Fast API smoke tests for Shopwise.

Run from the `shopwise/` folder:
    python -m pytest backend/tests -q
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["counts"]["products"] >= 1000
    assert body["recommender"]["ready"] is True


def test_shopper_login() -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@shopwise.com", "password": "demo1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "demo@shopwise.com"


def test_catalogue_and_search() -> None:
    response = client.get("/api/products", params={"page_size": 12, "sort": "featured"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1000
    assert len(body["items"]) == 12
    assert body["items"][0]["image"].startswith("/static/products/")

    search = client.get("/api/products", params={"search": "bowl", "page_size": 12})
    assert search.status_code == 200
    assert all(
        "bowl" in product["name"].lower()
        or "bowl" in product["description"].lower()
        or "bowl" in product["category"].lower()
        for product in search.json()["items"]
    )


def test_product_detail_and_reviews() -> None:
    detail = client.get("/api/products/291")
    assert detail.status_code == 200
    assert detail.json()["id"] == 291

    reviews = client.get("/api/products/291/reviews")
    assert reviews.status_code == 200
    assert isinstance(reviews.json(), list)


def test_recommendation_rails() -> None:
    token = client.post(
        "/api/auth/login",
        json={"email": "demo@shopwise.com", "password": "demo1234"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for path in [
        "/api/recommendations/home?limit=10",
        "/api/recommendations/trending?limit=10",
        "/api/recommendations/similar/291?limit=8",
        "/api/recommendations/also-bought/291?limit=8",
    ]:
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["items"]
        assert body["model_label"]


def test_admin_stats_requires_admin() -> None:
    assert client.get("/api/admin/stats").status_code in {401, 403}

    token = client.post(
        "/api/auth/login",
        json={"email": "admin@shopwise.com", "password": "admin1234"},
    ).json()["access_token"]
    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["totals"]["orders"] >= 7000
    assert body["totals"]["units"] >= 100000
    assert "revenue_by_category" in body
