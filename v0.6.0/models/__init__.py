"""
Инициализация модулей моделей данных.
"""
from .base import BaseModel
from .employee import Employee
from .client import Client
from .service import Service
from .order import Order, OrderEmployee, OrderService
from .expense import Expense
from .payment import Payment
from .transaction import FinancialTransaction
from .company_balance import CompanyBalance

# Список всех моделей для упрощения импорта
__all__ = [
    'BaseModel',
    'Employee',
    'Client',
    'Service',
    'Order',
    'OrderEmployee',
    'OrderService',
    'Expense',
    'Payment',
    'FinancialTransaction',
    'CompanyBalance'
]