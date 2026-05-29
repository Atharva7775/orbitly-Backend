import uuid

from fastapi import APIRouter

from app import schemas
from app.deps import CurrentUser, DbSession
from app.services import cart_service

router = APIRouter()


@router.get("", response_model=schemas.CartOut)
def get_cart(user: CurrentUser, db: DbSession):
    return cart_service.get_cart(db, user.id)


@router.post("/items", response_model=schemas.CartOut)
def add_item(body: schemas.CartItemIn, user: CurrentUser, db: DbSession):
    return cart_service.add_item(db, user.id, body.product_id, body.quantity)


@router.patch("/items/{product_id}", response_model=schemas.CartOut)
def update_item(product_id: uuid.UUID, body: schemas.CartItemUpdate, user: CurrentUser, db: DbSession):
    return cart_service.set_quantity(db, user.id, product_id, body.quantity)


@router.delete("/items/{product_id}", response_model=schemas.CartOut)
def remove_item(product_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return cart_service.remove_item(db, user.id, product_id)
