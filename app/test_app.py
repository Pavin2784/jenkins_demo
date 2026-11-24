import pytest
from app import create_app, db

@pytest.fixture()
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            from app import Product
            db.session.add(Product(name="Test item", description="For tests", price=10.0))
            db.session.commit()
        yield client

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"

def test_products(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    assert response.get_json()[0]["name"] == "Test item"

def test_create_order(client):
    response = client.post("/api/orders", json={
        "customer_name": "Demo Customer",
        "items": [{"product_id": 1, "quantity": 2}]
    })
    assert response.status_code == 201
    assert response.get_json()["total"] == 20.0

def test_reject_empty_order(client):
    response = client.post("/api/orders", json={"customer_name": "Demo", "items": []})
    assert response.status_code == 400
