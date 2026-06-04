"""JWT authentication — RS256 verification."""

from __future__ import annotations

import os
from dataclasses import dataclass

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer()
_PUBLIC_KEY = os.environ["JWT_PUBLIC_KEY"]  # PEM-encoded RSA public key


@dataclass
class JWTClaims:
    sub: str          # API key owner / user ID
    tier: str         # free | standard | premium
    model: str | None # optional per-token model restriction


def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> JWTClaims:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            _PUBLIC_KEY,
            algorithms=["RS256"],
            options={"require": ["sub", "exp", "tier"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")

    return JWTClaims(
        sub=payload["sub"],
        tier=payload.get("tier", "free"),
        model=payload.get("model"),  # None = all models allowed
    )
