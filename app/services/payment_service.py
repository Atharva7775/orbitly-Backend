"""Server-side capture against the PayStream gateway.

The browser tokenizes the card directly with PayStream; we only ever see the
single-use token. The gateway base URL and secret key come from the
environment (PAYMENTS_API_URL / PAYMENTS_API_KEY).
"""

import logging
import uuid

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Order, Payment

log = logging.getLogger("orbitly.payments")


class GatewayError(Exception):
    pass


def _charge(amount_cents: int, currency: str, card_token: str, order_id: uuid.UUID) -> dict:
    settings = get_settings()
    try:
        resp = httpx.post(
            f"{settings.payments_api_url}/v1/charges",
            headers={
                "Authorization": f"Bearer {settings.payments_api_key}",
                "Idempotency-Key": f"orbitly-order-{order_id}",
            },
            json={
                "amount": amount_cents,
                "currency": currency.lower(),
                "source": card_token,
                "capture": True,
                "metadata": {"order_id": str(order_id)},
            },
            timeout=settings.payments_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise GatewayError(str(exc)) from exc
    if resp.status_code >= 500:
        raise GatewayError(f"gateway returned {resp.status_code}")
    return resp.json()


def pay_order(db: Session, user_id: uuid.UUID, order_id: uuid.UUID, card_token: str) -> Payment:
    order = db.get(Order, order_id, with_for_update=True)
    if order is None or order.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if order.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Order is already {order.status}")

    try:
        result = _charge(order.total_cents, order.currency, card_token, order.id)
    except GatewayError as exc:
        log.warning("payment gateway unavailable for order %s: %s", order.id, exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Payments are temporarily unavailable") from exc

    captured = result.get("status") == "succeeded"
    payment = Payment(
        order_id=order.id,
        provider_ref=result.get("id"),
        amount_cents=order.total_cents,
        currency=order.currency,
        status="captured" if captured else "declined",
        failure_reason=None if captured else (result.get("failure_message") or "declined")[:200],
    )
    db.add(payment)
    if captured:
        order.status = "paid"
    db.commit()
    return payment
