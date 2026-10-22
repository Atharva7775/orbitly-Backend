import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.events.publish import publish
from app.events.topics import ORDER_PLACED
from app.models import CartItem, Order, OrderItem, Product
from app.schemas import OrderIn, OrderLineOut, OrderOut
from app.services import cart_service
from app.services.pricing import Line, compute_totals, find_promo


def to_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        status=order.status,  # type: ignore[arg-type]
        lines=[
            OrderLineOut(
                product_id=i.product_id, name=i.name, unit_price_cents=i.unit_price_cents, quantity=i.quantity
            )
            for i in order.items
        ],
        subtotal_cents=order.subtotal_cents,
        discount_cents=order.discount_cents,
        tax_cents=order.tax_cents,
        total_cents=order.total_cents,
        currency=order.currency,
        created_at=order.created_at,
    )


def place_order(db: Session, user_id: uuid.UUID, body: OrderIn, idempotency_key: str | None) -> Order:
    if idempotency_key:
        existing = db.scalar(select(Order).where(Order.idempotency_key == idempotency_key))
        if existing is not None:
            if existing.user_id != user_id:
                raise HTTPException(status.HTTP_409_CONFLICT, "Idempotency key already used")
            return existing

    cart = db.scalars(select(CartItem).where(CartItem.user_id == user_id).with_for_update()).unique().all()
    if not cart:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Your cart is empty")
    for item in cart:
        if item.quantity > item.product.stock:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Only {item.product.stock} left of {item.product.name}")

    promo = find_promo(body.promo_code)
    if body.promo_code and promo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Promo code is not valid")

    totals = compute_totals(
        [Line(i.product.price_cents, i.quantity) for i in cart], promo, body.shipping_address.country
    )
    order = Order(
        user_id=user_id,
        status="pending",
        subtotal_cents=totals.subtotal_cents,
        discount_cents=totals.discount_cents,
        tax_cents=totals.tax_cents,
        total_cents=totals.total_cents,
        currency=cart[0].product.currency,
        promo_code=promo.code if promo else None,
        shipping_address=body.shipping_address.model_dump(),
        idempotency_key=idempotency_key,
        items=[
            OrderItem(product_id=i.product_id, name=i.product.name, unit_price_cents=i.product.price_cents,
                      quantity=i.quantity)
            for i in cart
        ],
    )
    db.add(order)
    cart_service.clear(db, user_id)
    db.commit()
    db.refresh(order)

    publish(
        ORDER_PLACED,
        {
            "order_id": str(order.id),
            "user_id": str(user_id),
            "total_cents": order.total_cents,
            "currency": order.currency,
            "items": [{"product_id": str(i.product_id), "quantity": i.quantity} for i in order.items],
        },
    )
    return order


def list_orders(db: Session, user_id: uuid.UUID, page: int, page_size: int) -> tuple[list[Order], int]:
    base = select(Order).where(Order.user_id == user_id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(base.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(rows), total


def get_order(db: Session, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order = db.get(Order, order_id)
    # 404 rather than 403 so order ids cannot be probed.
    if order is None or order.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


CANCELLABLE = {"pending", "paid"}


def cancel_order(db: Session, user_id: uuid.UUID, order_id: uuid.UUID, reason: str) -> Order:
    order = db.get(Order, order_id, with_for_update=True)
    if order is None or order.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if order.status not in CANCELLABLE:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Order is already {order.status}")
    # Paid orders are refunded by the finance job that watches cancelled_at.
    order.status = "cancelled"
    order.cancelled_at = datetime.now(UTC)
    order.cancel_reason = reason
    for item in order.items:
        db.execute(update(Product).where(Product.id == item.product_id).values(stock=Product.stock + item.quantity))
    db.commit()
    return order
