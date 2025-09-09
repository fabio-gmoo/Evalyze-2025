from typing import Any
from jose import jwt, JWTError  # type: ignore
from fastapi import HTTPException  # type: ignore
from application.ports.auth_port import AuthPort  # type: ignore
from infrastructure.config.settings import settings


class JwtVerifier(AuthPort):
    def verify(self, authorization_header: str | None) -> dict[str, Any]:
        if not authorization_header or not authorization_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")
        token = authorization_header.split(" ", 1)[1]

        try:
            if settings.jwt_alg.upper() == "RS256":
                if not settings.jwt_public_key:
                    raise HTTPException(
                        status_code=500, detail="Missing JWT public key"
                    )
                payload = jwt.decode(
                    token, settings.jwt_public_key, algorithms=["RS256"]
                )
            else:
                if not settings.jwt_secret:
                    raise HTTPException(status_code=500, detail="Missing JWT secret")
                payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
