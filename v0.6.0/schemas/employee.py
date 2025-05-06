"""
Pydantic-схемы для сотрудников.
"""
import re
from typing import Optional, List
from pydantic import BaseModel, validator
from datetime import datetime

class EmployeeBase(BaseModel):
    """Базовая схема для сотрудников"""
    name: str
    phone: str
    employee_type: str
    base_salary: Optional[float] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Имя сотрудника не может быть пустым')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+?[0-9]{10,12}$', v.replace(' ', '')):
            raise ValueError('Неверный формат номера телефона')
        return v.replace(' ', '')
    
    @validator('employee_type')
    def validate_employee_type(cls, v):
        valid_types = ['менеджер', 'монтажник', 'владелец']
        if v.lower() not in valid_types:
            raise ValueError(f'Тип сотрудника должен быть одним из: {", ".join(valid_types)}')
        return v.lower()


class EmployeeCreate(EmployeeBase):
    """Схема для создания сотрудника"""
    pass


class EmployeeUpdate(EmployeeBase):
    """Схема для обновления сотрудника"""
    name: Optional[str] = None
    phone: Optional[str] = None
    employee_type: Optional[str] = None
    active: Optional[int] = None


class EmployeeResponse(EmployeeBase):
    """Схема для ответа с данными сотрудника"""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    active: int = 1
    
    class Config:
        orm_mode = True


class EmployeeSalaryResponse(BaseModel):
    """Схема для ответа с данными зарплаты сотрудника"""
    employee: dict
    salary: float
    paid: float
    to_pay: float
    details: dict
    month: str
    
    class Config:
        orm_mode = True