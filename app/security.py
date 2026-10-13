"""Password hashing and opaque bearer-token sessions.

Tokens are 256-bit random strings handed to the client once; the database only
stores their SHA-256, so a leaked sessions table cannot be replayed.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User, UserSession

TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    rounds = get_settings().bcrypt_rounds
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=rounds)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def session_expiry(now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    return now + timedelta(minutes=get_settings().session_ttl_minutes)


def issue_session(db: Session, user: User, user_agent: str | None) -> tuple[str, UserSession]:
    token = secrets.token_urlsafe(TOKEN_BYTES)
    row = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        user_agent=(user_agent or "")[:300] or None,
        expires_at=session_expiry(),
    )
    db.add(row)
    db.flush()
    return token, row


def resolve_session(db: Session, token: str) -> UserSession | None:
    row = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if row is None or row.revoked_at is not None:
        return None
    if row.expires_at <= datetime.now(UTC):
        return None
    return row


def revoke_session(db: Session, token: str) -> None:
    db.execute(
        update(UserSession)
        .where(UserSession.token_hash == hash_token(token), UserSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
