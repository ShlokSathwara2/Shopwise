"""Seed the Shopwise database from the prepared UCI Online Retail II data.

Usage (from repository root):
    python -m backend.app.seed --reset
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, func, select

from .config import BASE_DIR, DATA_DIR
from .database import Base, SessionLocal, engine
from .models import CartItem, Interaction, Order, OrderItem, Product, Review, User
from .security import hash_password

RNG = random.Random(2026)

REVIEW_TEMPLATES = {
    "positive": [
        ("Beautifully made", "This arrived beautifully wrapped and feels far more expensive than it is. It has become part of my everyday routine."),
        ("Exactly what I hoped for", "The quality is lovely and the colour is true to the photos. I would happily buy this again as a gift."),
        ("A new favourite", "Such a thoughtful little piece. It looks wonderful styled with the rest of my homeware and the finish is excellent."),
        ("Lovely detail", "Beautiful quality and a lovely weight to it. Delivery was quick and everything arrived safely packaged."),
    ],
    "mixed": [
        ("Lovely, with one small note", "Really pretty and well made overall. Slightly smaller than I expected, but still a lovely addition."),
        ("Good quality", "The piece itself is charming and feels sturdy. The colour is a little deeper than it appeared on screen."),
        ("Pleased overall", "A nice everyday piece and good value. Arrived on time, though the packaging was a little plain."),
    ],
    "neutral": [
        ("Nice enough", "Pretty design and matches the description. It is a simple piece and does what I expected."),
        ("Does the job", "A pleasant addition, though I think it is slightly overpriced for the size."),
    ],
}

SHIPPING_PLACES = [
    ("United Kingdom", ["12 Elm Grove", "8 Rosebery Road", "44 Camden Mews", "3 Harbour Lane"]),
    ("United States", ["145 Bleecker Street", "22 Willow Lane", "908 Juniper Way", "61 Mercer Street"]),
    ("Germany", ["Kastanienallee 18", "Rosenweg 7", "Lindenstrasse 42"]),
    ("France", ["14 Rue des Fleurs", "8 Rue du Temple", "27 Rue Oberkampf"]),
    ("Australia", ["31 Oxford Street", "6 Wattle Lane", "88 Brunswick Road"]),
]


def _chunks(rows: list[dict], size: int = 5000):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def _reference(year: int, n: int) -> str:
    return f"SW-{year}-H{n:05d}"


def _review_text(rating: int) -> tuple[str, str]:
    if rating >= 5:
        return RNG.choice(REVIEW_TEMPLATES["positive"])
    if rating == 4:
        return RNG.choice(REVIEW_TEMPLATES["positive"][:2] + REVIEW_TEMPLATES["mixed"])
    return RNG.choice(REVIEW_TEMPLATES["mixed"] + REVIEW_TEMPLATES["neutral"])


def seed_database(force: bool = False) -> dict:
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        if session.scalar(select(func.count(User.id))) and not force:
            print("[seed] database already contains users - skipping. Use --reset to rebuild.")
            return {"skipped": True}

        if force:
            print("[seed] clearing existing data...")
            for model in [Interaction, CartItem, OrderItem, Order, Review, Product, User]:
                session.execute(delete(model))
            session.commit()

        catalog = pd.read_csv(DATA_DIR / "catalog.csv")
        customers = pd.read_csv(DATA_DIR / "customers.csv")
        orders_df = pd.read_csv(DATA_DIR / "orders.csv", parse_dates=["invoice_date"])
        items_df = pd.read_csv(DATA_DIR / "order_items.csv")

        print(f"[seed] inserting {len(catalog)} products...")
        product_rows = []
        for i, row in catalog.reset_index(drop=True).iterrows():
            product_rows.append(
                {
                    "id": i + 1,
                    "code": str(row["code"]),
                    "name": str(row["name"]),
                    "description": str(row["description"]),
                    "category": str(row["category"]),
                    "price": float(row["price"]),
                    "stock": int(row["stock"]),
                    "rating": float(row["rating"]),
                    "review_count": int(row["review_count"]),
                    "image": str(row["image"]),
                    "material": str(row.get("material", "") or ""),
                    "colour": str(row.get("colour", "") or ""),
                    "popularity": int(row["popularity"]),
                    "is_active": True,
                    "created_at": datetime(2025, 1, 5, 9, 0),
                }
            )
        session.bulk_insert_mappings(Product, product_rows)
        session.commit()
        code_to_id = {row["code"]: row["id"] for row in product_rows}
        product_id_to_name = {row["id"]: row["name"] for row in product_rows}

        print(f"[seed] inserting {len(customers)} customers...")
        shared_hash = hash_password("shopper123")
        demo_hash = hash_password("demo1234")
        admin_hash = hash_password("admin1234")
        user_rows = []
        email_seen = {"demo@shopwise.com"}
        for _, row in customers.iterrows():
            email = str(row["email"]).strip().lower()
            if email in email_seen and not bool(row["is_demo"]):
                email = email.replace("@", f"+{int(row['user_id'])}@")
            email_seen.add(email)
            user_rows.append(
                {
                    "id": int(row["user_id"]),
                    "name": str(row["name"]),
                    "email": email,
                    "password_hash": demo_hash if bool(row["is_demo"]) else shared_hash,
                    "is_admin": False,
                    "created_at": datetime(2025, 2, 10, 10, 0) + timedelta(days=int(row["user_id"]) % 300),
                }
            )
        admin_id = int(customers["user_id"].max()) + 1
        user_rows.append(
            {
                "id": admin_id,
                "name": "Shopwise Admin",
                "email": "admin@shopwise.com",
                "password_hash": admin_hash,
                "is_admin": True,
                "created_at": datetime(2025, 1, 2, 9, 0),
            }
        )
        session.bulk_insert_mappings(User, user_rows)
        session.commit()

        print("[seed] inserting reviews...")
        review_rows = []
        review_id = 1
        for p in product_rows:
            pid = p["id"]
            base = float(p["rating"])
            n_reviews = 2 + int(hashlib.md5(str(pid).encode()).hexdigest()[:2], 16) % 5
            used_users: set[int] = set()
            for _ in range(n_reviews):
                uid = 2 + int(hashlib.md5(f"{pid}-{len(used_users)}-r".encode()).hexdigest()[:8], 16) % (len(customers) - 1)
                if uid in used_users:
                    continue
                used_users.add(uid)
                if base >= 4.5:
                    rating = RNG.choice([4, 5, 5, 5, 5])
                elif base >= 4.1:
                    rating = RNG.choice([4, 4, 5, 5])
                else:
                    rating = RNG.choice([3, 4, 4, 5])
                title, comment = _review_text(rating)
                created = datetime(2025, 8, 1) + timedelta(days=RNG.randint(0, 450), hours=RNG.randint(8, 21))
                review_rows.append(
                    {
                        "id": review_id,
                        "user_id": uid,
                        "product_id": pid,
                        "rating": rating,
                        "title": title,
                        "comment": comment,
                        "created_at": created,
                    }
                )
                review_id += 1
        for chunk in _chunks(review_rows, 3000):
            session.bulk_insert_mappings(Review, chunk)
        session.commit()

        # Recalculate product rating from the seeded reviews.
        rating_rows = session.execute(
            select(Review.product_id, func.avg(Review.rating), func.count(Review.id)).group_by(Review.product_id)
        ).all()
        for pid, avg, count in rating_rows:
            session.execute(
                Product.__table__.update()
                .where(Product.id == pid)
                .values(rating=round(float(avg), 2), review_count=int(count))
            )
        session.commit()

        print(f"[seed] inserting {len(orders_df)} historical orders and {len(items_df)} lines...")
        user_country = {int(r["user_id"]): str(r["country"]) for _, r in customers.iterrows()}
        user_name = {int(r["user_id"]): str(r["name"]) for _, r in customers.iterrows()}
        order_rows = []
        for _, row in orders_df.iterrows():
            country = user_country.get(int(row["user_id"]), "United Kingdom")
            place = next((p for p in SHIPPING_PLACES if p[0] == country), SHIPPING_PLACES[0])
            created = row["invoice_date"].to_pydatetime()
            order_rows.append(
                {
                    "id": int(row["order_id"]),
                    "reference": _reference(created.year, int(row["order_id"])),
                    "user_id": int(row["user_id"]),
                    "total": float(row["total"]),
                    "status": "Delivered",
                    "payment_method": "Card",
                    "payment_last4": f"{int(hashlib.md5(str(row['order_id']).encode()).hexdigest()[:4], 16) % 10000:04d}",
                    "shipping_name": user_name.get(int(row["user_id"]), ""),
                    "shipping_address": RNG.choice(place[1]),
                    "shipping_city": "New York" if place[0] == "United States" else "London",
                    "shipping_postcode": f"{RNG.randint(10, 99)}-{RNG.randint(100, 999)}",
                    "shipping_country": country,
                    "created_at": created,
                }
            )
        for chunk in _chunks(order_rows, 3000):
            session.bulk_insert_mappings(Order, chunk)
        session.commit()

        item_rows = []
        skipped = 0
        for idx, row in items_df.iterrows():
            pid = code_to_id.get(str(row["stock_code"]))
            if not pid:
                skipped += 1
                continue
            item_rows.append(
                {
                    "order_id": int(row["order_id"]),
                    "product_id": pid,
                    "product_name": str(row["product_name"]),
                    "product_code": str(row["stock_code"]),
                    "quantity": int(row["quantity"]),
                    "unit_price": float(row["unit_price"]),
                    "line_total": float(row["line_total"]),
                }
            )
        for chunk in _chunks(item_rows, 8000):
            session.bulk_insert_mappings(OrderItem, chunk)
        session.commit()
        print(f"[seed] order lines inserted: {len(item_rows):,} (skipped {skipped})")

        print("[seed] seeding interaction stream...")
        last_orders = (
            orders_df.sort_values("invoice_date").groupby("user_id").tail(3).sort_values("invoice_date")
        )
        order_user = dict(zip(orders_df["order_id"].astype(int), orders_df["user_id"].astype(int)))
        order_time = {int(row["order_id"]): row["invoice_date"].to_pydatetime() for _, row in orders_df.iterrows()}
        recent_order_ids = set(last_orders["order_id"].astype(int))
        interaction_rows = []
        iid = 1
        for row in item_rows:
            if row["order_id"] in recent_order_ids:
                interaction_rows.append(
                    {
                        "id": iid,
                        "user_id": order_user[row["order_id"]],
                        "product_id": row["product_id"],
                        "event_type": "purchase",
                        "weight": 3.0,
                        "created_at": order_time[row["order_id"]],
                        "meta": json.dumps({"order_id": int(row["order_id"]), "source": "historical_import"}),
                    }
                )
                iid += 1

        # Add authentic-looking browsing and basket events around the last orders.
        demo_user = 1
        demo_orders = orders_df[orders_df["user_id"] == demo_user]
        for _, order in demo_orders.iterrows():
            order_items = items_df[items_df["order_id"] == order["order_id"]]
            for _, item in order_items.head(4).iterrows():
                pid = code_to_id.get(str(item["stock_code"]))
                if not pid:
                    continue
                for offset, event_type, weight in [(3, "view", 0.5), (1, "cart_add", 2.0)]:
                    interaction_rows.append(
                        {
                            "id": iid,
                            "user_id": demo_user,
                            "product_id": pid,
                            "event_type": event_type,
                            "weight": weight,
                            "created_at": order["invoice_date"].to_pydatetime() - timedelta(days=offset),
                            "meta": json.dumps({"source": "seeded_browsing"}),
                        }
                    )
                    iid += 1

        # A light stream for the rest of the customer base.
        for _, customer in customers.sample(n=min(300, len(customers)), random_state=7).iterrows():
            for _ in range(RNG.randint(2, 5)):
                pid = RNG.randint(1, len(product_rows))
                event_type = RNG.choice(["view", "view", "view", "cart_add"])
                interaction_rows.append(
                    {
                        "id": iid,
                        "user_id": int(customer["user_id"]),
                        "product_id": pid,
                        "event_type": event_type,
                        "weight": 0.5 if event_type == "view" else 2.0,
                        "created_at": datetime.now() - timedelta(days=RNG.randint(0, 30), hours=RNG.randint(0, 23)),
                        "meta": json.dumps({"source": "seeded_browsing"}),
                    }
                )
                iid += 1

        for chunk in _chunks(interaction_rows, 8000):
            session.bulk_insert_mappings(Interaction, chunk)
        session.commit()

        # A ready-to-demo bag for the featured account.
        demo_cart = [1, 240, 520]
        for index, pid in enumerate(demo_cart):
            product = session.get(Product, pid)
            if product and product.is_active:
                session.add(CartItem(user_id=demo_user, product_id=pid, quantity=1 + index % 2))
        session.commit()

        stats = {
            "users": len(user_rows),
            "products": len(product_rows),
            "reviews": len(review_rows),
            "orders": len(order_rows),
            "order_items": len(item_rows),
            "interactions": len(interaction_rows),
        }
        (BASE_DIR / "data" / "seed_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        print("[seed] done:", json.dumps(stats))
        print("[seed] demo login:  demo@shopwise.com / demo1234")
        print("[seed] admin login: admin@shopwise.com / admin1234")
        return stats
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Shopwise database.")
    parser.add_argument("--reset", action="store_true", help="Delete existing data and reseed.")
    args = parser.parse_args()
    seed_database(force=args.reset)


if __name__ == "__main__":
    main()
