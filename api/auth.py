import hashlib
import hmac
import os
from dataclasses import dataclass

from fastapi import Cookie, HTTPException, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SESSION_COOKIE = "refund_lab_session"
SESSION_MAX_AGE = 60 * 60
DEMO_USER_IDS = frozenset({"user126"})
_PASSWORD_SALT = b"aiagente-demo-v1"
_PASSWORD_HASH = bytes.fromhex("cd4fc65ddb7f49b64fc00f393731fc726f8a7b1a3de5d1f38a970b21e551171b")


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str


def _serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("SESSION_SECRET", "local-development-secret")
    if os.getenv("APP_ENV") == "production" and secret == "local-development-secret":
        raise RuntimeError("SESSION_SECRET must be configured in production")
    return URLSafeTimedSerializer(secret, salt="refund-lab-session-v1")


def verify_demo_credentials(username: str, password: str) -> bool:
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _PASSWORD_SALT, 600_000)
    password_valid = hmac.compare_digest(candidate, _PASSWORD_HASH)
    return username in DEMO_USER_IDS and password_valid


def create_session(response: Response, username: str) -> None:
    token = _serializer().dumps({"username": username})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="lax")


def current_user(refund_lab_session: str | None = Cookie(default=None)) -> AuthenticatedUser:
    if not refund_lab_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")
    try:
        payload = _serializer().loads(refund_lab_session, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
        ) from error
    username = payload.get("username")
    if username not in DEMO_USER_IDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return AuthenticatedUser(username=username)
