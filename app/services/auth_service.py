from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.events.publish import publish
from app.events.topics import USER_SIGNED_UP
from app.models import User, UserSession
from app.security import hash_password, issue_session, revoke_session, verify_password


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    """Hash checked when the email is unknown, so response time does not reveal
    whether an account exists."""
    return hash_password("orbitly-timing-guard")


def signup(db: Session, email: str, password: str, full_name: str) -> UserSession:
    user = User(email=email.lower(), password_hash=hash_password(password), full_name=full_name.strip())
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists") from None
    session = issue_session(db, user)
    db.commit()
    publish(USER_SIGNED_UP, {"user_id": str(user.id), "email": user.email, "full_name": user.full_name})
    return session


def login(db: Session, email: str, password: str) -> UserSession:
    user = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
    if user is None:
        verify_password(password, _dummy_hash())
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    session = issue_session(db, user)
    db.commit()
    return session


def logout(db: Session, session_id: str) -> None:
    revoke_session(db, session_id)
    db.commit()
