"""
Модель финансовой транзакции для CRM-системы кондиционеров.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class FinancialTransaction(BaseModel):
    """
    Модель финансовой транзакции для учета всех движений средств.
    """
    # Основные поля
    transaction_date = Column(String, nullable=False)  # Дата транзакции
    amount = Column(Float, nullable=False)  # Сумма транзакции
    transaction_type = Column(String, nullable=False)  # Тип: доход, расход
    source_type = Column(String, nullable=False)  # Источник: заказ, вклад владельца, и т.д.
    source_id = Column(Integer, nullable=True)  # ID источника - заказа, расхода или выплаты
    description = Column(String, nullable=True)  # Описание
    
    def __repr__(self):
        return f"<FinancialTransaction(id={self.id}, type='{self.transaction_type}', amount={self.amount})>"