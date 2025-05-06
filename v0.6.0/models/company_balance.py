"""
Модель баланса компании для CRM-системы кондиционеров.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .base import BaseModel

class CompanyBalance(BaseModel):
    """
    Модель баланса компании.
    """
    # Основные поля
    balance = Column(Float, nullable=False)  # Текущий баланс
    initial_balance = Column(Float, nullable=False)  # Начальный баланс
    
    # Поля для отслеживания изменений
    last_transaction_id = Column(Integer, nullable=True)  # ID последней транзакции
    last_transaction_type = Column(String, nullable=True)  # Тип последней транзакции
    
    def __repr__(self):
        return f"<CompanyBalance(id={self.id}, balance={self.balance}, initial_balance={self.initial_balance})>"