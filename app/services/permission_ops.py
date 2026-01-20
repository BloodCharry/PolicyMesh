import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rbac import AccessRolesRules, BusinessElement
from app.models.users import User

logger = structlog.get_logger()


class PermissionService:
    @staticmethod
    async def has_permission(
        db: AsyncSession,
        user: User,
        resource_key: str,
        action: str,
        owner_id: int | None = None,
    ) -> bool:
        """
        Главная функция авторизации.
        :param db: Сессия БД
        :param user: Объект пользователя
        :param resource_key: Ключ элемента (например, "orders")
        :param action: "create", "read", "update", "delete"
        :param owner_id: ID владельца объекта (если применимо)
        """

        # Если пользователь неактивен — отказ сразу
        if not user.is_active:
            logger.warning(
                "Permission denied: inactive user",
                user_id=user.id,
                resource=resource_key,
                action=action,
            )
            return False

        # Поиск правила для роли пользователя и конкретного ресурса
        # Join с BusinessElement нужен, чтобы найти по строке, а не ID
        stmt = (
            select(AccessRolesRules)
            .join(BusinessElement)
            .where(
                AccessRolesRules.role_id == user.role_id,
                BusinessElement.key == resource_key,
            )
        )

        result = await db.execute(stmt)
        rule = result.scalar_one_or_none()

        # Если правила нет в БД — доступ запрещен
        if not rule:
            logger.warning(
                "Permission denied: no RBAC rule found",
                user_id=user.id,
                role_id=user.role_id,
                resource=resource_key,
                action=action,
            )
            return False

        # Логика проверки прав

        match action:
            case "create":
                # Для создания без проверки владельца
                return rule.create_permission

            case "read":
                # проверка глобального права
                if rule.read_all_permission:
                    return True
                # Если глобального нет, проверяем локальное ("Читать свои") + владение
                if rule.read_permission and owner_id is not None:
                    return user.id == owner_id
                return False

            case "update":
                if rule.update_all_permission:
                    return True
                if rule.update_permission and owner_id is not None:
                    return user.id == owner_id
                return False

            case "delete":
                if rule.delete_all_permission:
                    return True
                if rule.delete_permission and owner_id is not None:
                    return user.id == owner_id
                return False

            case _:
                logger.error(
                    "Unknown action in permission check",
                    action=action,
                    resource=resource_key,
                    user_id=user.id,
                )
                return False
