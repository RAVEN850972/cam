from fastapi import FastAPI, Depends, Form, Request, HTTPException, Query, Path
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, func, desc, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
import pandas as pd
from io import BytesIO
from datetime import datetime, date, timedelta
import re
import io
import csv
from pydantic import BaseModel, validator, constr, confloat
import json
from fastapi.encoders import jsonable_encoder

app = FastAPI(title="CRM Система", description="CRM для компании по установке кондиционеров")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Настройки базы данных
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Модели SQLAlchemy
Base = declarative_base()

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)  # Категория расхода (Материалы, Бензин, Закупка кондиционеров, Прочее)
    amount = Column(Float, nullable=False)  # Сумма расхода
    description = Column(String, nullable=True)  # Описание расхода
    expense_date = Column(String, nullable=False)  # Дата расхода (YYYY-MM-DD)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated_at = Column(String, onupdate=lambda: datetime.now().strftime("%Y-%m-%d"))

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)  # Категория услуги
    material_cost = Column(Float, default=0)  # Себестоимость
    price = Column(Float, nullable=False)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated_at = Column(String, onupdate=lambda: datetime.now().strftime("%Y-%m-%d"))

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=False)  # Номер телефона
    employee_type = Column(String, nullable=False)  # 'менеджер' или 'монтажник'
    base_salary = Column(Float, nullable=True)  # Только для менеджера, может быть null
    order_rate = Column(Float, nullable=False)  # Ставка за заказ
    commission_rate = Column(Float, nullable=False)  # Процент от доп. услуг
    active = Column(Integer, default=1)  # 1 - активный, 0 - неактивный
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated_at = Column(String, onupdate=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    # Отношения
    payments = relationship("Payment", back_populates="employee")
    managed_orders = relationship("Order", foreign_keys="Order.manager_id", back_populates="manager")
    first_installer_orders = relationship("Order", foreign_keys="Order.one_employee_id", back_populates="first_installer")
    second_installer_orders = relationship("Order", foreign_keys="Order.two_employee_id", back_populates="second_installer")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    amount = Column(Float, nullable=False)  # Положительное значение — выплата, отрицательное — штраф
    payment_date = Column(String, nullable=False)  # Дата платежа в формате YYYY-MM-DD
    description = Column(String, nullable=True)  # Описание платежа
    
    # Отношения
    employee = relationship("Employee", back_populates="payments")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)  # Основная услуга (монтаж)
    one_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)  # Первый монтажник
    two_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # Второй монтажник
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=False)  # Менеджер
    order_date = Column(String, nullable=False)  # Дата и время заказа
    completion_date = Column(String, nullable=True)  # Дата завершения
    notes = Column(String, nullable=True)  # Примечания
    status = Column(String, default="новый")  # Статус: новый, в работе, завершен, отменен
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated_at = Column(String, onupdate=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    # Отношения
    client = relationship("Client", back_populates="orders")
    service = relationship("Service")
    first_installer = relationship("Employee", foreign_keys=[one_employee_id], back_populates="first_installer_orders")
    second_installer = relationship("Employee", foreign_keys=[two_employee_id], back_populates="second_installer_orders")
    manager = relationship("Employee", foreign_keys=[manager_id], back_populates="managed_orders")
    additional_services = relationship("OrderService", back_populates="order")

class OrderService(Base):
    __tablename__ = "order_services"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    # Отношения
    order = relationship("Order", back_populates="additional_services")
    service = relationship("Service")

class OrderUpdate(BaseModel):
    client_id: int
    service_id: int
    one_employee_id: int
    two_employee_id: Optional[int] = None
    manager_id: int
    order_date: str
    completion_date: Optional[str] = None
    notes: Optional[str] = None
    status: str
    additional_services: List[int] = []

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["новый", "в работе", "завершен", "отменен"]
        if v not in valid_statuses:
            raise ValueError(f"Статус должен быть одним из: {', '.join(valid_statuses)}")
        return v

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    source = Column(String, nullable=False)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated_at = Column(String, onupdate=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    # Отношения
    orders = relationship("Order", back_populates="client")

class CompanyBalance(Base):
    __tablename__ = "company_balance"
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, nullable=False)  # Текущий баланс
    initial_balance = Column(Float, nullable=False)  # Начальный баланс
    updated_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))

# Инициализация базы данных
Base.metadata.create_all(bind=engine)

# Pydantic модели для валидации
class ExpenseCreate(BaseModel):
    category: str
    amount: float
    description: Optional[str] = None
    expense_date: str
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ["Материалы", "Бензин", "Закупка кондиционеров", "Прочее"]
        if v not in valid_categories:
            raise ValueError(f"Категория должна быть одной из: {', '.join(valid_categories)}")
        return v
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Сумма расхода должна быть положительной')
        return v
    
    @validator('expense_date')
    def validate_expense_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Дата расхода должна быть в формате YYYY-MM-DD')
        return v

class ServiceCreate(BaseModel):
    name: str
    category: str
    material_cost: float = 0
    price: float
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Название услуги не может быть пустым')
        return v
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Цена должна быть положительной')
        return v

class EmployeeCreate(BaseModel):
    name: str
    phone: str
    employee_type: str
    base_salary: Optional[float] = None
    order_rate: float
    commission_rate: float
    
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
        if v.lower() not in ['менеджер', 'монтажник']:
            raise ValueError('Тип сотрудника должен быть "менеджер" или "монтажник"')
        return v.lower()
    
    @validator('commission_rate')
    def validate_commission_rate(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Процент комиссии должен быть от 0 до 1')
        return v

class ClientCreate(BaseModel):
    name: str
    phone: str
    source: str
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Имя клиента не может быть пустым')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+?[0-9]{10,12}$', v.replace(' ', '')):
            raise ValueError('Неверный формат номера телефона')
        return v.replace(' ', '')
    
    @validator('source')
    def validate_source(cls, v):
        valid_sources = ["Авито", "ВК", "Яндекс услуги", "Листовки", "Рекомендации", "Другое"]
        if v not in valid_sources:
            raise ValueError(f'Источник должен быть одним из: {", ".join(valid_sources)}')
        return v

class OrderCreate(BaseModel):
    client_id: int
    service_id: int
    one_employee_id: int
    two_employee_id: Optional[int] = None
    manager_id: int
    order_date: str
    notes: Optional[str] = None
    additional_services: List[int] = []

class InitialBalanceCreate(BaseModel):
    initial_balance: float

    @validator('initial_balance')
    def validate_initial_balance(cls, v):
        if v < 0:
            raise ValueError('Начальный баланс не может быть отрицательным')
        return v

# Функции для работы с БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_order_details(order_id: int, db: Session):
    """Получить детали заказа с учетом всех связанных данных"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None
        
    # Получаем основную услугу
    main_service = db.query(Service).filter(Service.id == order.service_id).first()
    
    # Получаем дополнительные услуги
    additional_services = []
    order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
    for os in order_services:
        service = db.query(Service).filter(Service.id == os.service_id).first()
        if service:
            additional_services.append({
                "id": service.id,
                "name": service.name,
                "price": service.price,
                "category": service.category
            })
    
    # Получаем исполнителей
    manager = db.query(Employee).filter(Employee.id == order.manager_id).first()
    first_installer = db.query(Employee).filter(Employee.id == order.one_employee_id).first()
    second_installer = None
    if order.two_employee_id:
        second_installer = db.query(Employee).filter(Employee.id == order.two_employee_id).first()
    
    # Получаем клиента
    client = db.query(Client).filter(Client.id == order.client_id).first()
    
    # Рассчитываем общую стоимость заказа
    total_price = main_service.price if main_service else 0
    for service in additional_services:
        total_price += service["price"]
    
    return {
        "id": order.id,
        "status": order.status,
        "order_date": order.order_date,
        "completion_date": order.completion_date,
        "notes": order.notes,
        "client": {
            "id": client.id,
            "name": client.name,
            "phone": client.phone
        } if client else None,
        "main_service": {
            "id": main_service.id,
            "name": main_service.name,
            "price": main_service.price,
            "category": main_service.category
        } if main_service else None,
        "additional_services": additional_services,
        "manager": {
            "id": manager.id,
            "name": manager.name
        } if manager else None,
        "first_installer": {
            "id": first_installer.id,
            "name": first_installer.name
        } if first_installer else None,
        "second_installer": {
            "id": second_installer.id,
            "name": second_installer.name
        } if second_installer else None,
        "total_price": total_price
    }

async def calculate_salary(db: Session, month: Optional[str] = None):
    """Расчет зарплаты сотрудников с улучшенной логикой"""
    # Если месяц не указан, используем текущий
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # Получаем данные из базы с минимальным количеством запросов
    employees = db.query(Employee).filter(Employee.active == 1).all()
    
    # Получаем только заказы за указанный месяц и только завершенные
    orders = db.query(Order).filter(
        Order.order_date.like(f"{month}%"), 
        Order.status == "завершен"
    ).all()
    
    # Получаем все доп. услуги для заказов этого месяца
    order_ids = [order.id for order in orders]
    if order_ids:  # Проверка на пустой список
        order_services = db.query(OrderService).filter(OrderService.order_id.in_(order_ids)).all()
    else:
        order_services = []
    
    # Получаем все платежи за указанный месяц
    payments = db.query(Payment).filter(Payment.payment_date.like(f"{month}%")).all()
    
    # Получаем все услуги
    all_services = {service.id: service for service in db.query(Service).all()}
    
    # Подготовка результатов
    result = {
        "salary": {},       # Зарплата к выплате
        "order_counts": {}, # Количество заказов
        "employee_ids": {}, # ID сотрудников
        "paid": {},         # Уже выплачено
        "details": {}       # Детали расчета для каждого сотрудника
    }
    
    for employee in employees:
        # Инициализация данных для сотрудника
        result["employee_ids"][employee.name] = employee.id
        result["order_counts"][employee.name] = 0
        result["details"][employee.name] = {
            "base_salary": employee.base_salary or 0,
            "order_payments": 0,
            "additional_commission": 0,
            "ac_commission": 0,
            "breakdown": {
                "orders": [],
                "payments": []
            }
        }
        
        # Базовая ставка для менеджеров
        salary = 0
        if employee.employee_type == "менеджер":
            salary += employee.base_salary or 0
        
        # Подсчет заказов и комиссий
        orders_count = 0
        additional_revenue = 0
        ac_revenue = 0
        
        for order in orders:
            order_data = {
                "id": order.id,
                "date": order.order_date,
                "amount": 0,
                "type": ""
            }
            
            # Проверяем участие сотрудника в заказе
            is_manager = employee.employee_type == "менеджер" and order.manager_id == employee.id
            is_installer = employee.employee_type == "монтажник" and (
                order.one_employee_id == employee.id or order.two_employee_id == employee.id
            )
            
            if not is_manager and not is_installer:
                continue
                
            # Увеличиваем счетчик заказов
            orders_count += 1
            
            # Начисляем ставку за заказ
            salary += employee.order_rate
            order_data["amount"] = employee.order_rate
            
            if is_manager:
                order_data["type"] = "Менеджер"
            else:
                order_data["type"] = "Монтажник"
            
            # Проверяем основную услугу заказа
            main_service = all_services.get(order.service_id)
            if main_service and main_service.category == "Кондиционер" and is_manager:
                ac_revenue += main_service.price
            
            # Суммируем стоимость доп. услуг для заказа
            for os in order_services:
                if os.order_id == order.id:
                    service = all_services.get(os.service_id)
                    if service:
                        if service.category == "Кондиционер" and is_manager:
                            ac_revenue += service.price
                        elif service.category == "Доп услуга":
                            additional_revenue += service.price
            
            result["details"][employee.name]["breakdown"]["orders"].append(order_data)
        
        # Сохраняем количество заказов
        result["order_counts"][employee.name] = orders_count
        
        # Начисляем процент от доп. услуг
        additional_commission = additional_revenue * employee.commission_rate
        salary += additional_commission
        result["details"][employee.name]["order_payments"] = orders_count * employee.order_rate
        result["details"][employee.name]["additional_commission"] = additional_commission
        
        # Начисляем процент от услуги "кондиционер" только менеджеру
        if employee.employee_type == "менеджер":
            ac_commission = ac_revenue * 0.3
            salary += ac_commission
            result["details"][employee.name]["ac_commission"] = ac_commission
        
        # Учитываем выплаты и штрафы
        employee_payments = [p for p in payments if p.employee_id == employee.id]
        paid_amount = 0
        for payment in employee_payments:
            paid_amount += payment.amount
            result["details"][employee.name]["breakdown"]["payments"].append({
                "id": payment.id,
                "date": payment.payment_date,
                "amount": payment.amount,
                "description": payment.description or ("Штраф" if payment.amount < 0 else "Выплата")
            })
        
        # Сохраняем результаты
        result["salary"][employee.name] = salary
        result["paid"][employee.name] = paid_amount
    
    return result

# Новый эндпоинт для установки начального баланса
@app.post("/api/balance/initial", response_class=JSONResponse)
async def set_initial_balance(balance_data: InitialBalanceCreate, db: Session = Depends(get_db)):
    try:
        # Проверяем, есть ли уже запись о балансе
        existing_balance = db.query(CompanyBalance).first()
        if existing_balance:
            return {"message": "Начальный баланс уже установлен", "status": "error"}

        new_balance = CompanyBalance(
            balance=balance_data.initial_balance,
            initial_balance=balance_data.initial_balance,
            updated_at=datetime.now().strftime("%Y-%m-%d")
        )
        db.add(new_balance)
        db.commit()
        db.refresh(new_balance)
        return {"message": "Начальный баланс успешно установлен", "status": "success", "balance": new_balance.balance}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при установке начального баланса: {str(e)}", "status": "error"}

# Новый эндпоинт для получения текущего баланса
@app.get("/api/balance", response_class=JSONResponse)
async def get_balance(db: Session = Depends(get_db)):
    balance = db.query(CompanyBalance).first()
    if not balance:
        return {"balance": None, "initial_balance_set": False}
    return {
        "balance": balance.balance,
        "initial_balance": balance.initial_balance,
        "initial_balance_set": True,
        "updated_at": balance.updated_at
    }

# Эндпоинт для API дашборда
@app.get("/api/dashboard", response_class=JSONResponse)
async def get_dashboard_data(month: str = None, db: Session = Depends(get_db)):
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # Получаем завершенные заказы за месяц
    completed_orders = db.query(Order).filter(
        Order.order_date.like(f"{month}%"),
        Order.status == "завершен"
    ).count()
    
    # Получаем заказы в работе
    in_progress_orders = db.query(Order).filter(
        Order.order_date.like(f"{month}%"),
        Order.status == "в работе"
    ).count()
    
    # Рассчитываем выручку и прибыль
    orders = db.query(Order).filter(
        Order.order_date.like(f"{month}%"),
        Order.status == "завершен"
    ).all()
    
    total_revenue = 0
    total_costs = 0
    for order in orders:
        service = db.query(Service).filter(Service.id == order.service_id).first()
        if service:
            total_revenue += service.price
            total_costs += service.material_cost
        
        order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
        for os in order_services:
            additional_service = db.query(Service).filter(Service.id == os.service_id).first()
            if additional_service:
                total_revenue += additional_service.price
                total_costs += additional_service.material_cost
    
    salary_data = await calculate_salary(db, month)
    total_salary = sum(salary_data["salary"].values())
    total_expenses = total_costs + total_salary
    total_profit = total_revenue - total_expenses
    
    # Популярные услуги
    categories = ["Монтаж", "Демонтаж", "Кондиционер", "Фреон", "Доп услуга"]
    popular_services = []
    for category in categories:
        main_services_count = db.query(Order).join(Service).filter(
            Service.category == category,
            Order.order_date.like(f"{month}%"),
            Order.status == "завершен"
        ).count()
        
        additional_services_count = db.query(OrderService).join(Service).filter(
            Service.category == category
        ).join(Order).filter(
            Order.order_date.like(f"{month}%"),
            Order.status == "завершен"
        ).count()
        
        total_count = main_services_count + additional_services_count
        if total_count > 0:
            popular_services.append({"name": category, "count": total_count})
    
    popular_services.sort(key=lambda x: x["count"], reverse=True)
    popular_services = popular_services[:5]  # Топ-5
    
    # Топ монтажников
    top_installers = []
    employees = db.query(Employee).filter(Employee.active == 1, Employee.employee_type == "монтажник").all()
    for emp in employees:
        orders_count = db.query(Order).filter(
            or_(
                Order.one_employee_id == emp.id,
                Order.two_employee_id == emp.id
            ),
            Order.order_date.like(f"{month}%"),
            Order.status == "завершен"
        ).count()
        if orders_count > 0:
            top_installers.append({"name": emp.name, "orders": orders_count})
    
    top_installers.sort(key=lambda x: x["orders"], reverse=True)
    top_installers = top_installers[:5]  # Топ-5
    
    # Данные для графика (выручка и прибыль по месяцам за последний год)
    monthly_data = []
    current_date = datetime.strptime(month, "%Y-%m")
    for i in range(12):
        past_month = (current_date - timedelta(days=30 * i)).strftime("%Y-%m")
        past_orders = db.query(Order).filter(
            Order.order_date.like(f"{past_month}%"),
            Order.status == "завершен"
        ).all()
        
        month_revenue = 0
        month_costs = 0
        for order in past_orders:
            service = db.query(Service).filter(Service.id == order.service_id).first()
            if service:
                month_revenue += service.price
                month_costs += service.material_cost
            
            order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
            for os in order_services:
                additional_service = db.query(Service).filter(Service.id == os.service_id).first()
                if additional_service:
                    month_revenue += additional_service.price
                    month_costs += additional_service.material_cost
        
        month_salary_data = await calculate_salary(db, past_month)
        month_salary = sum(month_salary_data["salary"].values())
        month_expenses = month_costs + month_salary
        month_profit = month_revenue - month_expenses
        
        monthly_data.append({
            "month": past_month,
            "revenue": month_revenue,
            "profit": month_profit
        })
    
    monthly_data.sort(key=lambda x: x["month"])  # Сортируем по дате
    
    return {
        "completed_orders": completed_orders,
        "in_progress_orders": in_progress_orders,
        "revenue": total_revenue,
        "profit": total_profit,
        "popular_services": popular_services,
        "top_installers": top_installers,
        "monthly_data": monthly_data
    }

# Главная страница с дашбордом
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(
    request: Request, 
    month: str = None, 
    db: Session = Depends(get_db)
):
    # Если месяц не указан, используем текущий
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # Получаем только завершенные заказы за указанный месяц
    orders = db.query(Order).filter(
        Order.order_date.like(f"{month}%"),
        Order.status == "завершен"
    ).all()
    
    # Общее количество заказов, включая все статусы
    all_orders = db.query(Order).filter(
        Order.order_date.like(f"{month}%")
    ).all()
    
    # Получаем количество клиентов за указанный месяц
    new_clients_count = db.query(Client).filter(
        Client.created_at.like(f"{month}%")
    ).count()
    
    # Рассчитываем выручку, себестоимость и прибыль с JOIN для оптимизации
    total_revenue = 0
    total_costs = 0
    
    for order in orders:
        # Основная услуга
        service = db.query(Service).filter(Service.id == order.service_id).first()
        if service:
            total_revenue += service.price
            total_costs += service.material_cost
        
        # Дополнительные услуги
        order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
        for os in order_services:
            additional_service = db.query(Service).filter(Service.id == os.service_id).first()
            if additional_service:
                total_revenue += additional_service.price
                total_costs += additional_service.material_cost
    
    # Получаем информацию о сотрудниках, услугах и клиентах для отображения
    services = db.query(Service).all()
    employees = db.query(Employee).filter(Employee.active == 1).all()
    clients = db.query(Client).all()
    
    # Загружаем данные о зарплатах для этого месяца
    salary_data = await calculate_salary(db, month)
    total_salary = sum(salary_data["salary"].values())
    
    # Общие расходы включают зарплаты и себестоимость материалов
    total_expenses = total_costs + total_salary
    
    # Чистая прибыль
    total_profit = total_revenue - total_expenses
    
    # Статистика по источникам клиентов
    sources = ["Авито", "ВК", "Яндекс услуги", "Листовки", "Рекомендации", "Другое"]
    client_sources = {}
    for source in sources:
        client_sources[source] = db.query(Client).filter(
            Client.source == source,
            Client.created_at.like(f"{month}%")
        ).count()
    
    # Статистика по категориям услуг
    categories = ["Монтаж", "Демонтаж", "Кондиционер", "Фреон", "Доп услуга"]
    service_categories = {}
    for category in categories:
        # Считаем количество основных услуг по категории
        main_services_count = db.query(Order).join(Service).filter(
            Service.category == category,
            Order.order_date.like(f"{month}%"),
            Order.status == "завершен"
        ).count()
        
        # Считаем количество доп. услуг по категории
        additional_services_count = db.query(OrderService).join(Service).filter(
            Service.category == category
        ).join(Order).filter(
            Order.order_date.like(f"{month}%"),
            Order.status == "завершен"
        ).count()
        
        service_categories[category] = main_services_count + additional_services_count
    
    # Получаем данные по статусам заказов
    statuses = ["новый", "в работе", "завершен", "отменен"]
    order_statuses = {}
    for status in statuses:
        order_statuses[status] = db.query(Order).filter(
            Order.status == status,
            Order.order_date.like(f"{month}%")
        ).count()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": services,
        "employees": employees,
        "orders": orders,
        "all_orders_count": len(all_orders),
        "completed_orders_count": len(orders),
        "clients": clients,
        "new_clients_count": new_clients_count,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "total_profit": total_profit,
        "current_month": month,
        "client_sources": client_sources,
        "service_categories": service_categories,
        "order_statuses": order_statuses
    })

# Страница для заказов с пагинацией и фильтрацией
@app.get("/orders", response_class=HTMLResponse)
async def read_orders(
    request: Request, 
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = None,
    client_name: str = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db)
):
    # Базовый запрос
    query = db.query(Order).order_by(desc(Order.created_at))
    
    # Применяем фильтры
    if status:
        query = query.filter(Order.status == status)
    if client_name:
        query = query.filter(Order.client.has(name=client_name))
    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)
    
    # Получаем общее количество записей
    total_count = query.count()
    
    # Применяем пагинацию
    orders = query.offset((page - 1) * limit).limit(limit).all()
    
    # Получаем дополнительные данные для отображения
    statuses = ["новый", "в работе", "завершен", "отменен"]
    clients = db.query(Client).all()
    services = db.query(Service).all()
    employees = db.query(Employee).filter(Employee.active == 1).all()
    
    # Вычисляем общее количество страниц
    total_pages = (total_count + limit - 1) // limit
    
    # Получаем детали для каждого заказа
    order_details = []
    for order in orders:
        detail = await get_order_details(order.id, db)
        if detail:
            order_details.append(detail)
    
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": order_details,
            "clients": clients,
            "services": services,
            "employees": employees,
            "statuses": statuses,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "limit": limit,
            "status_filter": status,
            "client_name_filter": client_name,
            "date_from_filter": date_from,
            "date_to_filter": date_to
        }
    )

# Страница для услуг
@app.get("/services", response_class=HTMLResponse)
async def read_services(request: Request, db: Session = Depends(get_db)):
    services = db.query(Service).all()
    categories = ["Монтаж", "Демонтаж", "Кондиционер", "Фреон", "Доп услуга"]
    
    # Статистика по категориям услуг
    category_stats = {}
    for category in categories:
        count = db.query(Service).filter(Service.category == category).count()
        avg_price = db.query(func.avg(Service.price)).filter(Service.category == category).scalar() or 0
        category_stats[category] = {
            "count": count,
            "avg_price": round(avg_price, 2)
        }
    
    return templates.TemplateResponse("services.html", {
        "request": request, 
        "services": services, 
        "categories": categories,
        "category_stats": category_stats
    })

# API-эндпоинт для получения списка услуг с фильтрацией
@app.get("/api/services/list", response_class=JSONResponse)
async def get_services_list(
    search: str = Query("", alias="search"),
    category: str = Query(None, alias="category"),
    db: Session = Depends(get_db)
):
    # Базовый запрос
    query = db.query(Service).order_by(Service.name)
    
    # Фильтрация по названию
    if search:
        query = query.filter(Service.name.ilike(f"%{search}%"))
    
    # Фильтрация по категории
    if category and category != "Все":
        query = query.filter(Service.category == category)
    
    # Получаем список услуг
    services = query.all()
    
    # Подсчет статистики по категориям
    categories = ["Монтаж", "Демонтаж", "Кондиционер", "Фреон", "Доп услуга"]
    stats = {}
    for cat in categories:
        count = db.query(Service).filter(Service.category == cat).count()
        avg_price = db.query(func.avg(Service.price)).filter(Service.category == cat).scalar() or 0
        stats[cat] = {
            "count": count,
            "avg_price": round(avg_price, 2)
        }
    
    # Формируем список услуг
    services_list = []
    for service in services:
        # Подсчет использования услуги в заказах
        main_usage = db.query(Order).filter(Order.service_id == service.id).count()
        additional_usage = db.query(OrderService).filter(OrderService.service_id == service.id).count()
        total_usage = main_usage + additional_usage
        
        services_list.append({
            "id": service.id,
            "name": service.name,
            "category": service.category,
            "material_cost": service.material_cost,
            "price": service.price,
            "created_at": service.created_at,
            "updated_at": service.updated_at,
            "total_usage": total_usage
        })
    
    return {
        "services": services_list,
        "stats": stats,
        "categories": categories
    }

# Страница для сотрудников
@app.get("/employees", response_class=HTMLResponse)
async def read_employees(
    request: Request, 
    month: str = None,
    db: Session = Depends(get_db)
):
    # Если месяц не указан, используем текущий
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # Получаем только активных сотрудников
    employees = db.query(Employee).filter(Employee.active == 1).all()
    
    # Получаем данные о зарплате
    salary_data = await calculate_salary(db, month)
    
    # Статистика для инфо-блоков
    total_employees = len(employees)
    total_to_pay = sum(salary_data["salary"].get(emp.name, 0) - salary_data["paid"].get(emp.name, 0) for emp in employees)
    total_paid = sum(salary_data["paid"].get(emp.name, 0) for emp in employees)
    
    # Типы сотрудников
    employee_types = ["Менеджер", "Монтажник"]
    
    # Получаем все данные о выплатах за месяц
    payments = db.query(Payment).filter(Payment.payment_date.like(f"{month}%")).all()
    
    # Группируем выплаты по сотрудникам
    payment_history = {}
    for payment in payments:
        employee = db.query(Employee).filter(Employee.id == payment.employee_id).first()
        if employee:
            if employee.name not in payment_history:
                payment_history[employee.name] = []
            payment_history[employee.name].append({
                "id": payment.id,
                "date": payment.payment_date,
                "amount": payment.amount,
                "description": payment.description or ("Штраф" if payment.amount < 0 else "Выплата")
            })
    
    return templates.TemplateResponse(
        "employees.html",
        {
            "request": request,
            "employees": employees,
            "salary_data": salary_data,
            "total_employees": total_employees,
            "total_to_pay": total_to_pay,
            "total_paid": total_paid,
            "employee_types": employee_types,
            "payment_history": payment_history,
            "current_month": month
        }
    )

# Новый API-эндпоинт для получения списка сотрудников с фильтрацией
@app.get("/api/employees/list", response_class=JSONResponse)
async def get_employees_list(
    employee_type: str = Query(None, alias="type"),
    month: str = Query(None, alias="month"),
    db: Session = Depends(get_db)
):
    # Если месяц не указан, используем текущий
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # Базовый запрос
    query = db.query(Employee).filter(Employee.active == 1).order_by(Employee.name)
    
    # Фильтрация по типу сотрудника
    if employee_type and employee_type != "Все":
        query = query.filter(Employee.employee_type == employee_type)
    
    # Получаем список сотрудников
    employees = query.all()
    
    # Получаем данные о зарплате
    salary_data = await calculate_salary(db, month)
    
    # Формируем список сотрудников
    employees_list = []
    for employee in employees:
        # Подсчет количества заказов
        orders_count = 0
        if employee.employee_type == "менеджер":
            orders_count = db.query(Order).filter(
                Order.manager_id == employee.id,
                Order.order_date.like(f"{month}%"),
                Order.status == "завершен"
            ).count()
        else:
            orders_count = db.query(Order).filter(
                or_(
                    Order.one_employee_id == employee.id,
                    Order.two_employee_id == employee.id
                ),
                Order.order_date.like(f"{month}%"),
                Order.status == "завершен"
            ).count()
        
        # Получаем историю платежей за месяц
        payments = db.query(Payment).filter(
            Payment.employee_id == employee.id,
            Payment.payment_date.like(f"{month}%")
        ).all()
        payment_history = [{
            "id": payment.id,
            "date": payment.payment_date,
            "amount": payment.amount,
            "description": payment.description or ("Штраф" if payment.amount < 0 else "Выплата")
        } for payment in payments]
        
        employees_list.append({
            "id": employee.id,
            "name": employee.name,
            "phone": employee.phone,
            "employee_type": employee.employee_type,
            "base_salary": employee.base_salary or 0,
            "order_rate": employee.order_rate,
            "commission_rate": employee.commission_rate,
            "created_at": employee.created_at,
            "updated_at": employee.updated_at,
            "orders_count": orders_count,
            "salary": salary_data["salary"].get(employee.name, 0),
            "paid": salary_data["paid"].get(employee.name, 0),
            "to_pay": salary_data["salary"].get(employee.name, 0) - salary_data["paid"].get(employee.name, 0),
            "payment_history": payment_history
        })
    
    # Подсчет статистики
    stats = {
        "total_employees": len(employees),
        "total_to_pay": sum(salary_data["salary"].get(emp.name, 0) - salary_data["paid"].get(emp.name, 0) for emp in employees),
        "total_paid": sum(salary_data["paid"].get(emp.name, 0) for emp in employees)
    }
    
    return {
        "employees": employees_list,
        "stats": stats,
        "month": month
    }

# Страница для клиентов с поиском и пагинацией
@app.get("/clients", response_class=HTMLResponse)
async def read_clients(
    request: Request, 
    search: str = "",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source: str = None,
    db: Session = Depends(get_db)
):
    # Базовый запрос
    query = db.query(Client).order_by(desc(Client.created_at))
    
    # Фильтрация по имени или телефону
    if search:
        query = query.filter(
            or_(
                Client.name.ilike(f"%{search}%"),
                Client.phone.ilike(f"%{search}%")
            )
        )
    
    # Фильтрация по источнику
    if source and source != "Все":
        query = query.filter(Client.source == source)
    
    # Получаем общее количество записей
    total_count = query.count()
    
    # Применяем пагинацию
    clients = query.offset((page - 1) * limit).limit(limit).all()
    
    # Подсчет статистики по источникам
    sources = ["Авито", "ВК", "Яндекс услуги", "Листовки", "Рекомендации", "Другое"]
    stats = {}
    for src in sources:
        stats[src] = db.query(Client).filter(Client.source == src).count()
    
    # Статистика заказов по клиентам
    client_ids = [client.id for client in clients]
    client_orders = {}
    
    if client_ids:
        # Получаем количество заказов для каждого клиента
        for client_id in client_ids:
            order_count = db.query(Order).filter(Order.client_id == client_id).count()
            client_orders[client_id] = order_count
    
    # Вычисляем общее количество страниц
    total_pages = (total_count + limit - 1) // limit
    
    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "clients": clients,
            "stats": stats,
            "sources": sources,
            "search": search,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "limit": limit,
            "source_filter": source,
            "client_orders": client_orders
        }
    )

# API-эндпоинт для получения списка клиентов с пагинацией и фильтрацией
@app.get("/api/clients/list", response_class=JSONResponse)
async def get_clients_list(
    search: str = Query("", alias="search"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source: str = Query(None, alias="source"),
    db: Session = Depends(get_db)
):
    # Базовый запрос
    query = db.query(Client).order_by(desc(Client.created_at))
    
    # Фильтрация по имени или телефону
    if search:
        query = query.filter(
            or_(
                Client.name.ilike(f"%{search}%"),
                Client.phone.ilike(f"%{search}%")
            )
        )
    
    # Фильтрация по источнику
    if source and source != "Все":
        query = query.filter(Client.source == source)
    
    # Получаем общее количество записей
    total_count = query.count()
    
    # Применяем пагинацию
    clients = query.offset((page - 1) * limit).limit(limit).all()
    
    # Подсчет количества заказов для каждого клиента
    client_list = []
    for client in clients:
        order_count = db.query(Order).filter(Order.client_id == client.id).count()
        client_list.append({
            "id": client.id,
            "name": client.name,
            "phone": client.phone,
            "source": client.source,
            "created_at": client.created_at,
            "order_count": order_count
        })
    
    # Вычисляем общее количество страниц
    total_pages = (total_count + limit - 1) // limit
    
    # Подсчет статистики по источникам
    sources = ["Авито", "ВК", "Яндекс услуги", "Листовки", "Рекомендации", "Другое"]
    stats = {}
    for src in sources:
        stats[src] = db.query(Client).filter(Client.source == src).count()
    
    return {
        "clients": client_list,
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit,
        "stats": stats
    }

# Страница финансов
@app.get("/finance", response_class=HTMLResponse)
async def read_finance(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        "finance.html",
        {
            "request": request,
            "date_from_filter": date_from,
            "date_to_filter": date_to
        }
    )

# API для расчета зарплаты конкретного сотрудника
@app.get("/api/employees/{employee_id}/salary", response_class=JSONResponse)
async def get_employee_salary(
    employee_id: int = Path(...),
    month: str = None,
    db: Session = Depends(get_db)
):
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    
    salary_data = await calculate_salary(db, month)
    
    if employee.name in salary_data["details"]:
        result = {
            "employee": {
                "id": employee.id,
                "name": employee.name,
                "type": employee.employee_type
            },
            "salary": salary_data["salary"].get(employee.name, 0),
            "paid": salary_data["paid"].get(employee.name, 0),
            "to_pay": salary_data["salary"].get(employee.name, 0) - salary_data["paid"].get(employee.name, 0),
            "details": salary_data["details"].get(employee.name, {}),
            "month": month
        }
        return result
    else:
        raise HTTPException(status_code=404, detail="Данные о зарплате не найдены")

# Страница экспорта
@app.get("/export", response_class=HTMLResponse)
async def read_export(
    request: Request,
    export_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    client_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    client_source: Optional[str] = Query(None),
    service_category: Optional[str] = Query(None),
    employee_type: Optional[str] = Query(None),
    employee_active: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        "export.html",
        {
            "request": request,
            "export_type": export_type,
            "status_filter": status,
            "client_name_filter": client_name,
            "date_from_filter": date_from,
            "date_to_filter": date_to,
            "client_source_filter": client_source,
            "service_category_filter": service_category,
            "employee_type_filter": employee_type,
            "employee_active_filter": employee_active
        }
    )

# API-эндпоинты для создания, обновления и удаления сущностей

# Добавление новой услуги
@app.post("/api/services", response_class=JSONResponse)
async def create_service_api(service: ServiceCreate, db: Session = Depends(get_db)):
    try:
        new_service = Service(
            name=service.name,
            category=service.category,
            material_cost=service.material_cost,
            price=service.price
        )
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        return {"id": new_service.id, "message": "Услуга успешно добавлена", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при добавлении услуги: {str(e)}", "status": "error"}

# Обновление услуги
@app.put("/api/services/{service_id}", response_class=JSONResponse)
async def update_service_api(
    service_id: int, 
    service: ServiceCreate, 
    db: Session = Depends(get_db)
):
    try:
        db_service = db.query(Service).filter(Service.id == service_id).first()
        if not db_service:
            return {"message": "Услуга не найдена", "status": "error"}
        
        db_service.name = service.name
        db_service.category = service.category
        db_service.material_cost = service.material_cost
        db_service.price = service.price
        db_service.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        return {"message": "Услуга успешно обновлена", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при обновлении услуги: {str(e)}", "status": "error"}

# Удаление услуги
@app.delete("/api/services/{service_id}", response_class=JSONResponse)
async def delete_service_api(service_id: int, db: Session = Depends(get_db)):
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return {"message": "Услуга не найдена", "status": "error"}
        
        # Проверяем, используется ли услуга в заказах
        used_in_orders = db.query(Order).filter(Order.service_id == service_id).first()
        used_in_additional = db.query(OrderService).filter(OrderService.service_id == service_id).first()
        
        if used_in_orders or used_in_additional:
            return {"message": "Нельзя удалить услугу, она используется в заказах", "status": "error"}
        
        db.delete(service)
        db.commit()
        return {"message": "Услуга успешно удалена", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при удалении услуги: {str(e)}", "status": "error"}

# Добавление нового сотрудника
@app.post("/api/employees", response_class=JSONResponse)
async def create_employee_api(employee: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        new_employee = Employee(
            name=employee.name,
            phone=employee.phone,
            employee_type=employee.employee_type,
            base_salary=employee.base_salary if employee.employee_type == "менеджер" else None,
            order_rate=employee.order_rate,
            commission_rate=employee.commission_rate
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        return {"id": new_employee.id, "message": "Сотрудник успешно добавлен", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при добавлении сотрудника: {str(e)}", "status": "error"}

# Обновление сотрудника
@app.put("/api/employees/{employee_id}", response_class=JSONResponse)
async def update_employee_api(
    employee_id: int, 
    employee: EmployeeCreate, 
    db: Session = Depends(get_db)
):
    try:
        db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not db_employee:
            return {"message": "Сотрудник не найден", "status": "error"}
        
        db_employee.name = employee.name
        db_employee.phone = employee.phone
        db_employee.employee_type = employee.employee_type
        db_employee.base_salary = employee.base_salary if employee.employee_type == "менеджер" else None
        db_employee.order_rate = employee.order_rate
        db_employee.commission_rate = employee.commission_rate
        db_employee.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        return {"message": "Сотрудник успешно обновлен", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при обновлении сотрудника: {str(e)}", "status": "error"}

# Деактивация сотрудника (вместо удаления)
@app.put("/api/employees/{employee_id}/deactivate", response_class=JSONResponse)
async def deactivate_employee_api(employee_id: int, db: Session = Depends(get_db)):
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"message": "Сотрудник не найден", "status": "error"}
        
        employee.active = 0
        employee.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        return {"message": "Сотрудник деактивирован", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при деактивации сотрудника: {str(e)}", "status": "error"}

# Выплата сотруднику
@app.post("/api/employees/{employee_id}/pay", response_class=JSONResponse)
async def pay_employee_api(
    employee_id: int, 
    amount: float = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"message": "Сотрудник не найден", "status": "error"}
        
        if amount <= 0:
            return {"message": "Сумма выплаты должна быть положительной", "status": "error"}
        
        payment = Payment(
            employee_id=employee_id,
            amount=amount,
            payment_date=datetime.now().strftime("%Y-%m-%d"),
            description=description
        )
        db.add(payment)
        db.commit()
        return {"message": "Выплата успешно произведена", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при выплате: {str(e)}", "status": "error"}

# Штраф сотруднику
@app.post("/api/employees/{employee_id}/fine", response_class=JSONResponse)
async def fine_employee_api(
    employee_id: int, 
    amount: float = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"message": "Сотрудник не найден", "status": "error"}
        
        if amount <= 0:
            return {"message": "Сумма штрафа должна быть положительной", "status": "error"}
        
        payment = Payment(
            employee_id=employee_id,
            amount=-amount,  # Отрицательное значение для штрафа
            payment_date=datetime.now().strftime("%Y-%m-%d"),
            description=description
        )
        db.add(payment)
        db.commit()
        return {"message": "Штраф успешно наложен", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при наложении штрафа: {str(e)}", "status": "error"}

# Добавление нового клиента
@app.post("/api/clients", response_class=JSONResponse)
async def create_client_api(client: ClientCreate, db: Session = Depends(get_db)):
    try:
        # Проверяем, существует ли клиент с таким телефоном
        existing_client = db.query(Client).filter(Client.phone == client.phone).first()
        if existing_client:
            return {"message": "Клиент с таким номером телефона уже существует", "status": "error"}
            
        new_client = Client(
            name=client.name,
            phone=client.phone,
            source=client.source
        )
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        return {"id": new_client.id, "message": "Клиент успешно добавлен", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при добавлении клиента: {str(e)}", "status": "error"}

# Обновление клиента
@app.put("/api/clients/{client_id}", response_class=JSONResponse)
async def update_client_api(
    client_id: int, 
    client: ClientCreate, 
    db: Session = Depends(get_db)
):
    try:
        db_client = db.query(Client).filter(Client.id == client_id).first()
        if not db_client:
            return {"message": "Клиент не найден", "status": "error"}
        
        # Проверяем, существует ли другой клиент с таким телефоном
        existing_client = db.query(Client).filter(
            and_(
                Client.phone == client.phone,
                Client.id != client_id
            )
        ).first()
        if existing_client:
            return {"message": "Другой клиент с таким номером телефона уже существует", "status": "error"}
        
        db_client.name = client.name
        db_client.phone = client.phone
        db_client.source = client.source
        db_client.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        return {"message": "Клиент успешно обновлен", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при обновлении клиента: {str(e)}", "status": "error"}

# Удаление клиента
@app.delete("/api/clients/{client_id}", response_class=JSONResponse)
async def delete_client_api(client_id: int, db: Session = Depends(get_db)):
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {"message": "Клиент не найден", "status": "error"}
        
        # Проверяем, есть ли у клиента заказы
        has_orders = db.query(Order).filter(Order.client_id == client_id).first()
        if has_orders:
            return {"message": "Нельзя удалить клиента с существующими заказами", "status": "error"}
        
        db.delete(client)
        db.commit()
        return {"message": "Клиент успешно удален", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при удалении клиента: {str(e)}", "status": "error"}

async def get_order_details(order_id: int, db: Session):
    """Получить детали заказа с учетом всех связанных данных"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None
        
    # Получаем основную услугу
    main_service = db.query(Service).filter(Service.id == order.service_id).first()
    
    # Получаем дополнительные услуги
    additional_services = []
    order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
    for os in order_services:
        service = db.query(Service).filter(Service.id == os.service_id).first()
        if service:
            additional_services.append({
                "id": service.id,
                "name": service.name,
                "price": service.price,
                "category": service.category
            })
    
    # Получаем исполнителей
    manager = db.query(Employee).filter(Employee.id == order.manager_id).first()
    first_installer = db.query(Employee).filter(Employee.id == order.one_employee_id).first()
    second_installer = None
    if order.two_employee_id:
        second_installer = db.query(Employee).filter(Employee.id == order.two_employee_id).first()
    
    # Получаем клиента
    client = db.query(Client).filter(Client.id == order.client_id).first()
    
    # Рассчитываем общую стоимость заказа
    total_price = main_service.price if main_service else 0
    for service in additional_services:
        total_price += service["price"]
    
    return {
        "id": order.id,
        "status": order.status,
        "order_date": order.order_date,
        "completion_date": order.completion_date,
        "notes": order.notes,
        "client": {
            "id": client.id,
            "name": client.name,
            "phone": client.phone
        } if client else None,
        "main_service": {
            "id": main_service.id,
            "name": main_service.name,
            "price": main_service.price,
            "category": main_service.category
        } if main_service else None,
        "additional_services": additional_services,
        "manager": {
            "id": manager.id,
            "name": manager.name
        } if manager else None,
        "first_installer": {
            "id": first_installer.id,
            "name": first_installer.name
        } if first_installer else None,
        "second_installer": {
            "id": second_installer.id,
            "name": second_installer.name
        } if second_installer else None,
        "total_price": total_price
    }

# API-эндпоинт для создания расхода
# Обновленный эндпоинт для создания расхода (с обновлением баланса)
@app.post("/api/expenses", response_class=JSONResponse)
async def create_expense_api(expense: ExpenseCreate, db: Session = Depends(get_db)):
    try:
        new_expense = Expense(
            category=expense.category,
            amount=expense.amount,
            description=expense.description,
            expense_date=expense.expense_date
        )
        db.add(new_expense)
        
        # Обновляем баланс
        balance = db.query(CompanyBalance).first()
        if balance:
            balance.balance -= expense.amount
            balance.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        db.refresh(new_expense)
        return {"id": new_expense.id, "message": "Расход успешно добавлен", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при добавлении расхода: {str(e)}", "status": "error"}
    
# API-эндпоинт для получения списка расходов
@app.get("/api/expenses", response_class=JSONResponse)
async def get_expenses_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Expense).order_by(desc(Expense.expense_date))
    
    if date_from:
        query = query.filter(Expense.expense_date >= date_from)
    if date_to:
        query = query.filter(Expense.expense_date <= date_to)
    if category:
        query = query.filter(Expense.category == category)
    
    total_count = query.count()
    expenses = query.offset((page - 1) * limit).limit(limit).all()
    
    total_pages = (total_count + limit - 1) // limit
    
    expenses_list = [
        {
            "id": expense.id,
            "category": expense.category,
            "amount": expense.amount,
            "description": expense.description or "-",
            "expense_date": expense.expense_date,
            "created_at": expense.created_at,
            "updated_at": expense.updated_at
        } for expense in expenses
    ]
    
    return {
        "expenses": expenses_list,
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit
    }

# API-эндпоинт для обновления расхода
@app.put("/api/expenses/{expense_id}", response_class=JSONResponse)
async def update_expense_api(
    expense_id: int,
    expense: ExpenseCreate,
    db: Session = Depends(get_db)
):
    try:
        db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not db_expense:
            return {"message": "Расход не найден", "status": "error"}
        
        db_expense.category = expense.category
        db_expense.amount = expense.amount
        db_expense.description = expense.description
        db_expense.expense_date = expense.expense_date
        db_expense.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        return {"message": "Расход успешно обновлен", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при обновлении расхода: {str(e)}", "status": "error"}

# API-эндпоинт для удаления расхода
@app.delete("/api/expenses/{expense_id}", response_class=JSONResponse)
async def delete_expense_api(expense_id: int, db: Session = Depends(get_db)):
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            return {"message": "Расход не найден", "status": "error"}
        
        db.delete(expense)
        db.commit()
        return {"message": "Расход успешно удален", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при удалении расхода: {str(e)}", "status": "error"}

# Страница для заказов с пагинацией и фильтрацией
@app.get("/orders", response_class=HTMLResponse)
async def read_orders(
    request: Request, 
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = None,
    client_name: str = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db)
):
    # Базовый запрос
    query = db.query(Order).order_by(desc(Order.created_at))
    
    # Применяем фильтры
    if status:
        query = query.filter(Order.status == status)
    if client_name:
        query = query.filter(Order.client.has(name=client_name))
    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)
    
    # Получаем общее количество записей
    total_count = query.count()
    
    # Применяем пагинацию
    orders = query.offset((page - 1) * limit).limit(limit).all()
    
    # Получаем дополнительные данные для отображения
    statuses = ["новый", "в работе", "завершен", "отменен"]
    clients = db.query(Client).all()
    services = db.query(Service).all()
    employees = db.query(Employee).filter(Employee.active == 1).all()
    
    # Вычисляем общее количество страниц
    total_pages = (total_count + limit - 1) // limit
    
    # Получаем детали для каждого заказа
    order_details = []
    for order in orders:
        detail = await get_order_details(order.id, db)
        if detail:
            order_details.append(detail)
    
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": order_details,
            "clients": clients,
            "services": services,
            "employees": employees,
            "statuses": statuses,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "limit": limit,
            "status_filter": status,
            "client_name_filter": client_name,
            "date_from_filter": date_from,
            "date_to_filter": date_to
        }
    )

# API-эндпоинт для получения списка заказов с пагинацией и фильтрацией
@app.get("/api/orders/list", response_class=JSONResponse)
async def get_orders_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query(None, alias="status"),
    client_name: str = Query(None, alias="client_name"),
    date_from: str = Query(None, alias="date_from"),
    date_to: str = Query(None, alias="date_to"),
    db: Session = Depends(get_db)
):
    # Базовый запрос
    query = db.query(Order).order_by(desc(Order.created_at))
    
    # Применяем фильтры
    if status:
        query = query.filter(Order.status == status)
    if client_name:
        query = query.filter(Order.client.has(name=client_name))
    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)
    
    # Получаем общее количество записей
    total_count = query.count()
    
    # Применяем пагинацию
    orders = query.offset((page - 1) * limit).limit(limit).all()
    
    # Получаем детали для каждого заказа
    order_details = []
    for order in orders:
        detail = await get_order_details(order.id, db)
        if detail:
            order_details.append(detail)
    
    # Вычисляем общее количество страниц
    total_pages = (total_count + limit - 1) // limit
    
    return {
        "orders": order_details,
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit
    }

# Получение деталей заказа в формате JSON
@app.get("/api/orders/{order_id}", response_class=JSONResponse)
async def get_order_api(order_id: int = Path(...), db: Session = Depends(get_db)):
    order_details = await get_order_details(order_id, db)
    if not order_details:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order_details

# Добавление нового заказа
@app.post("/api/orders", response_class=JSONResponse)
async def create_order_api(order: OrderCreate, db: Session = Depends(get_db)):
    try:
        new_order = Order(
            client_id=order.client_id,
            service_id=order.service_id,
            one_employee_id=order.one_employee_id,
            two_employee_id=order.two_employee_id,
            manager_id=order.manager_id,
            order_date=order.order_date,
            notes=order.notes,
            status="новый"
        )
        db.add(new_order)
        db.flush()  # Получаем ID нового заказа

        # Добавляем дополнительные услуги
        for service_id in order.additional_services:
            order_service = OrderService(order_id=new_order.id, service_id=service_id)
            db.add(order_service)
        
        # Рассчитываем доход от заказа
        main_service = db.query(Service).filter(Service.id == order.service_id).first()
        total_revenue = main_service.price if main_service else 0
        for service_id in order.additional_services:
            additional_service = db.query(Service).filter(Service.id == service_id).first()
            if additional_service:
                total_revenue += additional_service.price
        
        # Обновляем баланс
        balance = db.query(CompanyBalance).first()
        if balance:
            balance.balance += total_revenue
            balance.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        db.refresh(new_order)
        return {"id": new_order.id, "message": "Заказ успешно создан", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при создании заказа: {str(e)}", "status": "error"}
    
# Обновление заказа
@app.put("/api/orders/{order_id}", response_class=JSONResponse)
async def update_order_api(
    order_id: int, 
    order: OrderUpdate, 
    db: Session = Depends(get_db)
):
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return {"message": "Заказ не найден", "status": "error"}

        # Проверяем существование клиента
        client = db.query(Client).filter(Client.id == order.client_id).first()
        if not client:
            return {"message": "Клиент не найден", "status": "error"}

        # Проверяем существование услуги
        service = db.query(Service).filter(Service.id == order.service_id).first()
        if not service:
            return {"message": "Услуга не найдена", "status": "error"}

        # Проверяем существование сотрудников и их активность
        manager = db.query(Employee).filter(Employee.id == order.manager_id, Employee.active == 1).first()
        if not manager or manager.employee_type != "менеджер":
            return {"message": "Менеджер не найден или неактивен", "status": "error"}

        first_installer = db.query(Employee).filter(Employee.id == order.one_employee_id, Employee.active == 1).first()
        if not first_installer or first_installer.employee_type != "монтажник":
            return {"message": "Первый монтажник не найден или неактивен", "status": "error"}

        second_installer = None
        if order.two_employee_id:
            second_installer = db.query(Employee).filter(Employee.id == order.two_employee_id, Employee.active == 1).first()
            if not second_installer or second_installer.employee_type != "монтажник":
                return {"message": "Второй монтажник не найден или неактивен", "status": "error"}

        # Проверяем дополнительные услуги
        for service_id in order.additional_services:
            additional_service = db.query(Service).filter(Service.id == service_id).first()
            if not additional_service:
                return {"message": f"Дополнительная услуга с ID {service_id} не найдена", "status": "error"}

        # Проверяем даты
        try:
            order_date = datetime.strptime(order.order_date, "%Y-%m-%d %H:%M")
            if order.completion_date:
                completion_date = datetime.strptime(order.completion_date, "%Y-%m-%d %H:%M")
                if completion_date < order_date:
                    return {"message": "Дата завершения не может быть раньше даты заказа", "status": "error"}
        except ValueError:
            return {"message": "Неверный формат даты. Используйте YYYY-MM-DD HH:MM", "status": "error"}

        # Обновляем заказ
        db_order.client_id = order.client_id
        db_order.service_id = order.service_id
        db_order.one_employee_id = order.one_employee_id
        db_order.two_employee_id = order.two_employee_id
        db_order.manager_id = order.manager_id
        db_order.order_date = order.order_date
        db_order.completion_date = order.completion_date
        db_order.notes = order.notes
        db_order.status = order.status
        db_order.updated_at = datetime.now().strftime("%Y-%m-%d")

        # Удаляем старые дополнительные услуги
        db.query(OrderService).filter(OrderService.order_id == order_id).delete()

        # Добавляем новые дополнительные услуги
        for service_id in order.additional_services:
            order_service = OrderService(
                order_id=order_id,
                service_id=service_id
            )
            db.add(order_service)

        db.commit()
        return {"message": "Заказ успешно обновлен", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"message": f"Ошибка при обновлении заказа: {str(e)}", "status": "error"}
    
# Обновленный API-эндпоинт для финансовой сводки
@app.get("/api/finance/summary", response_class=JSONResponse)
async def get_finance_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Базовый запрос на заказы
    orders_query = db.query(Order)
    
    # Фильтрация по датам
    if date_from:
        orders_query = orders_query.filter(Order.order_date >= date_from)
    if date_to:
        orders_query = orders_query.filter(Order.order_date <= date_to)
    
    # Получаем заказы
    orders = orders_query.all()
    
    # Рассчитываем доходы
    total_revenue = 0
    for order in orders:
        order_details = await get_order_details(order.id, db)
        total_revenue += order_details["total_price"]
    
    # Рассчитываем расходы на материалы из заказов
    total_material_cost = 0
    for order in orders:
        main_service = db.query(Service).filter(Service.id == order.service_id).first()
        if main_service:
            total_material_cost += main_service.material_cost
        order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
        for os in order_services:
            additional_service = db.query(Service).filter(Service.id == os.service_id).first()
            if additional_service:
                total_material_cost += additional_service.material_cost
    
    # Рассчитываем дополнительные расходы из таблицы expenses
    expenses_query = db.query(Expense)
    if date_from:
        expenses_query = expenses_query.filter(Expense.expense_date >= date_from)
    if date_to:
        expenses_query = expenses_query.filter(Expense.expense_date <= date_to)
    
    total_additional_expenses = sum(expense.amount for expense in expenses_query.all())
    
    # Рассчитываем зарплаты сотрудников
    employees_response = await get_finance_employees(date_from=date_from, date_to=date_to, db=db)
    employees = employees_response.get("employees", [])
    
    # Суммируем общие зарплаты сотрудников
    total_salary = sum(employee["total_salary"] for employee in employees)
    
    # Если есть фильтры по датам, корректируем фиксированную зарплату пропорционально периоду
    if date_from and date_to:
        try:
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.strptime(date_to, "%Y-%m-%d")
            period_days = (end_date - start_date).days + 1
            if period_days <= 0:
                period_days = 1
            
            # Предполагаем, что base_salary — это месячная зарплата
            days_in_month = 30  # Усредненное значение
            period_ratio = period_days / days_in_month
            
            # Пересчитываем фиксированные зарплаты
            total_salary = 0
            for employee in employees:
                base_salary = employee["base_salary"] * period_ratio
                commission = employee["commission"]
                total_salary += base_salary + commission
        except ValueError:
            # Если даты в неправильном формате, оставляем total_salary без изменений
            pass
    
    total_expenses = total_material_cost + total_additional_expenses + total_salary
    profit = total_revenue - total_expenses
    
    # Получаем текущий баланс
    balance_record = db.query(CompanyBalance).first()
    current_balance = balance_record.balance if balance_record else None
    initial_balance_set = bool(balance_record)

    return {
        "total_revenue": round(total_revenue, 2),
        "total_expenses": round(total_expenses, 2),
        "total_material_cost": round(total_material_cost, 2),
        "total_additional_expenses": round(total_additional_expenses, 2),
        "total_salary": round(total_salary, 2),
        "profit": round(profit, 2),
        "current_balance": round(current_balance, 2) if current_balance is not None else None,
        "initial_balance_set": initial_balance_set
    }

# API-эндпоинт для получения финансовых данных по заказам
@app.get("/api/finance/orders", response_class=JSONResponse)
async def get_finance_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Базовый запрос на заказы
    query = db.query(Order).order_by(Order.order_date.desc())
    
    # Фильтрация по датам
    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)
    
    # Получаем общее количество записей
    total_count = query.count()
    
    # Применяем пагинацию
    orders = query.offset((page - 1) * limit).limit(limit).all()
    
    # Получаем детали для каждого заказа
    order_details = []
    for order in orders:
        detail = await get_order_details(order.id, db)
        # Добавляем расходы на материалы
        material_cost = 0
        main_service = db.query(Service).filter(Service.id == order.service_id).first()
        if main_service:
            material_cost += main_service.material_cost
        order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
        for os in order_services:
            additional_service = db.query(Service).filter(Service.id == os.service_id).first()
            if additional_service:
                material_cost += additional_service.material_cost
        detail["material_cost"] = material_cost
        order_details.append(detail)
    
    # Вычисляем общее количество страниц
    total_pages = (total_count + limit - 1) // limit
    
    return {
        "orders": order_details,
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit
    }

# API-эндпоинт для получения данных о зарплатах сотрудников
@app.get("/api/finance/employees", response_class=JSONResponse)
async def get_finance_employees(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    employees = db.query(Employee).filter(Employee.active == 1).all()
    employee_details = []
    
    for employee in employees:
        # Фиксированная зарплата
        base_salary = employee.base_salary or 0
        
        # Комиссии от заказов
        commission = 0
        order_count = 0
        
        # Заказы, где сотрудник был менеджером
        managed_orders = db.query(Order).filter(
            Order.manager_id == employee.id,
            Order.status != "отменен"
        )
        if date_from:
            managed_orders = managed_orders.filter(Order.order_date >= date_from)
        if date_to:
            managed_orders = managed_orders.filter(Order.order_date <= date_to)
        managed_orders = managed_orders.all()
        
        # Заказы, где сотрудник был первым монтажником
        first_installer_orders = db.query(Order).filter(
            Order.one_employee_id == employee.id,
            Order.status != "отменен"
        )
        if date_from:
            first_installer_orders = first_installer_orders.filter(Order.order_date >= date_from)
        if date_to:
            first_installer_orders = first_installer_orders.filter(Order.order_date <= date_to)
        first_installer_orders = first_installer_orders.all()
        
        # Заказы, где сотрудник был вторым монтажником
        second_installer_orders = db.query(Order).filter(
            Order.two_employee_id == employee.id,
            Order.status != "отменен"
        )
        if date_from:
            second_installer_orders = second_installer_orders.filter(Order.order_date >= date_from)
        if date_to:
            second_installer_orders = second_installer_orders.filter(Order.order_date <= date_to)
        second_installer_orders = second_installer_orders.all()
        
        # Рассчитываем комиссии
        if employee.employee_type == "менеджер":
            # Для менеджеров: процент от стоимости заказа
            for order in managed_orders:
                order_details = await get_order_details(order.id, db)
                commission += employee.order_rate
                order_count += 1
        else:
            # Для монтажников: фиксированная ставка за заказ
            for order in first_installer_orders:
                commission += employee.order_rate
                order_count += 1
            for order in second_installer_orders:
                # Убедимся, что не дублируем заказы
                if order not in first_installer_orders:
                    commission += employee.order_rate
                    order_count += 1
        
        total_salary = base_salary + commission
        employee_details.append({
            "id": employee.id,
            "name": employee.name,
            "employee_type": employee.employee_type,
            "base_salary": base_salary,
            "commission": round(commission, 2),
            "total_salary": round(total_salary, 2),
            "order_count": order_count
        })
    
    return {"employees": employee_details}

# Вспомогательная функция для расчета финансов сотрудника за период
async def calculate_employee_earnings(employee, date_from: Optional[str], date_to: Optional[str], db: Session):
    # Фиксированная зарплата
    base_salary = employee.base_salary or 0
    
    # Корректируем фиксированную зарплату пропорционально периоду
    if date_from and date_to:
        try:
            start_date = datetime.strptime(date_from, "%Y-%m-%d")
            end_date = datetime.strptime(date_to, "%Y-%m-%d")
            period_days = (end_date - start_date).days + 1
            if period_days <= 0:
                period_days = 1
            days_in_month = 30  # Усредненное значение
            period_ratio = period_days / days_in_month
            base_salary = base_salary * period_ratio
        except ValueError:
            pass
    
    # Комиссии от заказов
    commission = 0
    order_count = 0
    
    # Заказы, где сотрудник был менеджером
    managed_orders = db.query(Order).filter(
        Order.manager_id == employee.id,
        Order.status != "отменен"
    )
    if date_from:
        managed_orders = managed_orders.filter(Order.order_date >= date_from)
    if date_to:
        managed_orders = managed_orders.filter(Order.order_date <= date_to)
    managed_orders = managed_orders.all()
    
    # Заказы, где сотрудник был первым монтажником
    first_installer_orders = db.query(Order).filter(
        Order.one_employee_id == employee.id,
        Order.status != "отменен"
    )
    if date_from:
        first_installer_orders = first_installer_orders.filter(Order.order_date >= date_from)
    if date_to:
        first_installer_orders = first_installer_orders.filter(Order.order_date <= date_to)
    first_installer_orders = first_installer_orders.all()
    
    # Заказы, где сотрудник был вторым монтажником
    second_installer_orders = db.query(Order).filter(
        Order.two_employee_id == employee.id,
        Order.status != "отменен"
    )
    if date_from:
        second_installer_orders = second_installer_orders.filter(Order.order_date >= date_from)
    if date_to:
        second_installer_orders = second_installer_orders.filter(Order.order_date <= date_to)
    second_installer_orders = second_installer_orders.all()
    
    # Рассчитываем комиссии
    if employee.employee_type == "менеджер":
        for order in managed_orders:
            order_details = await get_order_details(order.id, db)
            commission += order_details["total_price"] * (employee.commission_rate / 100)
            order_count += 1
    else:
        for order in first_installer_orders:
            commission += employee.order_rate
            order_count += 1
        for order in second_installer_orders:
            if order not in first_installer_orders:
                commission += employee.order_rate
                order_count += 1
    
    total_earned = base_salary + commission
    paid_amount = employee.paid_amount or 0  # Предполагаем, что это поле есть в модели
    remaining_to_pay = total_earned - paid_amount
    
    return {
        "total_earned": round(total_earned, 2),
        "paid_amount": round(paid_amount, 2),
        "remaining_to_pay": round(remaining_to_pay, 2),
        "order_count": order_count
    }

# API-эндпоинт для предпросмотра данных
@app.get("/api/export/preview", response_class=JSONResponse)
async def preview_data(
    export_type: str = Query(..., description="Тип данных для экспорта: orders, clients, services, employees"),
    status: Optional[str] = Query(None),
    client_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    client_source: Optional[str] = Query(None),
    service_category: Optional[str] = Query(None),
    employee_type: Optional[str] = Query(None),
    employee_active: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    if export_type == "orders":
        query = db.query(Order).order_by(Order.order_date.desc())
        if status:
            query = query.filter(Order.status == status)
        if client_name:
            query = query.filter(Order.client.has(name=client_name))
        if date_from:
            query = query.filter(Order.order_date >= date_from)
        if date_to:
            query = query.filter(Order.order_date <= date_to)
        
        orders = query.all()
        order_details = []
        for order in orders:
            detail = await get_order_details(order.id, db)
            order_details.append(detail)
        
        return {"orders": order_details}

    elif export_type == "clients":
        query = db.query(Client).order_by(Client.name)
        if client_name:
            query = query.filter(Client.name.ilike(f"%{client_name}%"))
        if client_source:
            query = query.filter(Client.source == client_source)
        
        clients = query.all()
        return {"clients": [client.__dict__ for client in clients]}

    elif export_type == "services":
        query = db.query(Service).order_by(Service.name)
        if service_category:
            query = query.filter(Service.category == service_category)
        
        services = query.all()
        return {"services": [service.__dict__ for service in services]}

    elif export_type == "employees":
        query = db.query(Employee).order_by(Employee.name)
        if employee_type:
            query = query.filter(Employee.employee_type == employee_type)
        if employee_active is not None:
            query = query.filter(Employee.active == employee_active)
        
        employees = query.all()
        employee_details = []
        for employee in employees:
            earnings = await calculate_employee_earnings(employee, date_from, date_to, db)
            employee_dict = employee.__dict__
            employee_dict.update(earnings)
            employee_details.append(employee_dict)
        
        return {"employees": employee_details}

    else:
        raise HTTPException(status_code=400, detail="Неверный тип экспорта. Допустимые значения: orders, clients, services, employees")

# API-эндпоинт для экспорта данных
@app.get("/api/export")
async def export_data(
    export_type: str = Query(..., description="Тип данных для экспорта: orders, clients, services, employees"),
    format: str = Query("csv", description="Формат экспорта: csv или xlsx"),
    status: Optional[str] = Query(None),
    client_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    client_source: Optional[str] = Query(None),
    service_category: Optional[str] = Query(None),
    employee_type: Optional[str] = Query(None),
    employee_active: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    # Формируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_{export_type}_{timestamp}.{format}"

    if format == "csv":
        # Экспорт в CSV
        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')

        if export_type == "orders":
            query = db.query(Order).order_by(Order.order_date.desc())
            if status:
                query = query.filter(Order.status == status)
            if client_name:
                query = query.filter(Order.client.has(name=client_name))
            if date_from:
                query = query.filter(Order.order_date >= date_from)
            if date_to:
                query = query.filter(Order.order_date <= date_to)
            
            orders = query.all()
            order_details = []
            for order in orders:
                detail = await get_order_details(order.id, db)
                order_details.append(detail)
            
            headers = [
                "ID", "Клиент", "Основная услуга", "Дополнительные услуги", "Сумма (₽)",
                "Менеджер", "Первый монтажник", "Второй монтажник", "Дата заказа",
                "Дата завершения", "Статус", "Примечания"
            ]
            writer.writerow(headers)
            
            for order in order_details:
                additional_services = ", ".join([s["name"] for s in order["additional_services"]]) if order["additional_services"] else "-"
                row = [
                    order["id"],
                    order["client"]["name"] if order["client"] else "-",
                    order["main_service"]["name"] if order["main_service"] else "-",
                    additional_services,
                    order["total_price"],
                    order["manager"]["name"] if order["manager"] else "-",
                    order["first_installer"]["name"] if order["first_installer"] else "-",
                    order["second_installer"]["name"] if order["second_installer"] else "-",
                    order["order_date"] if order["order_date"] else "-",
                    order["completion_date"] if order["completion_date"] else "-",
                    order["status"],
                    order["notes"] if order["notes"] else "-"
                ]
                writer.writerow(row)

        elif export_type == "clients":
            query = db.query(Client).order_by(Client.name)
            if client_name:
                query = query.filter(Client.name.ilike(f"%{client_name}%"))
            if client_source:
                query = query.filter(Client.source == client_source)
            
            clients = query.all()
            headers = ["ID", "Имя", "Телефон", "Источник", "Дата создания", "Дата обновления"]
            writer.writerow(headers)
            
            for client in clients:
                row = [
                    client.id,
                    client.name,
                    client.phone,
                    client.source,
                    client.created_at,
                    client.updated_at if client.updated_at else "-"
                ]
                writer.writerow(row)

        elif export_type == "services":
            query = db.query(Service).order_by(Service.name)
            if service_category:
                query = query.filter(Service.category == service_category)
            
            services = query.all()
            headers = ["ID", "Название", "Категория", "Стоимость материалов (₽)", "Цена (₽)", "Дата создания", "Дата обновления"]
            writer.writerow(headers)
            
            for service in services:
                row = [
                    service.id,
                    service.name,
                    service.category,
                    service.material_cost,
                    service.price,
                    service.created_at,
                    service.updated_at if service.updated_at else "-"
                ]
                writer.writerow(row)

        elif export_type == "employees":
            query = db.query(Employee).order_by(Employee.name)
            if employee_type:
                query = query.filter(Employee.employee_type == employee_type)
            if employee_active is not None:
                query = query.filter(Employee.active == employee_active)
            
            employees = query.all()
            headers = [
                "ID", "Имя", "Телефон", "Тип сотрудника", "Базовая зарплата (₽)",
                "Ставка за заказ", "Комиссия (%)", "Активен", "Заработано за период (₽)",
                "Выплачено (₽)", "Осталось выплатить (₽)", "Количество заказов",
                "Дата создания", "Дата обновления"
            ]
            writer.writerow(headers)
            
            for employee in employees:
                earnings = await calculate_employee_earnings(employee, date_from, date_to, db)
                row = [
                    employee.id,
                    employee.name,
                    employee.phone,
                    employee.employee_type,
                    employee.base_salary if employee.base_salary else 0,
                    employee.order_rate,
                    employee.commission_rate,
                    "Да" if employee.active == 1 else "Нет",
                    earnings["total_earned"],
                    earnings["paid_amount"],
                    earnings["remaining_to_pay"],
                    earnings["order_count"],
                    employee.created_at,
                    employee.updated_at if employee.updated_at else "-"
                ]
                writer.writerow(row)

        else:
            raise HTTPException(status_code=400, detail="Неверный тип экспорта. Допустимые значения: orders, clients, services, employees")

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    elif format == "xlsx":
        # Экспорт в Excel
        workbook = openpyxl.Workbook()
        sheet = workbook.active

        if export_type == "orders":
            sheet.title = "Заказы"
            headers = [
                "ID", "Клиент", "Основная услуга", "Дополнительные услуги", "Сумма (₽)",
                "Менеджер", "Первый монтажник", "Второй монтажник", "Дата заказа",
                "Дата завершения", "Статус", "Примечания"
            ]
            sheet.append(headers)
            for cell in sheet[1]:
                cell.font = Font(bold=True)

            query = db.query(Order).order_by(Order.order_date.desc())
            if status:
                query = query.filter(Order.status == status)
            if client_name:
                query = query.filter(Order.client.has(name=client_name))
            if date_from:
                query = query.filter(Order.order_date >= date_from)
            if date_to:
                query = query.filter(Order.order_date <= date_to)
            
            orders = query.all()
            order_details = []
            for order in orders:
                detail = await get_order_details(order.id, db)
                order_details.append(detail)
            
            for order in order_details:
                additional_services = ", ".join([s["name"] for s in order["additional_services"]]) if order["additional_services"] else "-"
                row = [
                    order["id"],
                    order["client"]["name"] if order["client"] else "-",
                    order["main_service"]["name"] if order["main_service"] else "-",
                    additional_services,
                    order["total_price"],
                    order["manager"]["name"] if order["manager"] else "-",
                    order["first_installer"]["name"] if order["first_installer"] else "-",
                    order["second_installer"]["name"] if order["second_installer"] else "-",
                    order["order_date"] if order["order_date"] else "-",
                    order["completion_date"] if order["completion_date"] else "-",
                    order["status"],
                    order["notes"] if order["notes"] else "-"
                ]
                sheet.append(row)

        elif export_type == "clients":
            sheet.title = "Клиенты"
            headers = ["ID", "Имя", "Телефон", "Источник", "Дата создания", "Дата обновления"]
            sheet.append(headers)
            for cell in sheet[1]:
                cell.font = Font(bold=True)

            query = db.query(Client).order_by(Client.name)
            if client_name:
                query = query.filter(Client.name.ilike(f"%{client_name}%"))
            if client_source:
                query = query.filter(Client.source == client_source)
            
            clients = query.all()
            for client in clients:
                row = [
                    client.id,
                    client.name,
                    client.phone,
                    client.source,
                    client.created_at,
                    client.updated_at if client.updated_at else "-"
                ]
                sheet.append(row)

        elif export_type == "services":
            sheet.title = "Услуги"
            headers = ["ID", "Название", "Категория", "Стоимость материалов (₽)", "Цена (₽)", "Дата создания", "Дата обновления"]
            sheet.append(headers)
            for cell in sheet[1]:
                cell.font = Font(bold=True)

            query = db.query(Service).order_by(Service.name)
            if service_category:
                query = query.filter(Service.category == service_category)
            
            services = query.all()
            for service in services:
                row = [
                    service.id,
                    service.name,
                    service.category,
                    service.material_cost,
                    service.price,
                    service.created_at,
                    service.updated_at if service.updated_at else "-"
                ]
                sheet.append(row)

        elif export_type == "employees":
            sheet.title = "Сотрудники"
            headers = [
                "ID", "Имя", "Телефон", "Тип сотрудника", "Базовая зарплата (₽)",
                "Ставка за заказ", "Комиссия (%)", "Активен", "Заработано за период (₽)",
                "Выплачено (₽)", "Осталось выплатить (₽)", "Количество заказов",
                "Дата создания", "Дата обновления"
            ]
            sheet.append(headers)
            for cell in sheet[1]:
                cell.font = Font(bold=True)

            query = db.query(Employee).order_by(Employee.name)
            if employee_type:
                query = query.filter(Employee.employee_type == employee_type)
            if employee_active is not None:
                query = query.filter(Employee.active == employee_active)
            
            employees = query.all()
            for employee in employees:
                earnings = await calculate_employee_earnings(employee, date_from, date_to, db)
                row = [
                    employee.id,
                    employee.name,
                    employee.phone,
                    employee.employee_type,
                    employee.base_salary if employee.base_salary else 0,
                    employee.order_rate,
                    employee.commission_rate,
                    "Да" if employee.active == 1 else "Нет",
                    earnings["total_earned"],
                    earnings["paid_amount"],
                    earnings["remaining_to_pay"],
                    earnings["order_count"],
                    employee.created_at,
                    employee.updated_at if employee.updated_at else "-"
                ]
                sheet.append(row)

        else:
            raise HTTPException(status_code=400, detail="Неверный тип экспорта. Допустимые значения: orders, clients, services, employees")

        # Сохраняем Excel в поток
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    else:
        raise HTTPException(status_code=400, detail="Неверный формат экспорта. Допустимые значения: csv, xlsx")