import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.rbac import AccessRolesRules, BusinessElement, Role
from app.schemas.rbac import RuleRead, RuleUpdate

logger = structlog.get_logger()

router = APIRouter()


# Вспомогательная функция проверки на Админа
def check_admin_privileges(request: Request) -> None:
    user = request.state.user
    if not user:
        logger.warning(
            "Admin access denied: unauthenticated user", path=request.url.path
        )
        raise HTTPException(status_code=401, detail="Not authenticated")
    if user.role.name != "Admin":
        logger.warning(
            "Admin access denied: insufficient privileges",
            user_id=user.id,
            role_name=user.role.name,
            path=request.url.path,
        )
        raise HTTPException(status_code=403, detail="Admins only")


@router.get("/rules", response_model=list[RuleRead])
async def get_all_rules(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_admin_privileges),
) -> list[RuleRead]:
    """
    Получить список всех правил доступа.
    Показывает матрицу: Роль -> Элемент -> Права.
    """
    user = request.state.user
    logger.info("Admin requested all RBAC rules", admin_id=user.id)
    stmt = (
        select(AccessRolesRules)
        .options(
            selectinload(AccessRolesRules.role), selectinload(AccessRolesRules.element)
        )
        .order_by(AccessRolesRules.role_id)
    )
    result = await db.execute(stmt)
    rules = result.scalars().all()

    # Преобразование ORM модели в Pydantic
    response = []
    for r in rules:
        response.append(
            RuleRead(
                role_name=r.role.name,
                element_key=r.element.key,
                element_name=r.element.name,
                create_permission=r.create_permission,
                read_permission=r.read_permission,
                read_all_permission=r.read_all_permission,
                update_permission=r.update_permission,
                update_all_permission=r.update_all_permission,
                delete_permission=r.delete_permission,
                delete_all_permission=r.delete_all_permission,
            )
        )
    logger.debug(
        "RBAC rules retrieved successfully", admin_id=user.id, rule_count=len(response)
    )
    return response


@router.put("/rules/{role_name}/{element_key}", response_model=RuleRead)
async def update_rule(
    role_name: str,
    element_key: str,
    rule_in: RuleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_admin_privileges),
) -> RuleRead:
    """
    Обновить или создать права для конкретной роли на конкретный элемент.
    """
    user = request.state.user
    logger.info(
        "Admin updating RBAC rule",
        admin_id=user.id,
        target_role=role_name,
        target_element=element_key,
    )
    # Поиск Роли и Элемена по имени
    role = (
        await db.execute(select(Role).where(Role.name == role_name))
    ).scalar_one_or_none()
    element = (
        await db.execute(
            select(BusinessElement).where(BusinessElement.key == element_key)
        )
    ).scalar_one_or_none()

    if not role or not element:
        logger.warning(
            "RBAC rule update failed: role or element not found",
            admin_id=user.id,
            target_role=role_name,
            target_element=element_key,
            role_found=bool(role),
            element_found=bool(element),
        )
        raise HTTPException(status_code=404, detail="Role or Element not found")

    # Поиск существующего правила
    stmt = select(AccessRolesRules).where(
        AccessRolesRules.role_id == role.id, AccessRolesRules.element_id == element.id
    )
    rule = (await db.execute(stmt)).scalar_one_or_none()

    is_new = False

    # Если правила нет - создать, если есть - обновить
    if not rule:
        rule = AccessRolesRules(role_id=role.id, element_id=element.id)
        db.add(rule)

    # Обновление полей
    rule.create_permission = rule_in.create_permission
    rule.read_permission = rule_in.read_permission
    rule.read_all_permission = rule_in.read_all_permission
    rule.update_permission = rule_in.update_permission
    rule.update_all_permission = rule_in.update_all_permission
    rule.delete_permission = rule_in.delete_permission
    rule.delete_all_permission = rule_in.delete_all_permission

    await db.commit()
    await db.refresh(rule)

    logger.info(
        "RBAC rule updated successfully",
        admin_id=user.id,
        target_role=role_name,
        target_element=element_key,
        is_new=is_new,
    )

    # Для ответа подгрузка связи
    return RuleRead(
        role_name=role.name,
        element_key=element.key,
        element_name=element.name,
        **rule.__dict__,
    )
