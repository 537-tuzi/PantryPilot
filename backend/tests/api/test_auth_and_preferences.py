"""Authentication and user preference API integration tests against PostgreSQL."""

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.user import User

REGISTER_PAYLOAD = {
    "username": "pantry_user",
    "email": "pantry.user@example.com",
    "password": "StrongPassword1",
}
PREFERENCE_PAYLOAD = {
    "dietary_preferences": ["vegetarian"],
    "allergens": ["peanut"],
    "disliked_ingredients": ["celery"],
    "default_servings": 2,
    "default_budget": "120.50",
    "default_cooking_minutes": 35,
}


def register(client: TestClient, **overrides: str) -> dict[str, object]:
    payload = {**REGISTER_PAYLOAD, **overrides}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_argon2id_user_and_returns_safe_response(
    client: TestClient, db_session: Session
) -> None:
    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["user"]["username"] == REGISTER_PAYLOAD["username"]
    assert "password_hash" not in body
    user = db_session.query(User).filter_by(email=REGISTER_PAYLOAD["email"]).one()
    assert user.password_hash.startswith("$argon2id$")
    assert REGISTER_PAYLOAD["password"] not in user.password_hash


def test_register_rejects_duplicate_username_or_email(
    client: TestClient, db_session: Session
) -> None:
    register(client)

    duplicate_username = client.post(
        "/api/v1/auth/register",
        json={**REGISTER_PAYLOAD, "email": "other@example.com"},
    )
    duplicate_email = client.post(
        "/api/v1/auth/register",
        json={**REGISTER_PAYLOAD, "username": "other_user"},
    )

    for response in (duplicate_username, duplicate_email):
        assert response.status_code == 409
        assert response.json()["code"] == "STATE_CONFLICT"
        assert "request_id" in response.json()


def test_register_rejects_weak_password_without_echoing_it(
    client: TestClient, db_session: Session
) -> None:
    weak_password = "password"
    response = client.post(
        "/api/v1/auth/register", json={**REGISTER_PAYLOAD, "password": weak_password}
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert weak_password not in response.text


def test_login_succeeds_for_correct_email_and_password(
    client: TestClient, db_session: Session
) -> None:
    register(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert "password_hash" not in response.json()


def test_login_rejects_incorrect_password(client: TestClient, db_session: Session) -> None:
    register(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "WrongPassword1"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_login_rejects_disabled_user(client: TestClient, db_session: Session) -> None:
    db_session.add(
        User(
            username="disabled_user",
            email="disabled@example.com",
            password_hash=hash_password("StrongPassword1"),
            is_active=False,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "disabled@example.com", "password": "StrongPassword1"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_current_user_requires_valid_nonexpired_bearer_token(
    client: TestClient, db_session: Session
) -> None:
    registration = register(client)
    token = str(registration["access_token"])

    unauthenticated = client.get("/api/v1/users/me")
    authenticated = client.get("/api/v1/users/me", headers=authorization(token))
    user_id = db_session.query(User.id).filter_by(email=REGISTER_PAYLOAD["email"]).scalar()
    expired_token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
    expired = client.get("/api/v1/users/me", headers=authorization(expired_token))

    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 200
    assert authenticated.json()["email"] == REGISTER_PAYLOAD["email"]
    assert "password_hash" not in authenticated.json()
    assert expired.status_code == 401
    assert expired.json()["code"] == "UNAUTHENTICATED"


def test_preferences_create_read_update_and_user_isolation(
    client: TestClient, db_session: Session
) -> None:
    first_registration = register(client)
    first_token = str(first_registration["access_token"])
    missing = client.get("/api/v1/users/me/preferences", headers=authorization(first_token))
    first_put = client.put(
        "/api/v1/users/me/preferences",
        headers=authorization(first_token),
        json=PREFERENCE_PAYLOAD,
    )
    second_registration = register(
        client,
        username="other_user",
        email="other.user@example.com",
    )
    second_token = str(second_registration["access_token"])
    second_payload = {**PREFERENCE_PAYLOAD, "allergens": ["shellfish"], "default_servings": 4}
    second_put = client.put(
        "/api/v1/users/me/preferences",
        headers=authorization(second_token),
        json=second_payload,
    )
    first_get = client.get("/api/v1/users/me/preferences", headers=authorization(first_token))
    second_get = client.get("/api/v1/users/me/preferences", headers=authorization(second_token))

    assert missing.status_code == 404
    assert missing.json()["code"] == "RESOURCE_NOT_FOUND"
    assert first_put.status_code == 200
    assert second_put.status_code == 200
    assert first_get.json()["allergens"] == ["peanut"]
    assert first_get.json()["default_servings"] == 2
    assert second_get.json()["allergens"] == ["shellfish"]
    assert second_get.json()["default_servings"] == 4
