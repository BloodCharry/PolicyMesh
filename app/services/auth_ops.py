from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import structlog
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings

logger = structlog.get_logger()


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Сверка чистого пароля с хешем из БД."""
        result = bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
        logger.debug("Password verification", result=result)
        return result

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Генерация хеша из пароля."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        logger.debug("Password hashed successfully")
        return hashed.decode("utf-8")

    @staticmethod
    def create_access_token(
        data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt: str = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        logger.debug(
            "Access token created",
            user_id=data.get("sub"),
            role_id=data.get("role_id"),
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt: str = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        logger.debug(
            "Refresh token created",
            user_id=data.get("sub"),
            role_id=data.get("role_id"),
            expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        try:
            payload: dict[str, Any] = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            logger.debug(
                "Token decoded successfully",
                user_id=payload.get("sub"),
                role_id=payload.get("role_id"),
            )
            return payload
        except ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except JWTError as e:
            logger.warning("Token decoding failed", error=str(e))
            return None
