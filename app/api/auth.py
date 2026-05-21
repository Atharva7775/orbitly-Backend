from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from app import schemas
from app.config import get_settings
from app.deps import DbSession
from app.security import SESSION_COOKIE
from app.services import auth_service

router = APIRouter()


def _set_cookie(response: Response, session) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session.id,
        expires=session.expires_at,
        httponly=True,
        secure=get_settings().environment != "development",
        samesite="lax",
        path="/",
    )


@router.post("/signup", response_model=schemas.SessionOut, status_code=status.HTTP_201_CREATED)
def signup(body: schemas.SignupIn, response: Response, db: DbSession):
    session = auth_service.signup(db, body.email, body.password, body.full_name)
    _set_cookie(response, session)
    return schemas.SessionOut(user=schemas.UserOut.model_validate(session.user))


@router.post("/login", response_model=schemas.SessionOut)
def login(body: schemas.LoginIn, response: Response, db: DbSession):
    session = auth_service.login(db, body.email, body.password)
    _set_cookie(response, session)
    return schemas.SessionOut(user=schemas.UserOut.model_validate(session.user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None):
    if session_id:
        auth_service.logout(db, session_id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
