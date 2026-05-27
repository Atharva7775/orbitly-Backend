import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import CartItem, Product
from app.schemas import CartItemOut, CartOut

MAX_LINES = 50


def get_cart(db: Session, user_id: uuid.UUID) -> CartOut:
    items = db.scalars(select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.added_at)).all()
    lines = [
        CartItemOut(
            product_id=i.product_id,
            name=i.product.name,
            unit_price_cents=i.product.price_cents,
            quantity=i.quantity,
        )
        for i in items
    ]
    return CartOut(items=lines, subtotal_cents=sum(line.unit_price_cents * line.quantity for line in lines))


def add_item(db: Session, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> CartOut:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    item = db.get(CartItem, (user_id, product_id))
    if item is None:
        count = len(db.scalars(select(CartItem.product_id).where(CartItem.user_id == user_id)).all())
        if count >= MAX_LINES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cart is full")
        item = CartItem(user_id=user_id, product_id=product_id, quantity=0)
        db.add(item)
    item.quantity = min(item.quantity + quantity, 20, product.stock)
    if item.quantity <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Product is out of stock")
    db.commit()
    return get_cart(db, user_id)


def set_quantity(db: Session, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> CartOut:
    item = db.get(CartItem, (user_id, product_id))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item is not in your cart")
    item.quantity = min(quantity, item.product.stock)
    db.commit()
    return get_cart(db, user_id)


def remove_item(db: Session, user_id: uuid.UUID, product_id: uuid.UUID) -> CartOut:
    db.execute(delete(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
    db.commit()
    return get_cart(db, user_id)


def clear(db: Session, user_id: uuid.UUID) -> None:
    db.execute(delete(CartItem).where(CartItem.user_id == user_id))
