from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import SESSION_COOKIE, resolve_session

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    if not session_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    session = resolve_session(db, session_id)
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    return session.user


CurrentUser = Annotated[User, Depends(get_current_user)]
