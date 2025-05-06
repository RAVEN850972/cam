"""
Модель выплаты для CRM-системы кондиционеров.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Payment(BaseModel):
    """
    Модель выплаты сотруднику.
    """
    # Основные поля
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Сумма выплаты (положительная — выплата, отрицательная — штраф)
    payment_date = Column(String, nullable=False)  # Дата платежа в формате YYYY-MM-DD
    description = Column(String, nullable=True)  # Описание платежа
    
    # Отношения
    employee = relationship("Employee", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, employee_id={self.employee_id}, amount={self.amount})>"