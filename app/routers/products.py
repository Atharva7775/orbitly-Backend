import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app import schemas
from app.deps import DbSession
from app.services import catalog_service
from app.services.catalog_service import Sort

router = APIRouter()


@router.get("", response_model=schemas.Page[schemas.ProductOut])
def list_products(
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
    sort: Sort = "newest",
):
    items, total = catalog_service.list_products(db, q, page, page_size, sort)
    return schemas.Page[schemas.ProductOut](
        items=[schemas.ProductOut.model_validate(p) for p in items], total=total, page=page, page_size=page_size
    )


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: uuid.UUID, db: DbSession):
    return catalog_service.get_product(db, product_id)
