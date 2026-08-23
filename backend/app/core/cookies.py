from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import settings

_serializer = URLSafeTimedSerializer(settings.cookie_secret, salt="verify-token")

COOKIE_NAME = "verify_token"
COOKIE_MAX_AGE_SECONDS = 600


def sign_token(token: str) -> str:
    return _serializer.dumps(token)


def unsign_token(signed_value: str) -> str | None:
    try:
        return _serializer.loads(signed_value, max_age=COOKIE_MAX_AGE_SECONDS)
    except BadSignature:
        return None
