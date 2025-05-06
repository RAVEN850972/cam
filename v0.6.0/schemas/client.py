"""
Pydantic-схемы для клиентов.
"""
import re
from typing import Optional, List
from pydantic import BaseModel, validator
from config import CLIENT_SOURCES

class ClientBase(BaseModel):
    """Базовая схема для клиентов"""
    name: str
    phone: str
    source: str
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Имя клиента не может быть пустым')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+?[0-9]{10,12}$', v.replace(' ', '')):
            raise ValueError('Неверный формат номера телефона')
        return v.replace(' ', '')
    
    @validator('source')
    def validate_source(cls, v):
        if v not in CLIENT_SOURCES:
            raise ValueError(f'Источник должен быть одним из: {", ".join(CLIENT_SOURCES)}')
        return v


class ClientCreate(ClientBase):
    """Схема для создания клиента"""
    pass


class ClientUpdate(ClientBase):
    """Схема для обновления клиента"""
    name: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None


class ClientResponse(ClientBase):
    """Схема для ответа с данными клиента"""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        orm_mode = True