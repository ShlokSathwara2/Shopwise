from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    is_admin: bool
    created_at: datetime


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    category: str
    price: float
    stock: int
    rating: float
    review_count: int
    image: str
    material: str = ""
    colour: str = ""
    popularity: int = 0
    is_active: bool = True


class ProductListResponse(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
    pages: int


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str = Field(default="", max_length=160)
    comment: str = Field(default="", max_length=2000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    title: str
    comment: str
    created_at: datetime
    user_name: str


class CartItemOut(BaseModel):
    id: int
    product: ProductOut
    quantity: int
    line_total: float


class CartOut(BaseModel):
    items: list[CartItemOut]
    subtotal: float
    count: int


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=20)


class CheckoutRequest(BaseModel):
    shipping_name: str = Field(min_length=2, max_length=120)
    shipping_address: str = Field(min_length=4, max_length=300)
    shipping_city: str = Field(min_length=2, max_length=100)
    shipping_postcode: str = Field(min_length=2, max_length=30)
    shipping_country: str = Field(default="United States", max_length=100)
    payment_name: str = Field(min_length=2, max_length=120)
    payment_card: str = Field(min_length=12, max_length=23)
    payment_expiry: str = Field(min_length=4, max_length=7)
    payment_cvc: str = Field(min_length=3, max_length=4)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int | None = None
    product_code: str
    product_name: str
    quantity: int
    unit_price: float
    line_total: float
    image: str = ""


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    total: float
    status: str
    payment_method: str
    payment_last4: str = ""
    shipping_name: str = ""
    shipping_address: str = ""
    shipping_city: str = ""
    shipping_postcode: str = ""
    shipping_country: str = ""
    created_at: datetime
    items: list[OrderItemOut]


class InteractionCreate(BaseModel):
    product_id: int
    event_type: Literal["view", "cart_add", "purchase"] = "view"
    meta: dict = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    title: str
    subtitle: str
    strategy: str
    generated_ms: float
    personalized: bool = False
    model_label: str = ""
    items: list[ProductOut]


class AdminProductInput(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=3000)
    category: str = Field(min_length=2, max_length=80)
    price: float = Field(gt=0, le=100000)
    stock: int = Field(ge=0, le=1000000)
    image: str = ""
    material: str = ""
    colour: str = ""


class AdminProductUpdate(AdminProductInput):
    is_active: bool | None = None


class StatusResponse(BaseModel):
    message: str
    detail: str | None = None
