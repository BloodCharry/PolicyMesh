import asyncio
import logging

import bcrypt
import structlog
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.rbac import AccessRolesRules, BusinessElement, Role
from app.models.users import User

# логгер
logger = structlog.get_logger()


async def seed_db() -> None:
    async with AsyncSessionLocal() as session:
        logger.info("Начало посева данных...")

        # 1. Создание РОЛЕЙ
        roles_data = ["Admin", "User", "Manager", "Guest"]
        roles_map: dict[str, Role] = {}

        for role_name in roles_data:
            stmt = select(Role).where(Role.name == role_name)
            result = await session.execute(stmt)
            role: Role | None = result.scalar_one_or_none()

            if not role:
                role = Role(name=role_name)
                session.add(role)
                await session.flush()
                logger.info(f"Role created: {role_name}")
            else:
                logger.info(f"Role exists: {role_name}")

            roles_map[role_name] = role

        # 2. Создание БИЗНЕС-ЭЛЕМЕНТОВ
        elements_data = [
            {"key": "users", "name": "Пользователи"},
            {"key": "orders", "name": "Заказы"},
            {"key": "reports", "name": "Отчеты"},
        ]
        elements_map: dict[str, BusinessElement] = {}

        for el in elements_data:
            stmt_el = select(BusinessElement).where(BusinessElement.key == el["key"])
            result_el = await session.execute(stmt_el)
            element: BusinessElement | None = result_el.scalar_one_or_none()

            if not element:
                element = BusinessElement(key=el["key"], name=el["name"])
                session.add(element)
                await session.flush()
                logger.info("Business element created", key=el["key"], name=el["name"])
            else:
                logger.info(f"Element exists: {el['key']}")

            elements_map[el["key"]] = element

        # Настройка ПРАВ (Rules)
        # Правила для Admin
        admin_role = roles_map["Admin"]

        for key, business_element in elements_map.items():
            stmt_rule = select(AccessRolesRules).where(
                AccessRolesRules.role_id == admin_role.id,
                AccessRolesRules.element_id == business_element.id,
            )
            existing_rule = (await session.execute(stmt_rule)).scalar_one_or_none()

            if not existing_rule:
                rule = AccessRolesRules(
                    role_id=admin_role.id,
                    element_id=business_element.id,
                    create_permission=True,
                    read_permission=True,
                    read_all_permission=True,
                    update_permission=True,
                    update_all_permission=True,
                    delete_permission=True,
                    delete_all_permission=True,
                )
                session.add(rule)
                logger.info("Full permissions granted to Admin", resource=key)
            else:
                logger.info("Admin permissions already exist", resource=key)

        # Правила для User (Ограниченные)
        user_role = roles_map["User"]
        orders_el = elements_map["orders"]

        stmt_user_rule = select(AccessRolesRules).where(
            AccessRolesRules.role_id == user_role.id,
            AccessRolesRules.element_id == orders_el.id,
        )
        existing_user_rule = (
            await session.execute(stmt_user_rule)
        ).scalar_one_or_none()

        if not existing_user_rule:
            rule = AccessRolesRules(
                role_id=user_role.id,
                element_id=orders_el.id,
                create_permission=True,
                read_permission=True,
                read_all_permission=False,
                update_permission=True,
                update_all_permission=False,
                delete_permission=False,
                delete_all_permission=False,
            )
            session.add(rule)
            logger.info("Limited permissions granted to User", resource="orders")
        else:
            logger.info("User permissions already exist", resource="orders")

        # Создание АДМИНИСТРАТОРА
        admin_email = "admin@example.com"
        stmt_user = select(User).where(User.email == admin_email)  # ← новое имя
        existing_admin = (await session.execute(stmt_user)).scalar_one_or_none()

        if not existing_admin:
            password_bytes = b"admin123"  # nosec  # noqa: S105
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

            admin_user = User(
                email=admin_email,
                hashed_password=hashed_password,
                first_name="Super",
                last_name="Admin",
                role_id=admin_role.id,
                is_active=True,
            )
            session.add(admin_user)
            logger.info("Superuser created", email=admin_email)
        else:
            logger.info("Superuser already exists", email=admin_email)

        await session.commit()
        logger.info("Seeding completed successfully!")


if __name__ == "__main__":
    import logging
    import sys

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    asyncio.run(seed_db())
