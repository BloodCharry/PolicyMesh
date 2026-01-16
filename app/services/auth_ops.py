from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.config import settings

# Настройка контекста для хеширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Сверка чистого пароля с хешем из БД."""
        result: bool = pwd_context.verify(plain_password, hashed_password)
        return result

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Генерация хеша из пароля."""
        hashed: str = pwd_context.hash(password)
        return hashed

    @staticmethod
    def create_access_token(
        data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """
        Создание JWT токена доступа.
        В data обычно кладем {"sub": "user_id", "role": "admin"}
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        # Добавляем стандартное поле exp
        to_encode.update({"exp": expire})

        encoded_jwt: str = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict[str, Any]) -> str:
        """
        Создание Refresh токена
        """
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})

        encoded_jwt: str = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        """
        Декодирование токена.
        Возвращает словарь или None, если токен невалиден.
        """
        try:
            payload: dict[str, Any] = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except Exception:
            return None
