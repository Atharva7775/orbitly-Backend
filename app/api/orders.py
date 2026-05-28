import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Query, status

from app import schemas
from app.deps import CurrentUser, DbSession
from app.services import order_service

router = APIRouter()


@router.post("", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    body: schemas.OrderIn,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: Annotated[str | None, Header(max_length=64)] = None,
):
    order = order_service.place_order(db, user.id, body, idempotency_key)
    return order_service.to_out(order)


@router.get("", response_model=schemas.Page[schemas.OrderOut])
def list_orders(
    user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
):
    orders, total = order_service.list_orders(db, user.id, page, page_size)
    return schemas.Page[schemas.OrderOut](
        items=[order_service.to_out(o) for o in orders], total=total, page=page, page_size=page_size
    )


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return order_service.to_out(order_service.get_order(db, user.id, order_id))
