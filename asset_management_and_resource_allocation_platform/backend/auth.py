import base64
import hashlib
import hmac
import json
import os
import time
from http import cookies


SECRET_KEY = os.environ.get("ASSET_MANAGER_SECRET", "change-this-secret-before-production")
SESSION_MAX_AGE = 60 * 60 * 8


def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return f"{salt}${digest.hex()}"


def verify_password(password, saved_hash):
    try:
        salt, expected = saved_hash.split("$", 1)
    except ValueError:
        return False
    candidate = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, expected)


def _sign(payload):
    return hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session(user):
    payload = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "expires_at": int(time.time()) + SESSION_MAX_AGE,
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return f"{encoded}.{_sign(encoded)}"


def read_session(headers):
    raw_cookie = headers.get("Cookie", "")
    jar = cookies.SimpleCookie()
    jar.load(raw_cookie)
    morsel = jar.get("asset_session")
    if not morsel:
        return None

    try:
        encoded, signature = morsel.value.rsplit(".", 1)
    except ValueError:
        return None

    if not hmac.compare_digest(_sign(encoded), signature):
        return None

    try:
        payload = json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())
    except (ValueError, json.JSONDecodeError):
        return None

    if payload.get("expires_at", 0) < int(time.time()):
        return None
    return payload


def session_cookie(token):
    return f"asset_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_MAX_AGE}"


def clear_session_cookie():
    return "asset_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"
