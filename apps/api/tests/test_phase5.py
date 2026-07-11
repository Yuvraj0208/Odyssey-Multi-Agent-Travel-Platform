"""Phase 5: security (hashing/JWT), guardrails, rate limiting (no LLM)."""

import time

from odyssey.core.guardrails import clean_user_text, redact_pii
from odyssey.core.ratelimit import TokenBucket
from odyssey.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("supersecret1")
    assert h != "supersecret1"
    assert verify_password("supersecret1", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip_and_tamper():
    tok = create_access_token("u_1", "a@b.com")
    payload = decode_access_token(tok)
    assert payload and payload["sub"] == "u_1" and payload["email"] == "a@b.com"
    assert decode_access_token(tok + "x") is None  # tampered token rejected


def test_clean_user_text():
    assert clean_user_text("hi\x00\x07 there") == "hi there"
    assert len(clean_user_text("x" * 20000)) == 8000
    assert clean_user_text("  spaced  ") == "spaced"


def test_redact_pii():
    r = redact_pii("email me at ada@example.com or call 415-555-2671")
    assert "ada@example.com" not in r and "[email]" in r
    assert "[phone]" in r
    assert redact_pii("card 4111 1111 1111 1111 now") .count("[card]") == 1


def test_token_bucket_limits():
    tb = TokenBucket(per_minute=3)
    assert tb.allow("k") and tb.allow("k") and tb.allow("k")
    assert not tb.allow("k")  # 4th within the window is denied
    assert tb.allow("other")  # separate key unaffected


def test_token_bucket_refills():
    tb = TokenBucket(per_minute=60)  # 1 token/sec
    for _ in range(60):
        tb.allow("k")
    assert not tb.allow("k")
    tb._buckets["k"] = (0.0, time.monotonic() - 2)  # simulate 2s elapsed
    assert tb.allow("k")  # refilled
