import uuid
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Product

Sort = Literal["newest", "price_asc", "price_desc"]

_ORDERING = {
    "newest": Product.created_at.desc(),
    "price_asc": Product.price_cents.asc(),
    "price_desc": Product.price_cents.desc(),
}


def list_products(db: Session, q: str | None, page: int, page_size: int, sort: Sort) -> tuple[list[Product], int]:
    stmt = select(Product)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(Product.name.ilike(pattern) | Product.sku.ilike(pattern))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(_ORDERING[sort], Product.id).offset((page - 1) * page_size).limit(page_size))
    return list(rows), total


def get_product(db: Session, product_id: uuid.UUID) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product
