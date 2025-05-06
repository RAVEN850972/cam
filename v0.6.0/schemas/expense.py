"""
Pydantic-схемы для расходов.
"""
from typing import Optional
from pydantic import BaseModel, validator
from datetime import datetime
from config import EXPENSE_CATEGORIES, EXPENSE_TYPES

class ExpenseBase(BaseModel):
    """Базовая схема для расходов"""
    category: str
    amount: float
    description: Optional[str] = None
    expense_date: str
    expense_type: str = "операционный"
    related_order_id: Optional[int] = None
    related_service_id: Optional[int] = None
    
    @validator('category')
    def validate_category(cls, v):
        if v not in EXPENSE_CATEGORIES:
            raise ValueError(f'Категория должна быть одной из: {", ".join(EXPENSE_CATEGORIES)}')
        return v
    
    @validator('expense_type')
    def validate_expense_type(cls, v):
        if v not in EXPENSE_TYPES:
            raise ValueError(f'Тип расхода должен быть одним из: {", ".join(EXPENSE_TYPES)}')
        return v
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Сумма расхода должна быть положительной')
        return v
    
    @validator('expense_date')
    def validate_expense_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Дата расхода должна быть в формате YYYY-MM-DD')
        return v


class ExpenseCreate(ExpenseBase):
    """Схема для создания расхода"""
    pass


class ExpenseUpdate(ExpenseBase):
    """Схема для обновления расхода"""
    category: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    expense_date: Optional[str] = None
    expense_type: Optional[str] = None
    related_order_id: Optional[int] = None
    related_service_id: Optional[int] = None


class ExpenseResponse(ExpenseBase):
    """Схема для ответа с данными расхода"""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        orm_mode = True