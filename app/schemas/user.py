from pydantic import BaseModel, ConfigDict, EmailStr


# Базовая схема
class UserBase(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None


# Схема для регистрации
class UserCreate(UserBase):
    password: str
    password_confirm: str  # Поле для проверки, но в БД не пойдет


# Схема для чтения
class UserRead(UserBase):
    id: int
    is_active: bool
    role_id: int

    # Настройка для работы с ORM объектами
    model_config = ConfigDict(from_attributes=True)
