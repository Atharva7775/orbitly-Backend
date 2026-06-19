"""Subscriber for user.signed_up: send the welcome email."""

import logging

from app.events.topics import USER_SIGNED_UP
from app.services.notifications import send_email

log = logging.getLogger("orbitly.workers.user_signed_up")

TOPIC = USER_SIGNED_UP
GROUP = "lifecycle-email"


def handle(payload: dict) -> None:
    send_email(
        payload["email"],
        "Welcome to Orbitly",
        f"Hi {payload['full_name']},\n\nThanks for joining Orbitly. Use code ORBIT10 for 10% off your first order.\n",
    )
