"""Publishes domain events to Redis Streams.

Events are fire-and-forget from the request's point of view: the write that
triggered them is already committed, so a Redis outage must not fail the
request. Failures are logged and counted; consumers in app/workers/ are
idempotent so a later replay is safe.
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import redis

from app.config import get_settings
from app.events.topics import ALL_TOPICS

log = logging.getLogger("orbitly.events")

# Keep roughly a week of events at current volume.
STREAM_MAXLEN = 200_000


@lru_cache(maxsize=1)
def _client() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url, socket_timeout=2, decode_responses=True)


def publish(topic: str, payload: dict[str, Any]) -> str | None:
    if topic not in ALL_TOPICS:
        raise ValueError(f"unknown topic {topic!r}")
    envelope = {
        "id": str(uuid.uuid4()),
        "topic": topic,
        "occurred_at": datetime.now(UTC).isoformat(),
        "payload": json.dumps(payload, separators=(",", ":")),
    }
    try:
        return _client().xadd(topic, envelope, maxlen=STREAM_MAXLEN, approximate=True)
    except redis.RedisError:
        log.exception("failed to publish %s event %s", topic, envelope["id"])
        return None
