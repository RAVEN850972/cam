"""
Инициализация модулей роутеров API.
"""
from .employees import router as employee_router
from .clients import router as client_router
from .services import router as service_router
from .orders import router as order_router
from .finance import router as finance_router
from .export import router as export_router

# Список роутеров для упрощения импорта
__all__ = [
    'employee_router',
    'client_router',
    'service_router',
    'order_router',
    'finance_router',
    'export_router'
]