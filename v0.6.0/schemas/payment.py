"""
Pydantic-схемы для выплат сотрудникам.
"""
from typing import Optional
from pydantic import BaseModel, validator
from datetime import datetime

class PaymentBase(BaseModel):
    """Базовая схема для выплат"""
    employee_id: int
    amount: float
    payment_date: str
    description: Optional[str] = None
    
    @validator('payment_date')
    def validate_payment_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Дата выплаты должна быть в формате YYYY-MM-DD')
        return v


class PaymentCreate(PaymentBase):
    """Схема для создания выплаты"""
    pass


class PaymentUpdate(PaymentBase):
    """Схема для обновления выплаты"""
    employee_id: Optional[int] = None
    amount: Optional[float] = None
    payment_date: Optional[str] = None
    description: Optional[str] = None


class PaymentResponse(PaymentBase):
    """Схема для ответа с данными выплаты"""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    employee: dict  # Информация о сотруднике
    
    class Config:
        orm_mode = True