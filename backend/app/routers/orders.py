from __future__ import annotations

import re
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..database import get_db
from ..deps import get_current_user
from ..models import CartItem, Interaction, Order, OrderItem, Product, User
from ..schemas import CheckoutRequest, OrderOut

router = APIRouter(prefix="/api/orders", tags=["orders"])


def order_query():
    return select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.product)
    )


@router.get("", response_model=list[OrderOut])
def list_orders(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrderOut]:
    orders = db.scalars(
        order_query().where(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(min(limit, 200))
    ).unique().all()
    return [OrderOut.model_validate(order) for order in orders]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> OrderOut:
    order = db.scalars(order_query().where(Order.id == order_id, Order.user_id == user.id)).unique().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return OrderOut.model_validate(order)


@router.post("/checkout", response_model=OrderOut, status_code=201)
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderOut:
    cart_items = db.scalars(
        select(CartItem).options(joinedload(CartItem.product)).where(CartItem.user_id == user.id)
    ).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Your bag is empty.")

    card_digits = re.sub(r"\D", "", payload.payment_card)
    if len(card_digits) < 12:
        raise HTTPException(status_code=400, detail="Enter a valid card number.")
    if not re.match(r"^\d{2}\s?/\s?\d{2}$", payload.payment_expiry.strip()):
        raise HTTPException(status_code=400, detail="Enter the expiry as MM/YY.")
    if not payload.payment_cvc.isdigit():
        raise HTTPException(status_code=400, detail="Enter a valid CVC.")

    for cart_item in cart_items:
        if not cart_item.product.is_active:
            raise HTTPException(status_code=400, detail=f"{cart_item.product.name} is no longer available.")
        if cart_item.quantity > cart_item.product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Only {cart_item.product.stock} units of {cart_item.product.name} are available.",
            )

    total = round(sum(item.product.price * item.quantity for item in cart_items), 2)
    year = datetime.utcnow().year
    order = Order(
        reference=f"SW-{year}-{secrets.token_hex(3).upper()}",
        user_id=user.id,
        total=total,
        status="Confirmed",
        payment_method="Card",
        payment_last4=card_digits[-4:],
        shipping_name=payload.shipping_name,
        shipping_address=payload.shipping_address,
        shipping_city=payload.shipping_city,
        shipping_postcode=payload.shipping_postcode,
        shipping_country=payload.shipping_country,
    )
    db.add(order)
    db.flush()

    for cart_item in cart_items:
        product = cart_item.product
        product.stock -= cart_item.quantity
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_code=product.code,
                quantity=cart_item.quantity,
                unit_price=product.price,
                line_total=round(product.price * cart_item.quantity, 2),
            )
        )
        db.add(Interaction(user_id=user.id, product_id=product.id, event_type="purchase", weight=3.0))
        db.delete(cart_item)

    db.commit()
    order = db.scalars(order_query().where(Order.id == order.id)).unique().first()
    return OrderOut.model_validate(order)
