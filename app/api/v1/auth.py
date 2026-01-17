
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.rbac import Role
from app.models.users import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_ops import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    """
    Регистрация нового пользователя.
    По умолчанию выдаем роль 'User'.
    """
    # Проверка паролей
    if user_in.password != user_in.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    # Проверка уникальности email
    stmt = select(User).where(User.email == user_in.email)
    existing_user = (await db.execute(stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Получение дефолтной роли
    role_stmt = select(Role).where(Role.name == "User")
    default_role = (await db.execute(role_stmt)).scalar_one_or_none()

    if not default_role:
        # Fallback на случай если БД пустая
        raise HTTPException(
            status_code=500, detail="Default role 'User' not found in DB"
        )

    # Создание пользователя
    hashed_pw = AuthService.get_password_hash(user_in.password)

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role_id=default_role.id,
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)  # Подгружаем ID и другие поля из БД

    return UserRead.model_validate(new_user)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Вход в систему по Email/Password.
    Возвращает Access и Refresh токены.
    """
    # Поиск пользователя
    stmt = select(User).where(User.email == login_data.email)
    user = (await db.execute(stmt)).scalar_one_or_none()

    # Проверка пользователя и пароля
    if not user or not AuthService.verify_password(
        login_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User is inactive")

    # Генерация токенов
    # В payload кладем ID и RoleID, чтобы не ходить в БД при каждой проверке прав
    payload = {"sub": str(user.id), "role_id": user.role_id}

    access_token = AuthService.create_access_token(payload)
    refresh_token = AuthService.create_refresh_token(payload)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout() -> dict[str, str]:
    """
    Выход из системы.
    Так как мы используем JWT (Stateless), сервер не хранит сессию.
    Клиент должен сам удалить токен из LocalStorage/Cookies.
    """
    return {"detail": "Logout successful. Please remove token from client storage."}
