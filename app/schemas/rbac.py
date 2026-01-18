from pydantic import BaseModel, ConfigDict


# Базовая схема с флагами
class RuleBase(BaseModel):
    create_permission: bool = False
    read_permission: bool = False
    read_all_permission: bool = False
    update_permission: bool = False
    update_all_permission: bool = False
    delete_permission: bool = False
    delete_all_permission: bool = False


# Схема для обновления
class RuleUpdate(RuleBase):
    pass


# Схема для чтения
class RuleRead(RuleBase):
    role_name: str
    element_key: str
    element_name: str

    model_config = ConfigDict(from_attributes=True)
