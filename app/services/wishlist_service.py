import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Product, WishlistItem


def list_items(db: Session, user_id: uuid.UUID) -> list[Product]:
    rows = db.scalars(select(WishlistItem).where(WishlistItem.user_id == user_id).order_by(WishlistItem.added_at))
    return [row.product for row in rows]


def add(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> None:
    if db.get(Product, product_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    if db.get(WishlistItem, (user_id, product_id)) is None:
        db.add(WishlistItem(user_id=user_id, product_id=product_id))
        db.commit()


def remove(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> None:
    db.execute(delete(WishlistItem).where(WishlistItem.user_id == user_id, WishlistItem.product_id == product_id))
    db.commit()
