from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status
from fastapi.security import HTTPAuthorizationCredentials

from app import schemas
from app.deps import DbSession, bearer
from app.services import auth_service

router = APIRouter()


def _token_out(token: str, session) -> schemas.TokenOut:
    return schemas.TokenOut(
        access_token=token,
        expires_at=session.expires_at,
        user=schemas.UserOut.model_validate(session.user),
    )


@router.post("/signup", response_model=schemas.TokenOut, status_code=status.HTTP_201_CREATED)
def signup(body: schemas.SignupIn, db: DbSession, user_agent: Annotated[str | None, Header()] = None):
    token, session = auth_service.signup(db, body.email, body.password, body.full_name, user_agent)
    return _token_out(token, session)


@router.post("/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: DbSession, user_agent: Annotated[str | None, Header()] = None):
    token, session = auth_service.login(db, body.email, body.password, user_agent)
    return _token_out(token, session)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is not None:
        auth_service.logout(db, credentials.credentials)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
