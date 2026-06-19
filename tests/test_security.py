from app.security import hash_password, verify_password


def test_password_roundtrip():
    h = hash_password("correct horse battery")
    assert verify_password("correct horse battery", h)
    assert not verify_password("wrong", h)


def test_verify_password_handles_garbage_hash():
    assert verify_password("anything", "not-a-bcrypt-hash") is False
