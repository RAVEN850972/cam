"""
Модели для заказов в CRM-системе кондиционеров.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel
from config import DEFAULT_MOUNT_PRICE, OWNER_MOUNT_COMMISSION

class Order(BaseModel):
    """
    Модель заказа.
    """
    # Основные поля
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    order_date = Column(String, nullable=False)  # Дата и время заказа
    completion_date = Column(String, nullable=True)  # Дата завершения
    notes = Column(String, nullable=True)  # Примечания
    status = Column(String, default="новый")  # Статус: новый, в работе, завершен, отменен
    
    # Финансовые поля
    mount_price = Column(Float, default=DEFAULT_MOUNT_PRICE)  # Фактическая стоимость монтажа
    owner_commission = Column(Float, default=OWNER_MOUNT_COMMISSION)  # Комиссия владельца (1500)
    
    # Отношения
    client = relationship("Client", back_populates="orders")
    manager = relationship("Employee", foreign_keys=[manager_id], back_populates="managed_orders")
    
    employees = relationship("OrderEmployee", back_populates="order")
    services = relationship("OrderService", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, client_id={self.client_id}, status='{self.status}')>"


class OrderEmployee(BaseModel):
    """
    Модель для связи заказа с сотрудниками (монтажниками).
    """
    # Основные поля
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    employee_type = Column(String, nullable=False)  # монтажник, владелец_на_монтаже
    base_payment = Column(Float, nullable=False)  # Базовый платеж (1500 для монтажника)
    
    # Отношения
    order = relationship("Order", back_populates="employees")
    employee = relationship("Employee", back_populates="order_participations")
    
    def __repr__(self):
        return f"<OrderEmployee(order_id={self.order_id}, employee_id={self.employee_id})>"


class OrderService(BaseModel):
    """
    Модель для связи заказа с услугами.
    """
    # Основные поля
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    selling_price = Column(Float, nullable=False)  # Фактическая продажная цена
    sold_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # ID сотрудника, который продал
    
    # Отношения
    order = relationship("Order", back_populates="services")
    service = relationship("Service", back_populates="order_services")
    sold_by = relationship("Employee", foreign_keys=[sold_by_id], back_populates="sold_services")
    
    def __repr__(self):
        return f"<OrderService(order_id={self.order_id}, service_id={self.service_id})>"