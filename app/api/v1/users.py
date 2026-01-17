from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserRead

router = APIRouter()


@router.get("/profile", response_model=UserRead)
async def read_profile(request: Request) -> UserRead:
    """
    Получить данные текущего пользователя.
    """
    user = getattr(request.state, "user", None)

    if not user:
        # Если Middleware не отработал или токен невалиден
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    return UserRead.model_validate(user)


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(request: Request, db: AsyncSession = Depends(get_db)) -> None:
    """
    Мягкое удаление профиля (is_active = False).
    """
    user = getattr(request.state, "user", None)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    user.is_active = False

    # Мы добавляем user в текущую сессию, чтобы SQLAlchemy отследил изменения
    db.add(user)
    await db.commit()

    return None
