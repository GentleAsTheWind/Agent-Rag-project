from server.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("secret")
    assert verify_password("secret", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip() -> None:
    token = create_access_token("user-id-1")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-1"
    assert payload["type"] == "access"
