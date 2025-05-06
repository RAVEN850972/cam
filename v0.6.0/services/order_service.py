"""
Сервис для работы с заказами.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import Order, OrderService as OrderServiceModel, OrderEmployee, Employee
from models import Client, Service
from schemas import OrderCreate, OrderUpdate

from services.finance_service import FinanceService
from config import MANAGER_ORDER_COMMISSION, DEFAULT_MOUNT_PRICE, MANAGER_MOUNT_UPSELL_PERCENT
from config import MANAGER_CONDITIONER_COMMISSION_PERCENT, MANAGER_ADDON_COMMISSION_PERCENT
from config import INSTALLER_BASE_PAYMENT, OWNER_MOUNT_COMMISSION, DEFAULT_MOUNT_PRICE_7_9, DEFAULT_MOUNT_PRICE_12_18

class OrderService:
    """
    Сервис для работы с заказами.
    """
    
    @staticmethod
    def get_orders(
        db: Session, 
        status: Optional[str] = None,
        client_name: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ):
        """
        Получение списка заказов с фильтрацией и пагинацией.
        """
        query = db.query(Order).order_by(desc(Order.created_at))
        
        if status:
            query = query.filter(Order.status == status)
        
        if client_name:
            query = query.join(Client).filter(Client.name.ilike(f"%{client_name}%"))
        
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
            detail = OrderService.get_order_details(db, order.id)
            order_details.append(detail)
        
        # Общее количество страниц
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "orders": order_details,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "limit": limit
        }
    
    @staticmethod
    def get_order_details(db: Session, order_id: int):
        """
        Получение детальной информации о заказе.
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        
        # Получаем клиента
        client = db.query(Client).filter(Client.id == order.client_id).first()
        
        # Получаем менеджера
        manager = db.query(Employee).filter(Employee.id == order.manager_id).first()
        
        # Получаем монтажников
        employees = db.query(OrderEmployee).filter(OrderEmployee.order_id == order.id).all()
        employees_data = []
        
        for emp in employees:
            employee = db.query(Employee).filter(Employee.id == emp.employee_id).first()
            if employee:
                employees_data.append({
                    "id": employee.id,
                    "name": employee.name,
                    "employee_type": emp.employee_type,
                    "base_payment": emp.base_payment
                })
        
        # Получаем услуги заказа
        services_query = db.query(OrderServiceModel).filter(OrderServiceModel.order_id == order.id)
        services = services_query.all()
        services_data = []
        
        total_price = order.mount_price  # Начинаем с цены монтажа
        
        for svc in services:
            service = db.query(Service).filter(Service.id == svc.service_id).first()
            sold_by = None
            if svc.sold_by_id:
                sold_by_emp = db.query(Employee).filter(Employee.id == svc.sold_by_id).first()
                if sold_by_emp:
                    sold_by = {
                        "id": sold_by_emp.id,
                        "name": sold_by_emp.name
                    }
            
            if service:
                services_data.append({
                    "id": service.id,
                    "name": service.name,
                    "category": service.category,
                    "selling_price": svc.selling_price,
                    "is_manager_bonus": service.is_manager_bonus,
                    "sold_by": sold_by
                })
                
                # Добавляем к общей стоимости
                total_price += svc.selling_price
        
        return {
            "id": order.id,
            "client": {
                "id": client.id,
                "name": client.name,
                "phone": client.phone
            } if client else None,
            "manager": {
                "id": manager.id,
                "name": manager.name
            } if manager else None,
            "order_date": order.order_date,
            "completion_date": order.completion_date,
            "status": order.status,
            "notes": order.notes,
            "mount_price": order.mount_price,
            "owner_commission": order.owner_commission,
            "employees": employees_data,
            "services": services_data,
            "total_price": total_price,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        }
    
    @staticmethod
    def create_order(db: Session, order_data: OrderCreate):
        """
        Создание нового заказа.
        """
        # Проверяем существование клиента
        client = db.query(Client).filter(Client.id == order_data.client_id).first()
        if not client:
            return {"error": "Клиент не найден"}
        
        # Проверяем существование менеджера
        manager = db.query(Employee).filter(
            Employee.id == order_data.manager_id,
            Employee.employee_type == "менеджер",
            Employee.active == 1
        ).first()
        if not manager:
            return {"error": "Менеджер не найден или неактивен"}
        
        # Создаем новый заказ
        new_order = Order(
            client_id=order_data.client_id,
            manager_id=order_data.manager_id,
            order_date=order_data.order_date,
            notes=order_data.notes,
            status=order_data.status if order_data.status else "новый",
            mount_price=order_data.mount_price if order_data.mount_price else DEFAULT_MOUNT_PRICE,
            owner_commission=OWNER_MOUNT_COMMISSION
        )
        db.add(new_order)
        db.flush()
        
        # Добавляем услуги
        for service_data in order_data.services:
            service = db.query(Service).filter(Service.id == service_data.service_id).first()
            if not service:
                db.rollback()
                return {"error": f"Услуга с ID {service_data.service_id} не найдена"}
            
            # Если цена продажи не указана, берем из услуги
            selling_price = service_data.selling_price if service_data.selling_price else service.selling_price
            
            order_service = OrderServiceModel(
                order_id=new_order.id,
                service_id=service_data.service_id,
                selling_price=selling_price,
                sold_by_id=service_data.sold_by_id
            )
            db.add(order_service)
        
        # Добавляем сотрудников (если указаны)
        for employee_data in order_data.employees:
            employee = db.query(Employee).filter(
                Employee.id == employee_data.employee_id,
                Employee.active == 1
            ).first()
            if not employee:
                db.rollback()
                return {"error": f"Сотрудник с ID {employee_data.employee_id} не найден или неактивен"}
            
            # Проверяем тип сотрудника (для монтажников)
            if employee_data.employee_type == "монтажник" and employee.employee_type != "монтажник":
                db.rollback()
                return {"error": f"Сотрудник с ID {employee_data.employee_id} не является монтажником"}
            
            # Проверяем тип сотрудника (для владельца)
            if employee_data.employee_type == "владелец_на_монтаже" and employee.employee_type != "владелец":
                db.rollback()
                return {"error": f"Сотрудник с ID {employee_data.employee_id} не является владельцем"}
            
            order_employee = OrderEmployee(
                order_id=new_order.id,
                employee_id=employee_data.employee_id,
                employee_type=employee_data.employee_type,
                base_payment=employee_data.base_payment if employee_data.base_payment else INSTALLER_BASE_PAYMENT
            )
            db.add(order_employee)
        
        # Если заказ уже отмечен как "завершен", обновляем дату завершения
        if order_data.status == "завершен" and not order_data.completion_date:
            new_order.completion_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        try:
            db.flush()
            
            # Обновляем баланс компании
            result = FinanceService.update_company_balance_on_order_creation(db, new_order.id)
            if "error" in result:
                db.rollback()
                return {"error": result["error"]}
            
            db.commit()
            db.refresh(new_order)
            
            return {"success": True, "id": new_order.id}
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
    
    @staticmethod
    def update_order(db: Session, order_id: int, order_data: OrderUpdate):
        """
        Обновление существующего заказа.
        """
        # Получаем заказ
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": "Заказ не найден"}
        
        # Проверяем данные клиента
        if order_data.client_id:
            client = db.query(Client).filter(Client.id == order_data.client_id).first()
            if not client:
                return {"error": "Клиент не найден"}
            order.client_id = order_data.client_id
        
        # Проверяем данные менеджера
        if order_data.manager_id:
            manager = db.query(Employee).filter(
                Employee.id == order_data.manager_id,
                Employee.employee_type == "менеджер",
                Employee.active == 1
            ).first()
            if not manager:
                return {"error": "Менеджер не найден или неактивен"}
            order.manager_id = order_data.manager_id
        
        # Обновляем базовые поля
        if order_data.order_date:
            order.order_date = order_data.order_date
        
        if order_data.completion_date:
            order.completion_date = order_data.completion_date
        
        if order_data.notes is not None:
            order.notes = order_data.notes
        
        if order_data.status:
            order.status = order_data.status
            # Если заказ отмечен как "завершен" и нет даты завершения, устанавливаем текущую дату
            if order_data.status == "завершен" and not order.completion_date:
                order.completion_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if order_data.mount_price:
            order.mount_price = order_data.mount_price
        
        # Обновляем услуги, если они указаны
        if order_data.services:
            # Удаляем старые услуги
            db.query(OrderServiceModel).filter(OrderServiceModel.order_id == order_id).delete()
            
            # Добавляем новые услуги
            for service_data in order_data.services:
                service = db.query(Service).filter(Service.id == service_data.service_id).first()
                if not service:
                    db.rollback()
                    return {"error": f"Услуга с ID {service_data.service_id} не найдена"}
                
                # Если цена продажи не указана, берем из услуги
                selling_price = service_data.selling_price if service_data.selling_price else service.selling_price
                
                order_service = OrderServiceModel(
                    order_id=order_id,
                    service_id=service_data.service_id,
                    selling_price=selling_price,
                    sold_by_id=service_data.sold_by_id
                )
                db.add(order_service)
        
        # Обновляем сотрудников, если они указаны
        if order_data.employees:
            # Удаляем старых сотрудников
            db.query(OrderEmployee).filter(OrderEmployee.order_id == order_id).delete()
            
            # Добавляем новых сотрудников
            for employee_data in order_data.employees:
                employee = db.query(Employee).filter(
                    Employee.id == employee_data.employee_id,
                    Employee.active == 1
                ).first()
                if not employee:
                    db.rollback()
                    return {"error": f"Сотрудник с ID {employee_data.employee_id} не найден или неактивен"}
                
                # Проверяем тип сотрудника (для монтажников)
                if employee_data.employee_type == "монтажник" and employee.employee_type != "монтажник":
                    db.rollback()
                    return {"error": f"Сотрудник с ID {employee_data.employee_id} не является монтажником"}
                
                # Проверяем тип сотрудника (для владельца)
                if employee_data.employee_type == "владелец_на_монтаже" and employee.employee_type != "владелец":
                    db.rollback()
                    return {"error": f"Сотрудник с ID {employee_data.employee_id} не является владельцем"}
                
                order_employee = OrderEmployee(
                    order_id=order_id,
                    employee_id=employee_data.employee_id,
                    employee_type=employee_data.employee_type,
                    base_payment=employee_data.base_payment if employee_data.base_payment else INSTALLER_BASE_PAYMENT
                )
                db.add(order_employee)
        
        try:
            order.updated_at = datetime.now().strftime("%Y-%m-%d")
            db.commit()
            db.refresh(order)
            return {"success": True, "id": order.id}
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
    
    @staticmethod
    def delete_order(db: Session, order_id: int):
        """
        Удаление заказа.
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": "Заказ не найден"}
        
        try:
            # Удаляем связанные услуги
            db.query(OrderServiceModel).filter(OrderServiceModel.order_id == order_id).delete()
            
            # Удаляем связанных сотрудников
            db.query(OrderEmployee).filter(OrderEmployee.order_id == order_id).delete()
            
            # Удаляем сам заказ
            db.delete(order)
            db.commit()
            return {"success": True}
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
    
    @staticmethod
    def calculate_order_profit(db: Session, order_id: int):
        """
        Расчет прибыли по заказу.
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": "Заказ не найден"}
        
        # Инициализация
        total_revenue = order.mount_price  # Стоимость монтажа
        total_cost = 0  # Затраты
        total_commissions = order.owner_commission  # Комиссия владельца
        
        # Получаем все услуги заказа
        order_services = db.query(OrderService).filter(OrderService.order_id == order_id).all()
        
        # Определяем стандартную стоимость монтажа в зависимости от типа кондиционера
        standard_mount_price = DEFAULT_MOUNT_PRICE_7_9  # По умолчанию для 7 и 9 БТЮ
        ac_power_info = "7/9 БТЮ"
        
        for order_service in order_services:
            service = db.query(Service).filter(Service.id == order_service.service_id).first()
            if service and service.category == "Кондиционер":
                if service.power_type in ["12 БТЮ", "18 БТЮ"]:
                    standard_mount_price = DEFAULT_MOUNT_PRICE_12_18
                    ac_power_info = service.power_type
                    break
        
        # Расчет комиссии менеджера от завышения цены монтажа
        manager_mount_bonus = 0
        if order.mount_price > standard_mount_price:
            manager_mount_bonus = (order.mount_price - standard_mount_price) * MANAGER_MOUNT_UPSELL_PERCENT
            total_commissions += manager_mount_bonus
        
        # Комиссия менеджера за заказ
        manager_order_commission = MANAGER_ORDER_COMMISSION
        total_commissions += manager_order_commission
        
        manager_services_commission = 0
        installer_services_commission = 0
        
        for order_service in order_services:
            service = db.query(Service).filter(Service.id == order_service.service_id).first()
            if not service:
                continue
            
            # Добавляем к выручке
            total_revenue += order_service.selling_price
            
            # Добавляем к затратам (если есть закупочная цена)
            if service.purchase_price:
                total_cost += service.purchase_price
            
            # Рассчитываем комиссии
            profit = order_service.selling_price - (service.purchase_price or 0)
            
            if service.category == "Кондиционер":
                # Комиссия менеджера от продажи кондиционера
                manager_commission = profit * MANAGER_CONDITIONER_COMMISSION_PERCENT
                manager_services_commission += manager_commission
                total_commissions += manager_commission
            
            elif service.is_manager_bonus:
                # Комиссия менеджера от доп. услуг (монтажный комплект, виброопоры)
                manager_commission = profit * MANAGER_ADDON_COMMISSION_PERCENT
                manager_services_commission += manager_commission
                total_commissions += manager_commission
            
            elif order_service.sold_by_id:
                # Получаем сотрудника, который продал услугу
                employee = db.query(Employee).filter(Employee.id == order_service.sold_by_id).first()
                
                if employee and employee.employee_type == "монтажник":
                    # Фиксированная выплата монтажнику за проданную услугу
                    installer_commission = service.installer_bonus_fixed
                    installer_services_commission += installer_commission
                    total_commissions += installer_commission
        
        # Комиссии монтажникам за монтаж
        order_employees = db.query(OrderEmployee).filter(OrderEmployee.order_id == order_id).all()
        installers_base_commission = 0
        
        for order_emp in order_employees:
            installers_base_commission += order_emp.base_payment
            total_commissions += order_emp.base_payment
        
        # Расчет прибыли
        total_profit = total_revenue - total_cost - total_commissions
        
        return {
            "revenue": total_revenue,
            "cost": total_cost,
            "commissions": total_commissions,
            "profit": total_profit,
            "details": {
                "manager_order_commission": manager_order_commission,
                "manager_mount_bonus": manager_mount_bonus,
                "manager_services_commission": manager_services_commission,
                "installers_base_commission": installers_base_commission,
                "installer_services_commission": installer_services_commission,
                "owner_commission": order.owner_commission,
                "standard_mount_price": standard_mount_price,
                "ac_power_type": ac_power_info
            }
        }