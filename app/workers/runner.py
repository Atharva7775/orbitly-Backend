"""Consumes Redis Streams with consumer groups and dispatches to handlers.

Run with:  python -m app.workers.runner
Each pod is one consumer; messages are acked only after the handler succeeds,
so a crash leaves them pending for another consumer to claim.
"""

import json
import logging
import os
import signal
import socket
from collections.abc import Callable

import redis

from app.config import get_settings
from app.workers import order_placed, user_signed_up

log = logging.getLogger("orbitly.workers")

HANDLERS: dict[str, tuple[str, Callable[[dict], None]]] = {
    order_placed.TOPIC: (order_placed.GROUP, order_placed.handle),
    user_signed_up.TOPIC: (user_signed_up.GROUP, user_signed_up.handle),
}

CLAIM_IDLE_MS = 60_000
_running = True


def _stop(*_: object) -> None:
    global _running
    _running = False


def _ensure_groups(client: redis.Redis) -> None:
    for topic, (group, _) in HANDLERS.items():
        try:
            client.xgroup_create(topic, group, id="0", mkstream=True)
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise


def _dispatch(client: redis.Redis, topic: str, msg_id: str, fields: dict) -> None:
    group, handler = HANDLERS[topic]
    try:
        handler(json.loads(fields["payload"]))
    except Exception:
        log.exception("handler for %s failed on %s; leaving pending", topic, msg_id)
        return
    client.xack(topic, group, msg_id)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    consumer = os.environ.get("HOSTNAME", socket.gethostname())
    client = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
    _ensure_groups(client)
    log.info("worker %s consuming %s", consumer, ", ".join(HANDLERS))

    while _running:
        for topic, (group, _) in HANDLERS.items():
            # Reclaim messages a crashed consumer left behind.
            _, claimed, _ = client.xautoclaim(topic, group, consumer, min_idle_time=CLAIM_IDLE_MS, count=10)
            for msg_id, fields in claimed:
                _dispatch(client, topic, msg_id, fields)

        for topic, (group, _) in HANDLERS.items():
            # Short block per stream so SIGTERM is honoured within a few seconds.
            batches = client.xreadgroup(group, consumer, {topic: ">"}, count=20, block=1000)
            for _stream, messages in batches or []:
                for msg_id, fields in messages:
                    _dispatch(client, topic, msg_id, fields)

    log.info("worker %s stopped", consumer)


if __name__ == "__main__":
    main()
