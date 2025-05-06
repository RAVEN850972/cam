"""
Модель услуги для CRM-системы кондиционеров.
"""
from sqlalchemy import Column, String, Float, Boolean, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel
from config import INSTALLER_SERVICE_BONUS

class Service(BaseModel):
    """
    Модель услуги или товара.
    """
    # Основные поля
    name = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)  # Категория (Монтаж, Кондиционер, Доп услуга, и т.д.)
    power_type = Column(String, nullable=True)  # Тип мощности для кондиционеров (7 БТЮ, 9 БТЮ и т.д.)
    
    # Ценовые поля
    purchase_price = Column(Float, default=0)  # Закупочная цена (для товаров)
    selling_price = Column(Float, nullable=False)  # Продажная цена
    default_price = Column(Float, nullable=True)  # Базовая цена (для монтажа)
    
    # Поля для расчета комиссий
    is_manager_bonus = Column(Boolean, default=False)  # Идет ли комиссия менеджеру
    installer_bonus_fixed = Column(Float, default=INSTALLER_SERVICE_BONUS)  # Фиксированная оплата монтажнику
    profit_margin_percent = Column(Float, default=0.3)  # Процент прибыли
    
    # Отношения
    order_services = relationship("OrderService", back_populates="service")
    
    def __repr__(self):
        return f"<Service(id={self.id}, name='{self.name}', category='{self.category}', price={self.selling_price})>"