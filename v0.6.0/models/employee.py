"""
Модель сотрудника для CRM-системы кондиционеров.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel
from config import MANAGER_BASE_SALARY

class Employee(BaseModel):
    """
    Модель сотрудника (менеджер, монтажник, владелец).
    """
    # Основные поля
    name = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=False)
    employee_type = Column(String, nullable=False)  # 'менеджер', 'монтажник', 'владелец'
    
    # Поля оплаты
    base_salary = Column(Float, nullable=True)  # Фиксированная часть зарплаты (для менеджера)
    active = Column(Integer, default=1)  # 1 - активный, 0 - неактивный
    
    # Отношения
    payments = relationship("Payment", back_populates="employee")
    managed_orders = relationship("Order", foreign_keys="Order.manager_id", back_populates="manager")
    order_participations = relationship("OrderEmployee", back_populates="employee")
    sold_services = relationship("OrderService", foreign_keys="OrderService.sold_by_id", back_populates="sold_by")
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', type='{self.employee_type}')>"