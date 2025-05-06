"""
Pydantic-схемы для заказов.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime
from config import ORDER_STATUSES, DEFAULT_MOUNT_PRICE, OWNER_MOUNT_COMMISSION

class OrderServiceBase(BaseModel):
    """Базовая схема для услуг в заказе"""
    service_id: int
    selling_price: float
    sold_by_id: Optional[int] = None


class OrderEmployeeBase(BaseModel):
    """Базовая схема для сотрудников в заказе"""
    employee_id: int
    employee_type: str
    base_payment: float
    
    @validator('employee_type')
    def validate_employee_type(cls, v):
        valid_types = ['монтажник', 'владелец_на_монтаже']
        if v not in valid_types:
            raise ValueError(f'Тип сотрудника должен быть одним из: {", ".join(valid_types)}')
        return v


class OrderBase(BaseModel):
    """Базовая схема для заказов"""
    client_id: int
    manager_id: int
    order_date: str
    completion_date: Optional[str] = None
    notes: Optional[str] = None
    status: str = "новый"
    mount_price: float = DEFAULT_MOUNT_PRICE
    owner_commission: float = OWNER_MOUNT_COMMISSION
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ORDER_STATUSES:
            raise ValueError(f'Статус должен быть одним из: {", ".join(ORDER_STATUSES)}')
        return v
    
    @validator('order_date')
    def validate_order_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                datetime.strptime(v, "%Y-%m-%d")
                return v + " 00:00"
            except ValueError:
                raise ValueError('Дата заказа должна быть в формате YYYY-MM-DD или YYYY-MM-DD HH:MM')
        return v
    
    @validator('completion_date')
    def validate_completion_date(cls, v, values):
        if not v:
            return None
        
        try:
            completion = datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                datetime.strptime(v, "%Y-%m-%d")
                v = v + " 00:00"
                completion = datetime.strptime(v, "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError('Дата завершения должна быть в формате YYYY-MM-DD или YYYY-MM-DD HH:MM')
        
        # Проверяем, что дата завершения не раньше даты заказа
        if 'order_date' in values and values['order_date']:
            try:
                order_date = datetime.strptime(values['order_date'], "%Y-%m-%d %H:%M")
                if completion < order_date:
                    raise ValueError('Дата завершения не может быть раньше даты заказа')
            except ValueError:
                pass  # Пропускаем проверку, если с датой заказа что-то не так
        
        return v


class OrderCreate(OrderBase):
    """Схема для создания заказа"""
    services: List[OrderServiceBase]
    employees: Optional[List[OrderEmployeeBase]] = []


class OrderUpdate(OrderBase):
    """Схема для обновления заказа"""
    client_id: Optional[int] = None
    manager_id: Optional[int] = None
    order_date: Optional[str] = None
    status: Optional[str] = None
    mount_price: Optional[float] = None
    services: Optional[List[OrderServiceBase]] = None
    employees: Optional[List[OrderEmployeeBase]] = None


class OrderResponse(OrderBase):
    """Схема для ответа с данными заказа"""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    client: Dict[str, Any]  # Информация о клиенте
    manager: Dict[str, Any]  # Информация о менеджере
    services: List[Dict[str, Any]]  # Список услуг
    employees: List[Dict[str, Any]]  # Список сотрудников
    total_price: float  # Общая стоимость заказа
    
    class Config:
        orm_mode = True


class OrderProfitResponse(BaseModel):
    """Схема для ответа с данными о прибыли заказа"""
    revenue: float
    cost: float
    commissions: float
    profit: float
    details: Dict[str, Any]
    
    class Config:
        orm_mode = True