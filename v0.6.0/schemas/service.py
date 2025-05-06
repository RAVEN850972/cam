"""
Pydantic-схемы для услуг.
"""
from typing import Optional, List
from pydantic import BaseModel, validator, confloat
from config import SERVICE_CATEGORIES, INSTALLER_SERVICE_BONUS, AC_POWER_CATEGORIES

class ServiceBase(BaseModel):
    """Базовая схема для услуг"""
    name: str
    category: str
    power_type: Optional[str] = None
    purchase_price: Optional[float] = 0
    selling_price: float
    default_price: Optional[float] = None
    is_manager_bonus: Optional[bool] = False
    installer_bonus_fixed: Optional[float] = INSTALLER_SERVICE_BONUS
    profit_margin_percent: Optional[float] = 0.3
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Название услуги не может быть пустым')
        return v
    
    @validator('category')
    def validate_category(cls, v):
        if v not in SERVICE_CATEGORIES:
            raise ValueError(f'Категория должна быть одной из: {", ".join(SERVICE_CATEGORIES)}')
        return v
    
    @validator('power_type')
    def validate_power_type(cls, v, values):
        if v is not None and values.get('category') == 'Кондиционер' and v not in AC_POWER_CATEGORIES:
            raise ValueError(f'Тип мощности должен быть одним из: {", ".join(AC_POWER_CATEGORIES)}')
        return v
    
    @validator('selling_price')
    def validate_selling_price(cls, v):
        if v <= 0:
            raise ValueError('Цена продажи должна быть положительной')
        return v
    
    @validator('profit_margin_percent')
    def validate_profit_margin(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Процент прибыли должен быть от 0 до 1')
        return v


class ServiceCreate(ServiceBase):
    """Схема для создания услуги"""
    pass


class ServiceUpdate(ServiceBase):
    """Схема для обновления услуги"""
    name: Optional[str] = None
    category: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    default_price: Optional[float] = None
    is_manager_bonus: Optional[bool] = None
    installer_bonus_fixed: Optional[float] = None
    profit_margin_percent: Optional[float] = None


class ServiceResponse(ServiceBase):
    """Схема для ответа с данными услуги"""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        orm_mode = True