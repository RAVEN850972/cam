"""
Pydantic-схемы для финансовых транзакций.
"""
from typing import Optional
from pydantic import BaseModel, validator
from datetime import datetime
from config import TRANSACTION_TYPES, TRANSACTION_SOURCE_TYPES

class TransactionBase(BaseModel):
    """Базовая схема для финансовых транзакций"""
    transaction_date: str
    amount: float
    transaction_type: str
    source_type: str
    source_id: Optional[int] = None
    description: Optional[str] = None
    
    @validator('transaction_date')
    def validate_transaction_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Дата транзакции должна быть в формате YYYY-MM-DD')
        return v
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        if v not in TRANSACTION_TYPES:
            raise ValueError(f'Тип транзакции должен быть одним из: {", ".join(TRANSACTION_TYPES)}')
        return v
    
    @validator('source_type')
    def validate_source_type(cls, v):
        if v not in TRANSACTION_SOURCE_TYPES:
            raise ValueError(f'Тип источника должен быть одним из: {", ".join(TRANSACTION_SOURCE_TYPES)}')
        return v


class TransactionCreate(TransactionBase):
    """Схема для создания транзакции"""
    pass


class TransactionUpdate(TransactionBase):
    """Схема для обновления транзакции"""
    transaction_date: Optional[str] = None
    amount: Optional[float] = None
    transaction_type: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    description: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Схема для ответа с данными транзакции"""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True