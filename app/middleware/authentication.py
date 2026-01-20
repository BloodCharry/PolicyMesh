from collections.abc import Awaitable, Callable

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.db.session import AsyncSessionLocal
from app.models.users import User
from app.services.auth_ops import AuthService

logger = structlog.get_logger()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Инициализируем user как None (для анонимов)
        request.state.user = None

        # Получаем заголовок
        auth_header = request.headers.get("Authorization")

        # Если заголовка нет — просто пропустить запрос дальше.
        if not auth_header:
            logger.debug("No auth header", path=request.url.path, method=request.method)
            return await call_next(request)

        # Валидация формата Bearer <token>
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                logger.warning(
                    "Invalid authentication scheme",
                    scheme=scheme,
                    path=request.url.path,
                    client_ip=self._get_client_ip(request),
                )
                return JSONResponse(
                    status_code=401, content={"detail": "Invalid authentication scheme"}
                )
        except ValueError:
            logger.warning(
                "Invalid authorization header format",
                auth_header=(
                    auth_header[:50] + "..." if len(auth_header) > 50 else auth_header
                ),
                path=request.url.path,
                client_ip=self._get_client_ip(request),
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
            )

        # Декодирование токена
        payload = AuthService.decode_token(token)
        if not payload:
            logger.warning(
                "Invalid or expired token",
                path=request.url.path,
                client_ip=self._get_client_ip(request),
            )
            return JSONResponse(
                status_code=401, content={"detail": "Invalid or expired token"}
            )

        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id.isdigit():
            logger.warning(
                "Invalid user ID in token",
                user_id=user_id,
                path=request.url.path,
                client_ip=self._get_client_ip(request),
            )
            return JSONResponse(
                status_code=401, content={"detail": "Invalid user ID in token"}
            )
        user_id_int = int(user_id)

        # Поиск пользователя в БД
        async with AsyncSessionLocal() as session:
            # Role и Rules понадобятся для проверки прав
            stmt = (
                select(User)
                .options(selectinload(User.role))
                .where(User.id == user_id_int)  # ← убрал лишний int()
            )

            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            # Проверки безопасности
            if not user:
                logger.warning(
                    "User not found",
                    user_id=user_id_int,
                    path=request.url.path,
                    client_ip=self._get_client_ip(request),
                )
                return JSONResponse(
                    status_code=401, content={"detail": "User not found"}
                )

            if not user.is_active:
                logger.warning(
                    "Inactive user access attempt",
                    user_id=user.id,
                    email=getattr(user, "email", "unknown"),
                    path=request.url.path,
                    client_ip=self._get_client_ip(request),
                )
                return JSONResponse(
                    status_code=401, content={"detail": "User is inactive"}
                )

            # отсоединить объект от сессии, чтобы использовать его в роутах
            request.state.user = user
            logger.debug(
                "User authenticated successfully",
                user_id=user.id,
                role=getattr(user.role, "name", "unknown"),
                path=request.url.path,
            )

        # Передача управления дальше
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Получить IP-адрес клиента с учётом proxy headers"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
