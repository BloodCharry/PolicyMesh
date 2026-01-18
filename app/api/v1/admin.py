from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.rbac import AccessRolesRules, BusinessElement, Role
from app.schemas.rbac import RuleRead, RuleUpdate

router = APIRouter()


# Вспомогательная функция проверки на Админа
def check_admin_privileges(request: Request) -> None:
    user = request.state.user
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if user.role.name != "Admin":
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
        raise HTTPException(status_code=404, detail="Role or Element not found")

    # Поиск существующего правила
    stmt = select(AccessRolesRules).where(
        AccessRolesRules.role_id == role.id, AccessRolesRules.element_id == element.id
    )
    rule = (await db.execute(stmt)).scalar_one_or_none()

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

    # Для ответа подгрузка связи
    return RuleRead(
        role_name=role.name,
        element_key=element.key,
        element_name=element.name,
        **rule.__dict__,
    )
