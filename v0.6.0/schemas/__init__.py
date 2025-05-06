"""
Инициализация Pydantic-схем для валидации данных.
"""
from .employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeSalaryResponse
from .client import ClientCreate, ClientUpdate, ClientResponse
from .service import ServiceCreate, ServiceUpdate, ServiceResponse
from .order import OrderCreate, OrderUpdate, OrderResponse, OrderProfitResponse, OrderServiceBase, OrderEmployeeBase
from .expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from .payment import PaymentCreate, PaymentUpdate, PaymentResponse
from .transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from .finance import CompanyBalanceCreate, CompanyBalanceResponse, FinanceSummaryResponse, CashFlowForecastResponse