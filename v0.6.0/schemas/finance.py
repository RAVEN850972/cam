"""
Pydantic-схемы для финансовых операций и отчетов.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime

class CompanyBalanceBase(BaseModel):
    """Базовая схема для баланса компании"""
    balance: float
    initial_balance: float
    last_transaction_id: Optional[int] = None
    last_transaction_type: Optional[str] = None


class CompanyBalanceCreate(BaseModel):
    """Схема для создания баланса компании"""
    initial_balance: float
    
    @validator('initial_balance')
    def validate_initial_balance(cls, v):
        if v < 0:
            raise ValueError('Начальный баланс не может быть отрицательным')
        return v


class CompanyBalanceResponse(CompanyBalanceBase):
    """Схема для ответа с данными баланса компании"""
    id: int
    updated_at: str
    
    class Config:
        from_attributes = True


class FinanceSummaryResponse(BaseModel):
    """Схема для ответа с финансовой сводкой"""
    total_revenue: float
    total_expenses: float
    total_profit: float
    total_commissions: float
    expenses_by_category: Dict[str, float]
    revenue_by_source: Dict[str, float]
    current_balance: float


class CashFlowForecastItem(BaseModel):
    """Элемент прогноза денежных потоков"""
    month: str
    forecasted_revenue: float
    forecasted_expenses: float
    forecasted_profit: float
    forecasted_balance: float


class CashFlowForecastResponse(BaseModel):
    """Схема для ответа с прогнозом денежных потоков"""
    forecast: List[CashFlowForecastItem]