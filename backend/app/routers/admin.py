from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..config import ARTIFACTS_DIR, STATIC_DIR
from ..database import get_db
from ..deps import get_admin_user
from ..models import CartItem, Interaction, Order, OrderItem, Product, Review, User
from ..schemas import AdminProductInput, AdminProductUpdate, OrderOut, ProductOut, StatusResponse
from ..security import hash_password
from ..ml.recommender import get_recommender

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _model_metrics() -> dict:
    path = ARTIFACTS_DIR / "metrics.json"
    if not path.exists():
        return {"status": "not_trained", "message": "Run the training pipeline to generate metrics."}
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), _: User = Depends(get_admin_user)) -> dict:
    total_revenue = db.scalar(select(func.sum(Order.total))) or 0
    total_orders = db.scalar(select(func.count(Order.id))) or 0
    total_customers = db.scalar(select(func.count(User.id)).where(User.is_admin.is_(False))) or 0
    total_products = db.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True))) or 0
    low_stock = db.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True), Product.stock < 25)) or 0
    total_units = db.scalar(select(func.sum(OrderItem.quantity))) or 0
    avg_order = round(total_revenue / total_orders, 2) if total_orders else 0

    # Revenue for the last 30 days, grouped by day.
    revenue_rows = db.execute(
        select(func.date(Order.created_at), func.sum(Order.total), func.count(Order.id))
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    ).all()
    revenue_by_day = [{"date": str(day), "revenue": round(float(revenue or 0), 2), "orders": int(count)} for day, revenue, count in revenue_rows][-30:]

    category_rows = db.execute(
        select(Product.category, func.sum(OrderItem.line_total), func.sum(OrderItem.quantity))
        .join(Product, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .group_by(Product.category)
        .order_by(func.sum(OrderItem.line_total).desc())
    ).all()
    revenue_by_category = [{"category": c, "revenue": round(float(r or 0), 2), "units": int(u or 0)} for c, r, u in category_rows]

    top_rows = db.execute(
        select(Product.id, Product.name, Product.image, Product.category, func.sum(OrderItem.quantity).label("units"), func.sum(OrderItem.line_total).label("revenue"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.line_total).desc())
        .limit(8)
    ).all()
    top_products = [
        {"id": i, "name": n, "image": img, "category": cat, "units": int(u or 0), "revenue": round(float(r or 0), 2)}
        for i, n, img, cat, u, r in top_rows
    ]

    recent_orders = db.scalars(
        select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc()).limit(6)
    ).all()
    orders = [
        {"id": o.id, "reference": o.reference, "total": o.total, "status": o.status, "created_at": o.created_at.isoformat(), "items": sum(i.quantity for i in o.items)}
        for o in recent_orders
    ]

    event_rows = db.execute(
        select(Interaction.event_type, func.count(Interaction.id)).group_by(Interaction.event_type)
    ).all()
    events = {event: int(count) for event, count in event_rows}

    metrics = _model_metrics()
    return {
        "totals": {
            "revenue": round(float(total_revenue), 2),
            "orders": int(total_orders),
            "customers": int(total_customers),
            "products": int(total_products),
            "avg_order": avg_order,
            "low_stock": int(low_stock),
            "units": int(total_units),
        },
        "revenue_by_day": revenue_by_day,
        "revenue_by_category": revenue_by_category,
        "top_products": top_products,
        "recent_orders": orders,
        "events": events,
        "model": {
            "best_model": metrics.get("best_model", "Hybrid"),
            "metrics": metrics.get("models", {}),
            "trained_at": metrics.get("trained_at"),
            "dataset": metrics.get("dataset", {}),
        },
    }


@router.get("/products")
def admin_products(
    search: str = "",
    include_inactive: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> list[ProductOut]:
    stmt = select(Product)
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search}%"))
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    return [ProductOut.model_validate(p) for p in db.scalars(stmt.order_by(Product.id)).all()]


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    payload: AdminProductInput,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> ProductOut:
    code = f"NEW-{int(datetime.utcnow().timestamp() * 1000) % 1000000}"
    product = Product(
        code=code,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        price=payload.price,
        stock=payload.stock,
        image=payload.image or f"/static/products/placeholder.svg",
        material=payload.material,
        colour=payload.colour,
        rating=0,
        review_count=0,
        popularity=0,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductOut.model_validate(product)


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: AdminProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> ProductOut:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "is_active" and value is None:
            continue
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return ProductOut.model_validate(product)


@router.delete("/products/{product_id}", response_model=StatusResponse)
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_admin_user)) -> StatusResponse:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    product.is_active = False
    db.query(CartItem).filter(CartItem.product_id == product_id).delete()
    db.commit()
    return StatusResponse(message="Product removed from the shop.", detail="Historical orders retain their line items.")


@router.get("/orders", response_model=list[OrderOut])
def admin_orders(
    limit: int = 500,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> list[OrderOut]:
    orders = db.scalars(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.created_at.desc())
        .limit(min(limit, 1000))
    ).unique().all()
    return [OrderOut.model_validate(o) for o in orders]


@router.get("/model-metrics")
def model_metrics(_: User = Depends(get_admin_user)) -> dict:
    return _model_metrics()


@router.post("/retrain", response_model=StatusResponse)
def retrain(_: User = Depends(get_admin_user)) -> StatusResponse:
    from ..ml.train import train_pipeline

    result = train_pipeline(force=True)
    get_recommender().reload()
    plot_source = ARTIFACTS_DIR / "plots"
    plot_target = STATIC_DIR / "plots"
    plot_target.mkdir(parents=True, exist_ok=True)
    for plot in plot_source.glob("*.png"):
        shutil.copy2(plot, plot_target / plot.name)
    return StatusResponse(
        message="Models retrained successfully.",
        detail=f"Best model: {result.get('best_model', 'Hybrid')} | Evaluated users: {result.get('dataset', {}).get('evaluation_users', 0)}",
    )


@router.get("/users")
def admin_users(db: Session = Depends(get_db), _: User = Depends(get_admin_user)) -> list[dict]:
    rows = db.execute(
        select(User.id, User.name, User.email, User.created_at, func.count(Order.id))
        .outerjoin(Order, Order.user_id == User.id)
        .where(User.is_admin.is_(False))
        .group_by(User.id)
        .order_by(func.count(Order.id).desc())
        .limit(100)
    ).all()
    return [{"id": i, "name": n, "email": e, "joined": c.isoformat(), "orders": int(o)} for i, n, e, c, o in rows]
