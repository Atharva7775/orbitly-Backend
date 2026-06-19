"""Subscriber for order.placed: reserve stock and email a confirmation."""

import logging
import uuid

from sqlalchemy import update

from app.db import SessionLocal
from app.events.topics import ORDER_PLACED
from app.models import Order, Product, User
from app.services.notifications import send_email

log = logging.getLogger("orbitly.workers.order_placed")

TOPIC = ORDER_PLACED
GROUP = "order-fulfilment"


def handle(payload: dict) -> None:
    order_id = uuid.UUID(payload["order_id"])
    with SessionLocal() as db, db.begin():
        order = db.get(Order, order_id)
        if order is None:
            log.warning("order %s not found; skipping", order_id)
            return
        for item in payload["items"]:
            # Guarded decrement keeps stock non-negative even if two orders race.
            db.execute(
                update(Product)
                .where(Product.id == uuid.UUID(item["product_id"]), Product.stock >= item["quantity"])
                .values(stock=Product.stock - item["quantity"])
            )
        user = db.get(User, order.user_id)

    if user is not None:
        send_email(
            user.email,
            f"Your Orbitly order #{str(order_id)[:8]}",
            f"Hi {user.full_name},\n\nWe received your order totalling "
            f"{payload['total_cents'] / 100:.2f} {payload['currency']}. We'll email you when it ships.\n",
        )
