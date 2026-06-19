"""Domain event topics. Each topic is a Redis Stream of the same name."""

ORDER_PLACED = "order.placed"
USER_SIGNED_UP = "user.signed_up"

ALL_TOPICS = (ORDER_PLACED, USER_SIGNED_UP)
