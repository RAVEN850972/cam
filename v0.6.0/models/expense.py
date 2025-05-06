"""
Модель расхода для CRM-системы кондиционеров.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Expense(BaseModel):
    """
    Модель расхода компании.
    """
    # Основные поля
    category = Column(String, nullable=False)  # Категория расхода
    amount = Column(Float, nullable=False)  # Сумма расхода
    description = Column(String, nullable=True)  # Описание расхода
    expense_date = Column(String, nullable=False)  # Дата расхода (YYYY-MM-DD)
    
    # Дополнительные поля для анализа
    expense_type = Column(String, nullable=False)  # Тип расхода: операционный, закупка товара, и т.д.
    related_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # Связанный заказ
    related_service_id = Column(Integer, ForeignKey("services.id"), nullable=True)  # Связанная услуга
    
    # Отношения
    related_order = relationship("Order", foreign_keys=[related_order_id])
    related_service = relationship("Service", foreign_keys=[related_service_id])
    
    def __repr__(self):
        return f"<Expense(id={self.id}, category='{self.category}', amount={self.amount})>"