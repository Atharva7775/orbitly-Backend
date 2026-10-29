import uuid

from fastapi import APIRouter, Response, status

from app import schemas
from app.deps import CurrentUser, DbSession
from app.services import wishlist_service

router = APIRouter()


@router.get("", response_model=schemas.WishlistOut)
def get_wishlist(user: CurrentUser, db: DbSession):
    return schemas.WishlistOut(
        items=[schemas.ProductOut.model_validate(p) for p in wishlist_service.list_items(db, user.id)]
    )


@router.put("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def add(product_id: uuid.UUID, user: CurrentUser, db: DbSession):
    wishlist_service.add(db, user.id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(product_id: uuid.UUID, user: CurrentUser, db: DbSession):
    wishlist_service.remove(db, user.id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
