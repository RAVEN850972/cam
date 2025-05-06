"""
Модель клиента для CRM-системы кондиционеров.
"""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class Client(BaseModel):
    """
    Модель клиента.
    """
    # Основные поля
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    source = Column(String, nullable=False)  # Источник (Авито, ВК, и т.д.)
    
    # Отношения
    orders = relationship("Order", back_populates="client")
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', phone='{self.phone}')>"