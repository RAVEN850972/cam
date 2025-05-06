"""
Базовые модели данных для CRM-системы кондиционеров.
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from database import Base

class BaseModel(Base):
    """
    Базовая модель с общими полями для всех моделей системы.
    Используется как миксин и не создается как таблица в БД.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated_at = Column(String, onupdate=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    @declared_attr
    def __tablename__(cls):
        """
        Автоматически создает имя таблицы из имени класса.
        Например, класс Employee будет использовать таблицу "employees".
        """
        return cls.__name__.lower() + 's'