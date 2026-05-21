"""Password hashing and server-side cookie sessions.

The browser holds only a random session id in the orbitly_sid cookie; the
session row lives in Postgres so it can be revoked server-side.
"""

import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User, UserSession

SESSION_COOKIE = "orbitly_sid"


def hash_password(password: str) -> str:
    rounds = get_settings().bcrypt_rounds
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=rounds)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def session_expiry(now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    return now + timedelta(minutes=get_settings().session_ttl_minutes)


def issue_session(db: Session, user: User) -> UserSession:
    row = UserSession(id=secrets.token_urlsafe(32), user_id=user.id, expires_at=session_expiry())
    db.add(row)
    db.flush()
    return row


def resolve_session(db: Session, session_id: str) -> UserSession | None:
    row = db.scalar(select(UserSession).where(UserSession.id == session_id))
    if row is None or row.expires_at <= datetime.now(UTC):
        return None
    return row


def revoke_session(db: Session, session_id: str) -> None:
    db.execute(delete(UserSession).where(UserSession.id == session_id))
