"""Request/response models. JSON is camelCase to match orbitly-frontend's TypeScript types."""

import uuid
from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class Page(ApiModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class UserOut(ApiModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    created_at: datetime


class UserUpdate(ApiModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)


class LoginIn(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class SignupIn(LoginIn):
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=10, max_length=200)


class SessionOut(ApiModel):
    user: UserOut


class ProductOut(ApiModel):
    id: uuid.UUID
    sku: str
    name: str
    description: str
    price_cents: int
    currency: str
    image_url: str | None
    stock: int


class CartItemIn(ApiModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=20)


class CartItemUpdate(ApiModel):
    quantity: int = Field(ge=1, le=20)


class CartItemOut(ApiModel):
    product_id: uuid.UUID
    name: str
    unit_price_cents: int
    quantity: int


class CartOut(ApiModel):
    items: list[CartItemOut]
    subtotal_cents: int


class Address(ApiModel):
    line1: str = Field(min_length=1, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=2, max_length=20)
    country: str = Field(min_length=2, max_length=2)


class OrderIn(ApiModel):
    shipping_address: Address
    promo_code: str | None = Field(default=None, max_length=32)


class OrderLineOut(ApiModel):
    product_id: uuid.UUID
    name: str
    unit_price_cents: int
    quantity: int


OrderStatus = Literal["pending", "paid", "shipped", "cancelled", "refunded"]


class OrderOut(ApiModel):
    id: uuid.UUID
    status: OrderStatus
    lines: list[OrderLineOut]
    subtotal_cents: int
    discount_cents: int
    tax_cents: int
    total_cents: int
    currency: str
    created_at: datetime


class PaymentIn(ApiModel):
    order_id: uuid.UUID
    card_token: str = Field(min_length=4, max_length=100)


class PaymentOut(ApiModel):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    status: Literal["authorized", "captured", "declined"]
