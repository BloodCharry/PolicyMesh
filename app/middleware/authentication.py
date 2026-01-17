from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.db.session import AsyncSessionLocal
from app.models.users import User
from app.services.auth_ops import AuthService


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
            return await call_next(request)

        # Валидация формата Bearer <token>
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=401, content={"detail": "Invalid authentication scheme"}
                )
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
            )

        # Декодирование токена
        payload = AuthService.decode_token(token)
        if not payload:
            return JSONResponse(
                status_code=401, content={"detail": "Invalid or expired token"}
            )

        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id.isdigit():
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
                return JSONResponse(
                    status_code=401, content={"detail": "User not found"}
                )

            if not user.is_active:
                return JSONResponse(
                    status_code=401, content={"detail": "User is inactive"}
                )

            # отсоединить объект от сессии, чтобы использовать его в роутах
            request.state.user = user

        # Передача управления дальше
        response = await call_next(request)
        return response
