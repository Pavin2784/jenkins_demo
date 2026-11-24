import os
import time
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False, default="")
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(500), nullable=False, default="")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    total = db.Column(db.Float, nullable=False)
    items = db.Column(db.JSON, nullable=False)

def create_app(test_config=None):
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL")
    if not database_url and os.getenv("DB_HOST"):
        db_user = os.getenv("DB_USER", "shopeasy")
        db_password = os.getenv("DB_PASSWORD", "")
        db_name = os.getenv("DB_NAME", "shopeasy")
        database_url = (
            f"postgresql+psycopg2://{db_user}:{db_password}"
            f"@{os.getenv('DB_HOST')}:5432/{db_name}"
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///shopeasy.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    @app.get("/api/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify(status="healthy", database="connected"), 200
        except Exception:
            db.session.rollback()
            return jsonify(status="unhealthy", database="unavailable"), 503

    @app.get("/api/products")
    def products():
        rows = Product.query.order_by(Product.id).all()
        return jsonify([{
            "id": p.id, "name": p.name, "description": p.description,
            "price": p.price, "image": p.image
        } for p in rows])

    @app.post("/api/orders")
    def create_order():
        payload = request.get_json(silent=True) or {}
        customer = str(payload.get("customer_name", "")).strip()
        items = payload.get("items", [])

        if not customer or not isinstance(items, list) or not items:
            return jsonify(error="customer_name and a non-empty items list are required"), 400

        total = 0.0
        normalized = []
        for item in items:
            try:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
            except (KeyError, TypeError, ValueError):
                return jsonify(error="Each item needs product_id and quantity"), 400
            if quantity < 1 or quantity > 50:
                return jsonify(error="Quantity must be between 1 and 50"), 400
            product = db.session.get(Product, product_id)
            if product is None:
                return jsonify(error=f"Product {product_id} was not found"), 404
            total += product.price * quantity
            normalized.append({
                "product_id": product.id, "name": product.name,
                "unit_price": product.price, "quantity": quantity
            })

        order = Order(customer_name=customer, total=round(total, 2), items=normalized)
        db.session.add(order)
        db.session.commit()
        return jsonify(
            message="Demo order created", order_id=order.id,
            customer_name=order.customer_name, total=order.total, items=order.items
        ), 201

    @app.get("/api/orders")
    def list_orders():
        rows = Order.query.order_by(Order.id.desc()).all()
        return jsonify([{
            "id": o.id, "customer_name": o.customer_name,
            "total": o.total, "items": o.items
        } for o in rows])

    with app.app_context():
        # Retry briefly while PostgreSQL starts in container environments.
        for attempt in range(15):
            try:
                db.create_all()
                if Product.query.count() == 0:
                    db.session.add_all([
                        Product(name="Wireless Headphones", description="Comfortable everyday headphones", price=49.99,
                                image="https://placehold.co/600x400?text=Headphones"),
                        Product(name="Smart Watch", description="Fitness and notification features", price=79.00,
                                image="https://placehold.co/600x400?text=Smart+Watch"),
                        Product(name="Travel Backpack", description="Everyday backpack with laptop sleeve", price=39.50,
                                image="https://placehold.co/600x400?text=Backpack"),
                        Product(name="Bluetooth Speaker", description="Portable wireless speaker", price=29.99,
                                image="https://placehold.co/600x400?text=Speaker")
                    ])
                    db.session.commit()
                break
            except Exception:
                db.session.rollback()
                if attempt == 14:
                    raise
                time.sleep(2)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
