from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User  # type: ignore[import-untyped]


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")

    # Связь с правилами
    rules: Mapped[list["AccessRolesRules"]] = relationship(
        back_populates="role", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class BusinessElement(Base):
    __tablename__ = "business_elements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    key: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    def __repr__(self) -> str:
        return f"<BusinessElement(key={self.key})>"


class AccessRolesRules(Base):
    """
    Таблица прав доступа (Matrix).
    Определяет, какие права есть у Role X на Element Y.
    """

    __tablename__ = "access_roles_rules"

    # Уникальность
    __table_args__ = (
        UniqueConstraint("role_id", "element_id", name="uq_role_element"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Связи
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    element_id: Mapped[int] = mapped_column(
        ForeignKey("business_elements.id"), nullable=False
    )

    # ORM связи
    role: Mapped["Role"] = relationship(back_populates="rules")
    element: Mapped["BusinessElement"] = relationship()

    # Флаги разрешений

    # C (Create)
    create_permission: Mapped[bool] = mapped_column(Boolean, default=False)

    # R (Read)
    read_permission: Mapped[bool] = mapped_column(Boolean, default=False)  # Читать свои
    read_all_permission: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Читать чужие

    # U (Update)
    update_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    update_all_permission: Mapped[bool] = mapped_column(Boolean, default=False)

    # D (Delete)
    delete_permission: Mapped[bool] = mapped_column(Boolean, default=False)
    delete_all_permission: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Rule(role={self.role_id}, elem={self.element_id}, R={self.read_permission})>"
