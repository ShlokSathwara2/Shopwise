from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, Review, User
from ..deps import get_current_user
from ..schemas import ProductListResponse, ProductOut, ReviewCreate, ReviewOut

router = APIRouter(prefix="/api/products", tags=["products"])

SORTS = {
    "featured": (Product.popularity.desc(), Product.rating.desc()),
    "rating": (Product.rating.desc(), Product.review_count.desc()),
    "price_asc": (Product.price.asc(), Product.name.asc()),
    "price_desc": (Product.price.desc(), Product.name.asc()),
    "newest": (Product.id.desc(),),
    "name": (Product.name.asc(),),
}


@router.get("/categories")
def categories(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(Product.category, func.count(Product.id))
        .where(Product.is_active.is_(True))
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
    ).all()
    return [{"name": name, "count": count} for name, count in rows]


@router.get("", response_model=ProductListResponse)
def list_products(
    search: str = "",
    category: str = "",
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str = "featured",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=60),
    in_stock: bool = False,
    db: Session = Depends(get_db),
) -> ProductListResponse:
    stmt = select(Product).where(Product.is_active.is_(True))
    for term in [t for t in search.strip().split() if t][:6]:
        pattern = f"%{term}%"
        stmt = stmt.where(or_(Product.name.ilike(pattern), Product.description.ilike(pattern), Product.category.ilike(pattern)))
    if category:
        wanted = [c.strip() for c in category.split(",") if c.strip()]
        if wanted:
            stmt = stmt.where(Product.category.in_(wanted))
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    if in_stock:
        stmt = stmt.where(Product.stock > 0)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order_by = SORTS.get(sort, SORTS["featured"])
    products = db.scalars(stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)).all()
    return ProductListResponse(
        items=[ProductOut.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductOut:
    product = db.get(Product, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found.")
    return ProductOut.model_validate(product)


@router.get("/{product_id}/reviews", response_model=list[ReviewOut])
def get_reviews(product_id: int, db: Session = Depends(get_db)) -> list[ReviewOut]:
    rows = db.execute(
        select(Review, User.name)
        .join(User, Review.user_id == User.id)
        .where(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .limit(30)
    ).all()
    return [
        ReviewOut(
            id=review.id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            created_at=review.created_at,
            user_name=name,
        )
        for review, name in rows
    ]


@router.post("/{product_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    product_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewOut:
    product = db.get(Product, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found.")
    existing = db.scalar(select(Review).where(Review.user_id == user.id, Review.product_id == product_id))
    if existing:
        existing.rating = payload.rating
        existing.title = payload.title
        existing.comment = payload.comment
        review = existing
    else:
        review = Review(user_id=user.id, product_id=product_id, **payload.model_dump())
        db.add(review)
    db.flush()
    avg_rating = db.scalar(select(func.avg(Review.rating)).where(Review.product_id == product_id)) or payload.rating
    count = db.scalar(select(func.count(Review.id)).where(Review.product_id == product_id)) or 1
    product.rating = round(float(avg_rating), 2)
    product.review_count = int(count)
    db.commit()
    db.refresh(review)
    return ReviewOut(
        id=review.id,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        created_at=review.created_at,
        user_name=user.name,
    )
