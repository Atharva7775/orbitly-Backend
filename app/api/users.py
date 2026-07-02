from fastapi import APIRouter

from app import schemas
from app.deps import CurrentUser, DbSession

router = APIRouter()


@router.get("/me", response_model=schemas.UserOut)
def me(user: CurrentUser):
    return user


@router.patch("/me", response_model=schemas.UserOut)
def update_me(body: schemas.UserUpdate, user: CurrentUser, db: DbSession):
    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    db.add(user)
    db.commit()
    return user
