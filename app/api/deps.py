from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.rbac import AccessRolesRules, BusinessElement
from app.models.users import User


class RequirePermission:
    """
    Зависимость для проверки наличия базовых прав доступа к ресурсу.
    Использование: Depends(RequirePermission(key="orders", action="read"))
    """

    def __init__(self, key: str, action: str):
        self.key = key
        self.action = action

    async def __call__(
        self, request: Request, db: AsyncSession = Depends(get_db)
    ) -> bool:
        # Получение пользователя из request (положил Middleware)
        user: User = request.state.user

        # Если Middleware не нашел юзера то возрат 401.
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        # Поиск правила в БД
        stmt = (
            select(AccessRolesRules)
            .join(BusinessElement)
            .where(
                AccessRolesRules.role_id == user.role_id,
                BusinessElement.key == self.key,
            )
        )
        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()

        if not rule:
            # Если правил нет вообще - запрещено по умолчанию
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to resource '{self.key}'",
            )

        # Проверка флагов, впустить пользователя, если у него есть ЛИБО локальные, ЛИБО глобальные права.
        is_allowed = False

        match self.action:
            case "create":
                is_allowed = rule.create_permission
            case "read":
                is_allowed = rule.read_permission or rule.read_all_permission
            case "update":
                is_allowed = rule.update_permission or rule.update_all_permission
            case "delete":
                is_allowed = rule.delete_permission or rule.delete_all_permission
            case _:
                # Если передан неизвестный экшен
                raise HTTPException(
                    status_code=500, detail=f"Unknown action '{self.action}'"
                )

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to {self.action} {self.key}",
            )

        return True
