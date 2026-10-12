from datetime import UTC, datetime, timedelta

from app.security import hash_password, hash_token, session_expiry, verify_password


def test_password_roundtrip():
    h = hash_password("correct horse battery")
    assert verify_password("correct horse battery", h)
    assert not verify_password("wrong", h)


def test_verify_password_handles_garbage_hash():
    assert verify_password("anything", "not-a-bcrypt-hash") is False


def test_token_hash_is_sha256_hex():
    digest = hash_token("abc")
    assert len(digest) == 64
    assert digest == hash_token("abc")


def test_session_expiry_uses_minutes():
    now = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
    # Default SESSION_TTL_MINUTES is 720 (12 hours).
    assert session_expiry(now) - now == timedelta(minutes=720)
