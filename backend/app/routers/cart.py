from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import get_current_user
from ..models import CartItem, Interaction, Product, User
from ..schemas import CartItemCreate, CartItemOut, CartItemUpdate, CartOut, ProductOut

router = APIRouter(prefix="/api/cart", tags=["cart"])


def cart_payload(db: Session, user_id: int) -> CartOut:
    items = db.scalars(
        select(CartItem)
        .options(joinedload(CartItem.product))
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.created_at.asc())
    ).all()
    out = [
        CartItemOut(
            id=item.id,
            product=ProductOut.model_validate(item.product),
            quantity=item.quantity,
            line_total=round(item.product.price * item.quantity, 2),
        )
        for item in items
    ]
    return CartOut(items=out, subtotal=round(sum(i.line_total for i in out), 2), count=sum(i.quantity for i in out))


@router.get("", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CartOut:
    return cart_payload(db, user.id)


@router.post("/items", response_model=CartOut)
def add_to_cart(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    product = db.get(Product, payload.product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found.")
    if product.stock <= 0:
        raise HTTPException(status_code=400, detail="This product is currently out of stock.")
    item = db.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product.id)
    )
    new_quantity = payload.quantity + (item.quantity if item else 0)
    if new_quantity > product.stock:
        raise HTTPException(status_code=400, detail=f"Only {product.stock} units are available.")
    if item:
        item.quantity = new_quantity
    else:
        item = CartItem(user_id=user.id, product_id=product.id, quantity=payload.quantity)
        db.add(item)
    db.add(Interaction(user_id=user.id, product_id=product.id, event_type="cart_add", weight=2.0))
    db.commit()
    return cart_payload(db, user.id)


@router.patch("/items/{item_id}", response_model=CartOut)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id))
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    if payload.quantity > item.product.stock:
        raise HTTPException(status_code=400, detail=f"Only {item.product.stock} units are available.")
    item.quantity = payload.quantity
    db.commit()
    return cart_payload(db, user.id)


@router.delete("/items/{item_id}", response_model=CartOut)
def delete_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CartOut:
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id))
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    db.delete(item)
    db.commit()
    return cart_payload(db, user.id)


@router.delete("", response_model=CartOut)
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CartOut:
    items = db.scalars(select(CartItem).where(CartItem.user_id == user.id)).all()
    for item in items:
        db.delete(item)
    db.commit()
    return cart_payload(db, user.id)
