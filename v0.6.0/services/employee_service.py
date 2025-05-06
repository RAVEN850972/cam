"""
Сервис для работы с сотрудниками.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from models import Employee, Order, OrderService, OrderEmployee, Payment, Service
from schemas import EmployeeCreate, EmployeeUpdate
from config import MANAGER_BASE_SALARY, MANAGER_ORDER_COMMISSION, DEFAULT_MOUNT_PRICE, MANAGER_MOUNT_UPSELL_PERCENT
from config import MANAGER_CONDITIONER_COMMISSION_PERCENT, MANAGER_ADDON_COMMISSION_PERCENT
from config import INSTALLER_BASE_PAYMENT, DEFAULT_MOUNT_PRICE_7_9, DEFAULT_MOUNT_PRICE_12_18

class EmployeeService:
    """
    Сервис для работы с сотрудниками.
    """
    
    @staticmethod
    def get_employees(
        db: Session, 
        employee_type: Optional[str] = None,
        active: Optional[int] = None,
        page: int = 1,
        limit: int = 20
    ):
        """
        Получение списка сотрудников с фильтрацией и пагинацией.
        """
        query = db.query(Employee)
        
        if employee_type:
            query = query.filter(Employee.employee_type == employee_type)
        
        if active is not None:
            query = query.filter(Employee.active == active)
        
        query = query.order_by(Employee.name)
        
        # Получаем общее количество записей
        total_count = query.count()
        
        # Применяем пагинацию
        employees = query.offset((page - 1) * limit).limit(limit).all()
        
        # Преобразуем в словари для правильной сериализации
        employees_dict = []
        for emp in employees:
            employees_dict.append({
                "id": emp.id,
                "name": emp.name,
                "phone": emp.phone,
                "employee_type": emp.employee_type,
                "base_salary": emp.base_salary,
                "active": emp.active,
                "created_at": emp.created_at,
                "updated_at": emp.updated_at
            })
        
        # Общее количество страниц
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "employees": employees_dict,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "limit": limit
        }
    
    @staticmethod
    def get_employee(db: Session, employee_id: int):
        """
        Получение сотрудника по ID.
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return None
        
        # Преобразуем в словарь для правильной сериализации
        return {
            "id": employee.id,
            "name": employee.name,
            "phone": employee.phone,
            "employee_type": employee.employee_type,
            "base_salary": employee.base_salary,
            "active": employee.active,
            "created_at": employee.created_at,
            "updated_at": employee.updated_at
        }
    
    @staticmethod
    def create_employee(db: Session, employee_data: EmployeeCreate):
        """
        Создание нового сотрудника.
        """
        base_salary = None
        
        # Для менеджера устанавливаем базовую зарплату
        if employee_data.employee_type == "менеджер":
            base_salary = employee_data.base_salary if employee_data.base_salary is not None else MANAGER_BASE_SALARY
        
        # Создаем нового сотрудника
        employee = Employee(
            name=employee_data.name,
            phone=employee_data.phone,
            employee_type=employee_data.employee_type,
            base_salary=base_salary,
            active=1
        )
        
        try:
            db.add(employee)
            db.commit()
            db.refresh(employee)
            
            # Возвращаем словарь вместо объекта модели
            return {
                "id": employee.id,
                "name": employee.name,
                "phone": employee.phone,
                "employee_type": employee.employee_type,
                "base_salary": employee.base_salary,
                "active": employee.active,
                "created_at": employee.created_at,
                "updated_at": employee.updated_at
            }
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def update_employee(db: Session, employee_id: int, employee_data: EmployeeUpdate):
        """
        Обновление данных сотрудника.
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not employee:
            return None
        
        # Обновляем имя
        if employee_data.name is not None:
            employee.name = employee_data.name
        
        # Обновляем телефон
        if employee_data.phone is not None:
            employee.phone = employee_data.phone
        
        # Обновляем тип сотрудника
        if employee_data.employee_type is not None:
            employee.employee_type = employee_data.employee_type
            
            # Если тип изменился на "менеджер", устанавливаем базовую зарплату
            if employee_data.employee_type == "менеджер":
                employee.base_salary = employee_data.base_salary if employee_data.base_salary is not None else MANAGER_BASE_SALARY
            else:
                employee.base_salary = None
        elif employee.employee_type == "менеджер" and employee_data.base_salary is not None:
            # Если тип не изменился, но изменилась базовая зарплата для менеджера
            employee.base_salary = employee_data.base_salary
        
        # Обновляем статус активности
        if employee_data.active is not None:
            employee.active = employee_data.active
        
        # Обновляем дату обновления
        employee.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        try:
            db.commit()
            db.refresh(employee)
            
            # Возвращаем словарь вместо объекта модели
            return {
                "id": employee.id,
                "name": employee.name,
                "phone": employee.phone,
                "employee_type": employee.employee_type,
                "base_salary": employee.base_salary,
                "active": employee.active,
                "created_at": employee.created_at,
                "updated_at": employee.updated_at
            }
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def deactivate_employee(db: Session, employee_id: int):
        """
        Деактивация сотрудника (вместо удаления).
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not employee:
            return None
        
        employee.active = 0
        employee.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        try:
            db.commit()
            db.refresh(employee)
            
            # Возвращаем словарь вместо объекта модели
            return {
                "id": employee.id,
                "name": employee.name,
                "phone": employee.phone,
                "employee_type": employee.employee_type,
                "base_salary": employee.base_salary,
                "active": employee.active,
                "created_at": employee.created_at,
                "updated_at": employee.updated_at
            }
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def calculate_salary(db: Session, employee_id: int, month: Optional[str] = None):
        """
        Расчет зарплаты сотрудника за указанный месяц.
        """
        # Если месяц не указан, используем текущий
        if not month:
            month = datetime.now().strftime("%Y-%m")
        
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not employee:
            return None
        
        # Инициализация результата
        result = {
            "employee": {
                "id": employee.id,
                "name": employee.name,
                "type": employee.employee_type
            },
            "salary": 0,
            "paid": 0,
            "to_pay": 0,
            "details": {
                "base_salary": 0,
                "order_payments": 0,
                "additional_commission": 0,
                "ac_commission": 0,
                "breakdown": {
                    "orders": [],
                    "payments": []
                }
            },
            "month": month
        }
        
        # Базовая ставка для менеджеров
        if employee.employee_type == "менеджер" and employee.base_salary:
            result["salary"] += employee.base_salary
            result["details"]["base_salary"] = employee.base_salary
        
        # Получаем все завершенные заказы за месяц
        orders_query = db.query(Order).filter(
            Order.order_date.like(f"{month}%"),
            Order.status == "завершен"
        )
        
        # Расчет для менеджера
        if employee.employee_type == "менеджер":
            manager_orders = orders_query.filter(Order.manager_id == employee_id).all()
            
            for order in manager_orders:
                order_data = {
                    "id": order.id,
                    "date": order.order_date,
                    "amount": MANAGER_ORDER_COMMISSION,
                    "type": "Менеджер - фиксированная ставка"
                }
                
                # Фиксированная ставка за заказ
                result["salary"] += MANAGER_ORDER_COMMISSION
                result["details"]["order_payments"] += MANAGER_ORDER_COMMISSION
                
                # Получаем все услуги заказа, чтобы определить тип кондиционера
                order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
                
                # Определяем стандартную стоимость монтажа в зависимости от типа кондиционера
                standard_mount_price = DEFAULT_MOUNT_PRICE_7_9  # По умолчанию для 7 и 9 БТЮ
                ac_power = None
                
                for os in order_services:
                    service = db.query(Service).filter(Service.id == os.service_id).first()
                    if service and service.category == "Кондиционер":
                        if service.power_type in ["12 БТЮ", "18 БТЮ"]:
                            standard_mount_price = DEFAULT_MOUNT_PRICE_12_18
                            ac_power = service.power_type
                        else:
                            ac_power = service.power_type
                
                # 30% от завышения цены монтажа (с учетом типа кондиционера)
                if order.mount_price > standard_mount_price:
                    mount_bonus = (order.mount_price - standard_mount_price) * MANAGER_MOUNT_UPSELL_PERCENT
                    result["salary"] += mount_bonus
                    result["details"]["additional_commission"] += mount_bonus
                    
                    order_data["amount"] += mount_bonus
                    order_data["type"] += f", Повышение цены монтажа ({ac_power if ac_power else 'стандарт'}): {mount_bonus:.2f}"
                
                # Получаем все услуги заказа
                for os in order_services:
                    service = db.query(Service).filter(Service.id == os.service_id).first()
                    
                    if service:
                        profit = os.selling_price - (service.purchase_price or 0)
                        
                        if service.category == "Кондиционер":
                            # 20% от прибыли с продажи кондиционера
                            commission = profit * MANAGER_CONDITIONER_COMMISSION_PERCENT
                            result["salary"] += commission
                            result["details"]["ac_commission"] += commission
                            
                            order_data["amount"] += commission
                            order_data["type"] += f", Комиссия с кондиционера: {commission:.2f}"
                        
                        elif service.is_manager_bonus:
                            # 30% от прибыли с доп. услуг (монтажный комплект, виброопоры)
                            commission = profit * MANAGER_ADDON_COMMISSION_PERCENT
                            result["salary"] += commission
                            result["details"]["additional_commission"] += commission
                            
                            order_data["amount"] += commission
                            order_data["type"] += f", Комиссия с доп. услуг: {commission:.2f}"
                
                result["details"]["breakdown"]["orders"].append(order_data)
        
        # Расчет для монтажника
        elif employee.employee_type == "монтажник":
            # Получаем заказы, где сотрудник был монтажником
            installer_orders_query = db.query(OrderEmployee).filter(
                OrderEmployee.employee_id == employee_id,
                OrderEmployee.employee_type == "монтажник"
            ).join(Order).filter(
                Order.order_date.like(f"{month}%"),
                Order.status == "завершен"
            )
            
            installer_orders = installer_orders_query.all()
            
            for order_emp in installer_orders:
                order = db.query(Order).filter(Order.id == order_emp.order_id).first()
                
                if order:
                    # Убедимся, что мы используем правильную сумму - 1500
                    base_payment = 1500  # Фиксированная оплата 1500 рублей за монтаж
                    
                    order_data = {
                        "id": order.id,
                        "date": order.order_date,
                        "amount": base_payment,
                        "type": "Монтажник - фиксированная ставка"
                    }
                    
                    # Фиксированная ставка за монтаж
                    result["salary"] += base_payment
                    result["details"]["order_payments"] += base_payment
                    
                    # Получаем услуги, проданные монтажником
                    services_sold = db.query(OrderService).filter(
                        OrderService.order_id == order.id,
                        OrderService.sold_by_id == employee_id
                    ).all()
                    
                    for os in services_sold:
                        service = db.query(Service).filter(Service.id == os.service_id).first()
                        
                        if service and not service.is_manager_bonus:
                            # Фиксированная оплата за продажу услуги - 250 рублей
                            commission = 250  # Бонус монтажнику за дополнительную услугу
                            result["salary"] += commission
                            result["details"]["additional_commission"] += commission
                            
                            order_data["amount"] += commission
                            order_data["type"] += f", Бонус за доп. услугу: {commission:.2f}"
                    
                    result["details"]["breakdown"]["orders"].append(order_data)
        
        # Расчет для владельца
        elif employee.employee_type == "владелец":
            # Находим все заказы за месяц
            owner_orders = orders_query.all()
            
            for order in owner_orders:
                # 1500 за каждый монтаж
                order_data = {
                    "id": order.id,
                    "date": order.order_date,
                    "amount": order.owner_commission,
                    "type": "Владелец - комиссия за монтаж"
                }
                
                result["salary"] += order.owner_commission
                result["details"]["order_payments"] += order.owner_commission
                
                result["details"]["breakdown"]["orders"].append(order_data)
        
        # Учитываем выплаты и штрафы
        payments_query = db.query(Payment).filter(
            Payment.employee_id == employee_id,
            Payment.payment_date.like(f"{month}%")
        )
        
        for payment in payments_query.all():
            result["paid"] += payment.amount
            
            result["details"]["breakdown"]["payments"].append({
                "id": payment.id,
                "date": payment.payment_date,
                "amount": payment.amount,
                "description": payment.description or ("Штраф" if payment.amount < 0 else "Выплата")
            })
        
        # Осталось выплатить
        result["to_pay"] = result["salary"] - result["paid"]
        
        return result
    
    @staticmethod
    def add_payment(db: Session, employee_id: int, amount: float, description: Optional[str] = None):
        """
        Добавление выплаты сотруднику.
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        if not employee:
            return {"error": "Сотрудник не найден"}
        
        payment = Payment(
            employee_id=employee_id,
            amount=amount,
            payment_date=datetime.now().strftime("%Y-%m-%d"),
            description=description
        )
        
        try:
            db.add(payment)
            db.flush()
            
            # Если это выплата (не штраф), обновляем баланс компании
            if amount > 0:
                from services.finance_service import FinanceService
                result = FinanceService.update_company_balance_on_payment(db, payment.id)
                
                if "error" in result:
                    db.rollback()
                    return {"error": result["error"]}
            
            db.commit()
            db.refresh(payment)
            
            return {"success": True, "id": payment.id}
        except Exception as e:
            db.rollback()
            return {"error": str(e)}