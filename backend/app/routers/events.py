from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_optional_user
from ..models import Interaction, Product, User
from ..schemas import InteractionCreate, StatusResponse

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("", response_model=StatusResponse)
def log_event(
    payload: InteractionCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> StatusResponse:
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    weights = {"view": 0.5, "cart_add": 2.0, "purchase": 3.0}
    db.add(
        Interaction(
            user_id=user.id if user else None,
            product_id=product.id,
            event_type=payload.event_type,
            weight=weights.get(payload.event_type, 1.0),
            meta=__import__("json").dumps(payload.meta or {}),
        )
    )
    db.commit()
    return StatusResponse(message="Event recorded.")
