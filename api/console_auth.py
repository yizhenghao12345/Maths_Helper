import os
import hashlib
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import db


DEFAULT_PASSWORD = os.getenv("CONSOLE_PASSWORD", "admin123")

security = HTTPBearer(auto_error=False)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_stored_password_hash() -> str:
    stored = db.get_config("console_password_hash")
    if stored is None:
        stored = _hash_password(DEFAULT_PASSWORD)
        db.set_config("console_password_hash", stored)
    return stored


def verify_console_password(password: str) -> bool:
    stored_hash = _get_stored_password_hash()
    return _hash_password(password) == stored_hash


def create_console_token() -> str:
    token = secrets.token_urlsafe(32)
    db.set_config(f"console_token:{token}", "1")
    return token


def verify_console_token(token: str) -> bool:
    val = db.get_config(f"console_token:{token}")
    return val == "1"


def logout_console_token(token: str):
    stored = db.get_config(f"console_token:{token}")
    if stored is not None:
        db.set_config(f"console_token:{token}", "")


async def get_current_console_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    if not verify_console_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="无效或已过期的令牌")
    return True
