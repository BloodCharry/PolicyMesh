from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermission
from app.db.session import get_db
from app.services.permission_ops import PermissionService

router = APIRouter()


# Имитация БД
class Order(BaseModel):
    id: int
    title: str
    owner_id: int


# Создание пару заказов.
# Admin имеет ID=1, а User имеет ID=2 как после сида
MOCK_ORDERS = [
    Order(id=1, title="Заказ Админа #1", owner_id=1),
    Order(id=2, title="Заказ Юзера #2", owner_id=2),
    Order(id=3, title="Заказ Юзера #3", owner_id=2),
]


# Endpoints


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    request: Request,
    title: str,
    # Проверка: Есть ли право создавать
    _: bool = Depends(RequirePermission(key="orders", action="create")),
) -> Order:
    """
    Создание заказа.
    Доступно и Admin, и User согласно сиду
    """
    user = request.state.user
    new_id = len(MOCK_ORDERS) + 1
    new_order = Order(id=new_id, title=title, owner_id=user.id)
    MOCK_ORDERS.append(new_order)
    return new_order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    # Проверка: Есть ли право удалять
    # User отсеется, так как у него delete_permission=False
    _: bool = Depends(RequirePermission(key="orders", action="delete")),
) -> None:
    """
    Удаление заказа.
    Доступно ТОЛЬКО Admin.
    """
    user = request.state.user

    # Найти заказ
    order = next((o for o in MOCK_ORDERS if o.id == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Доп. проверка прав
    # Здесь сервис для проверки конкретного объекта
    has_perm = await PermissionService.has_permission(
        db, user, "orders", "delete", owner_id=order.owner_id
    )

    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden by logic")

    MOCK_ORDERS.remove(order)
    return None


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    # Проверка: Есть ли право читать (User пройдет, так как read_permission=True)
    _: bool = Depends(RequirePermission(key="orders", action="read")),
) -> Order:
    """
    Просмотр конкретного заказа.
    Admin видит любой.
    User видит только СВОЙ.
    """
    user = request.state.user

    order = next((o for o in MOCK_ORDERS if o.id == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    #  Проверка ВЛАДЕНИЯ (User vs Admin)
    # Если это Admin -> у него read_all=True -> has_permission вернет True
    # Если это User -> у него read_all=False -> has_permission проверит owner_id == user.id
    has_perm = await PermissionService.has_permission(
        db, user, "orders", "read", owner_id=order.owner_id
    )

    if not has_perm:
        raise HTTPException(
            status_code=403, detail="You do not have access to this order"
        )

    return order
