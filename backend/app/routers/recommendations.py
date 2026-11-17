from __future__ import annotations

import math
import time
from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_optional_user
from ..models import CartItem, Interaction, Order, OrderItem, Product, User
from ..schemas import ProductOut, RecommendationResponse
from ..ml.recommender import get_recommender

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

MODEL_LABELS = {
    "hybrid": "Hybrid recommender",
    "content_cf": "Content + collaborative",
    "popularity": "Popularity baseline",
    "content": "Content-based (TF-IDF)",
    "item_cf": "Item-to-item collaborative",
}


def _ordered_products(db: Session, product_ids: list[int]) -> list[Product]:
    if not product_ids:
        return []
    rows = db.scalars(
        select(Product).where(Product.id.in_(product_ids), Product.is_active.is_(True), Product.stock > 0)
    ).all()
    lookup = {p.id: p for p in rows}
    return [lookup[pid] for pid in product_ids if pid in lookup]


def _fallback(db: Session, limit: int, exclude: set[int], category: str | None = None) -> list[Product]:
    stmt = select(Product).where(
        Product.is_active.is_(True), Product.stock > 0, Product.id.notin_(exclude or {-1})
    )
    if category:
        stmt = stmt.where(Product.category == category)
    stmt = stmt.order_by(Product.popularity.desc(), Product.rating.desc(), Product.id.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def _top_up(
    db: Session,
    chosen: list[Product],
    limit: int,
    exclude: set[int],
    category: str | None = None,
) -> list[Product]:
    if len(chosen) >= limit:
        return chosen[:limit]
    seen = {p.id for p in chosen} | exclude
    for product in _fallback(db, limit * 2, seen, category):
        chosen.append(product)
        if len(chosen) >= limit:
            break
    return chosen[:limit]


def _diversify(candidates: list[Product], limit: int, max_per_category: int = 2) -> list[Product]:
    """Avoid a rail of eight near-identical bags; cap each category, then backfill."""
    picked: list[Product] = []
    seen: set[int] = set()
    counts: Counter[str] = Counter()
    for product in candidates:
        if product.id in seen:
            continue
        if counts[product.category] >= max_per_category:
            continue
        picked.append(product)
        seen.add(product.id)
        counts[product.category] += 1
        if len(picked) >= limit:
            return picked
    if len(picked) < limit:
        for product in candidates:
            if product.id in seen:
                continue
            picked.append(product)
            seen.add(product.id)
            if len(picked) >= limit:
                break
    return picked


def _user_history(db: Session, user_id: int) -> tuple[dict[int, float], set[int]]:
    weights: dict[int, float] = {}

    purchase_rows = db.execute(
        select(OrderItem.product_id, func.count(OrderItem.id))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.user_id == user_id, OrderItem.product_id.is_not(None))
        .group_by(OrderItem.product_id)
    ).all()
    purchased = set()
    for pid, count in purchase_rows:
        if pid is None:
            continue
        purchased.add(int(pid))
        weights[int(pid)] = 3.0 + math.log1p(int(count)) * 0.5

    cart_ids = set(
        db.scalars(select(CartItem.product_id).where(CartItem.user_id == user_id)).all()
    )
    exclude = purchased | {int(pid) for pid in cart_ids}

    event_rows = db.execute(
        select(Interaction.product_id, Interaction.event_type, Interaction.weight)
        .where(Interaction.user_id == user_id)
        .order_by(Interaction.created_at.desc())
        .limit(200)
    ).all()
    for pid, event_type, weight in event_rows:
        if pid is None or int(pid) in purchased:
            continue
        w = float(weight or 1.0)
        weights[int(pid)] = weights.get(int(pid), 0.0) + (w * 0.6 if event_type == "view" else w)
    return weights, exclude


def _payload(title: str, subtitle: str, strategy: str, started: float, products: list[Product], personalized: bool) -> RecommendationResponse:
    return RecommendationResponse(
        title=title,
        subtitle=subtitle,
        strategy=strategy,
        generated_ms=round((time.perf_counter() - started) * 1000, 2),
        personalized=personalized,
        model_label=MODEL_LABELS.get(strategy, strategy),
        items=[ProductOut.model_validate(p) for p in products],
    )


@router.get("/home", response_model=RecommendationResponse)
def home_recommendations(
    limit: int = Query(default=8, ge=1, le=24),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> RecommendationResponse:
    started = time.perf_counter()
    recommender = get_recommender()
    strategy = "popularity"
    if user:
        history, exclude = _user_history(db, user.id)
        ids, strategy = recommender.for_user(user.id, history, exclude, limit=limit * 8)
    else:
        ids, exclude = [], set()
        ids = recommender.popular(limit * 8)
    if not ids:
        ids = [p.id for p in _fallback(db, limit * 4, exclude)]
        strategy = "popularity"
    products = _ordered_products(db, ids)
    products = _diversify(products, limit, max_per_category=2)
    if len(products) < limit:
        seen = set(exclude) | {p.id for p in products}
        pool = products + _fallback(db, 200, seen)
        products = _diversify(pool, limit, max_per_category=2)
    products = products[:limit]

    if user and strategy in {"hybrid", "content_cf"}:
        title = f"Recommended for you, {user.name.split()[0]}"
        subtitle = "Pieces selected from your purchase history, recent views and what shoppers with similar taste love."
        personalized = True
    elif user:
        title = "A good place to start"
        subtitle = "Popular pieces from the Shopwise edit. Browse a few and your recommendations will become personal."
        personalized = False
    else:
        title = "Most loved this season"
        subtitle = "The pieces our customers are buying, saving and coming back for."
        personalized = False
    return _payload(title, subtitle, strategy, started, products, personalized)


@router.get("/trending", response_model=RecommendationResponse)
def trending(
    limit: int = Query(default=8, ge=1, le=24),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> RecommendationResponse:
    started = time.perf_counter()
    exclude: set[int] = set()
    if user:
        cart_ids = db.scalars(select(CartItem.product_id).where(CartItem.user_id == user.id)).all()
        exclude = {int(pid) for pid in cart_ids}
    recommender = get_recommender()
    ids = recommender.popular(limit * 2, exclude)
    products = _ordered_products(db, ids)
    products = _top_up(db, products, limit, exclude | {p.id for p in products})
    return _payload(
        "Trending now",
        "The most purchased pieces across the shop, refreshed as new orders arrive.",
        "popularity",
        started,
        products,
        False,
    )


@router.get("/similar/{product_id}", response_model=RecommendationResponse)
def similar_products(
    product_id: int,
    limit: int = Query(default=8, ge=1, le=24),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    started = time.perf_counter()
    product = db.get(Product, product_id)
    category = product.category if product else None
    recommender = get_recommender()
    ids = recommender.similar(product_id, limit * 3)
    products = _ordered_products(db, [pid for pid in ids if pid != product_id])
    if category:
        same_category = [p for p in products if p.category == category]
        other = [p for p in products if p.category != category]
        products = same_category + other
    products = _top_up(db, products, limit, {product_id} | {p.id for p in products}, category)
    return _payload(
        "Similar products",
        "Close matches from the same edit, scored on title, description and category with TF-IDF cosine similarity.",
        "content",
        started,
        products,
        False,
    )


@router.get("/also-bought/{product_id}", response_model=RecommendationResponse)
def also_bought(
    product_id: int,
    limit: int = Query(default=8, ge=1, le=24),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    started = time.perf_counter()
    product = db.get(Product, product_id)
    category = product.category if product else None
    recommender = get_recommender()
    ids = recommender.also_bought(product_id, limit * 2)
    products = _ordered_products(db, [pid for pid in ids if pid != product_id])
    products = _top_up(db, products, limit, {product_id} | {p.id for p in products}, category)
    return _payload(
        "Customers also bought",
        "Bought together by shoppers with similar baskets, from our item-based collaborative filter.",
        "item_cf",
        started,
        products,
        False,
    )


@router.get("/model-info")
def model_info() -> dict:
    return get_recommender().info()
