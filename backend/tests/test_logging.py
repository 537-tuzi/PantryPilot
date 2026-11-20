from app.core.logging import redact_sensitive_text


def test_sensitive_values_are_redacted() -> None:
    message = "password=plain secret:abc token=xyz Authorization: Bearer bearer-token postgresql+psycopg://user:pass@localhost/db"

    redacted = redact_sensitive_text(message)

    assert "plain" not in redacted
    assert "abc" not in redacted
    assert "xyz" not in redacted
    assert "bearer-token" not in redacted
    assert "user:pass" not in redacted
