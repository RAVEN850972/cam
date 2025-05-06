"""
Сервис для работы с финансами.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from models import CompanyBalance, Order, Expense, FinancialTransaction
from models import Payment, Service, OrderService, OrderEmployee, Employee, Client
from schemas import CompanyBalanceCreate
from config import TRANSACTION_TYPES, TRANSACTION_SOURCE_TYPES

class FinanceService:
    """
    Сервис для работы с финансами компании.
    """

    @staticmethod
    def get_company_balance(db: Session) -> CompanyBalance:
        """
        Получение текущего баланса компании.
        """
        return db.query(CompanyBalance).first()
    
    @staticmethod
    def set_initial_balance(db: Session, balance_data: CompanyBalanceCreate):
        """
        Установка начального баланса компании.
        """
        # Проверяем, есть ли уже запись о балансе
        existing_balance = db.query(CompanyBalance).first()
        if existing_balance:
            return {"error": "Начальный баланс уже установлен"}
        
        # Создаем новую запись баланса
        balance = CompanyBalance(
            balance=balance_data.initial_balance,
            initial_balance=balance_data.initial_balance,
            updated_at=datetime.now().strftime("%Y-%m-%d")
        )
        db.add(balance)
        db.flush()
        
        # Создаем транзакцию
        transaction = FinancialTransaction(
            transaction_date=datetime.now().strftime("%Y-%m-%d"),
            amount=balance_data.initial_balance,
            transaction_type="доход",
            source_type="вклад владельца",
            source_id=None,
            description="Установка начального баланса"
        )
        db.add(transaction)
        db.commit()
        
        # Обновляем баланс с ID транзакции
        balance.last_transaction_id = transaction.id
        balance.last_transaction_type = "доход"
        db.commit()
        db.refresh(balance)
        
        return {"success": True, "balance": balance}
    
    @staticmethod
    def update_company_balance_on_order_creation(db: Session, order_id: int):
        """
        Обновление баланса компании при создании заказа.
        """
        # Получаем заказ
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": "Заказ не найден"}
        
        # Рассчитываем общую сумму заказа
        total_amount = order.mount_price
        
        # Получаем все услуги заказа
        order_services = db.query(OrderService).filter(OrderService.order_id == order_id).all()
        for os in order_services:
            total_amount += os.selling_price
        
        # Создаем транзакцию
        transaction = FinancialTransaction(
            transaction_date=datetime.now().strftime("%Y-%m-%d"),
            amount=total_amount,
            transaction_type="доход",
            source_type="заказ",
            source_id=order_id,
            description=f"Заказ №{order_id} - {order.status}"
        )
        db.add(transaction)
        db.flush()
        
        # Обновляем баланс компании
        company_balance = db.query(CompanyBalance).first()
        if not company_balance:
            return {"error": "Баланс компании не инициализирован"}
        
        company_balance.balance += total_amount
        company_balance.last_transaction_id = transaction.id
        company_balance.last_transaction_type = "доход"
        company_balance.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        db.refresh(company_balance)
        
        return {"success": True, "balance": company_balance.balance}
    
    @staticmethod
    def update_company_balance_on_expense(db: Session, expense_id: int):
        """
        Обновление баланса компании при добавлении расхода.
        """
        # Получаем расход
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            return {"error": "Расход не найден"}
        
        # Создаем транзакцию
        transaction = FinancialTransaction(
            transaction_date=expense.expense_date,
            amount=expense.amount,
            transaction_type="расход",
            source_type="расход",
            source_id=expense_id,
            description=f"Расход: {expense.category} - {expense.description or ''}"
        )
        db.add(transaction)
        db.flush()
        
        # Обновляем баланс компании
        company_balance = db.query(CompanyBalance).first()
        if not company_balance:
            return {"error": "Баланс компании не инициализирован"}
        
        company_balance.balance -= expense.amount
        company_balance.last_transaction_id = transaction.id
        company_balance.last_transaction_type = "расход"
        company_balance.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        db.refresh(company_balance)
        
        return {"success": True, "balance": company_balance.balance}
    
    @staticmethod
    def update_company_balance_on_payment(db: Session, payment_id: int):
        """
        Обновление баланса компании при выплате зарплаты.
        """
        # Получаем выплату
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            return {"error": "Выплата не найдена"}
        
        # Только для положительных выплат (не штрафов)
        if payment.amount <= 0:
            return {"success": True, "message": "Штрафы не уменьшают баланс компании"}
        
        # Получаем сотрудника
        employee = db.query(Employee).filter(Employee.id == payment.employee_id).first()
        if not employee:
            return {"error": "Сотрудник не найден"}
        
        # Создаем транзакцию
        transaction = FinancialTransaction(
            transaction_date=payment.payment_date,
            amount=payment.amount,
            transaction_type="расход",
            source_type="выплата",
            source_id=payment_id,
            description=f"Выплата: {employee.name} - {payment.description or ''}"
        )
        db.add(transaction)
        db.flush()
        
        # Обновляем баланс компании
        company_balance = db.query(CompanyBalance).first()
        if not company_balance:
            return {"error": "Баланс компании не инициализирован"}
        
        company_balance.balance -= payment.amount
        company_balance.last_transaction_id = transaction.id
        company_balance.last_transaction_type = "расход"
        company_balance.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        db.commit()
        db.refresh(company_balance)
        
        return {"success": True, "balance": company_balance.balance}
    
    @staticmethod
    def get_transaction_history(
        db: Session, 
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        transaction_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ):
        """
        Получение истории финансовых транзакций с фильтрацией и пагинацией.
        """
        query = db.query(FinancialTransaction).order_by(desc(FinancialTransaction.transaction_date))
        
        if date_from:
            query = query.filter(FinancialTransaction.transaction_date >= date_from)
        if date_to:
            query = query.filter(FinancialTransaction.transaction_date <= date_to)
        if transaction_type:
            query = query.filter(FinancialTransaction.transaction_type == transaction_type)
        
        # Получаем общее количество записей
        total_count = query.count()
        
        # Применяем пагинацию
        transactions = query.offset((page - 1) * limit).limit(limit).all()
        
        # Преобразуем модели SQLAlchemy в словари для сериализации
        transactions_list = []
        for transaction in transactions:
            transactions_list.append({
                "id": transaction.id,
                "transaction_date": transaction.transaction_date,
                "amount": transaction.amount,
                "transaction_type": transaction.transaction_type,
                "source_type": transaction.source_type,
                "source_id": transaction.source_id,
                "description": transaction.description,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at
            })
        
        return {
            "transactions": transactions_list,
            "total_count": total_count,
            "page": page,
            "limit": limit
        }
    
    @staticmethod
    def get_finance_summary(db: Session, date_from: Optional[str] = None, date_to: Optional[str] = None):
        """
        Получение финансовой сводки за период.
        """
        # Инициализация результата
        summary = {
            "total_revenue": 0,
            "total_expenses": 0,
            "total_profit": 0,
            "total_commissions": 0,
            "expenses_by_category": {},
            "revenue_by_source": {},
            "current_balance": 0
        }
        
        # Получаем текущий баланс
        company_balance = db.query(CompanyBalance).first()
        if company_balance:
            summary["current_balance"] = company_balance.balance
        
        # Фильтрация по дате
        orders_query = db.query(Order).filter(Order.status == "завершен")
        expenses_query = db.query(Expense)
        
        if date_from:
            orders_query = orders_query.filter(Order.order_date >= date_from)
            expenses_query = expenses_query.filter(Expense.expense_date >= date_from)
        if date_to:
            orders_query = orders_query.filter(Order.order_date <= date_to)
            expenses_query = expenses_query.filter(Expense.expense_date <= date_to)
        
        # Получаем заказы и их услуги
        orders = orders_query.all()
        
        # Рассчитываем выручку и комиссии по заказам
        for order in orders:
            # Основная услуга - монтаж
            summary["total_revenue"] += order.mount_price
            
            # Комиссия владельца
            summary["total_commissions"] += order.owner_commission
            
            # Комиссия менеджера за заказ
            from config import MANAGER_ORDER_COMMISSION, DEFAULT_MOUNT_PRICE, MANAGER_MOUNT_UPSELL_PERCENT
            summary["total_commissions"] += MANAGER_ORDER_COMMISSION
            
            # Комиссия менеджера за завышение цены монтажа
            if order.mount_price > DEFAULT_MOUNT_PRICE:
                manager_mount_bonus = (order.mount_price - DEFAULT_MOUNT_PRICE) * MANAGER_MOUNT_UPSELL_PERCENT
                summary["total_commissions"] += manager_mount_bonus
            
            # Получаем все услуги заказа
            order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
            
            for order_service in order_services:
                service = db.query(Service).filter(Service.id == order_service.service_id).first()
                if service:
                    # Добавляем к выручке
                    summary["total_revenue"] += order_service.selling_price
                    
                    # Рассчитываем комиссии
                    profit = order_service.selling_price - (service.purchase_price or 0)
                    
                    if service.category == "Кондиционер":
                        from config import MANAGER_CONDITIONER_COMMISSION_PERCENT
                        manager_commission = profit * MANAGER_CONDITIONER_COMMISSION_PERCENT
                        summary["total_commissions"] += manager_commission
                    
                    elif service.is_manager_bonus:
                        from config import MANAGER_ADDON_COMMISSION_PERCENT
                        manager_commission = profit * MANAGER_ADDON_COMMISSION_PERCENT
                        summary["total_commissions"] += manager_commission
                    
                    elif order_service.sold_by_id:
                        # Фиксированная комиссия монтажнику за проданную услугу
                        summary["total_commissions"] += service.installer_bonus_fixed
            
            # Комиссии монтажникам за монтаж
            order_employees = db.query(OrderEmployee).filter(OrderEmployee.order_id == order.id).all()
            for order_emp in order_employees:
                summary["total_commissions"] += order_emp.base_payment  # 1500 каждому
            
            # Добавляем к статистике по источникам
            client = db.query(Client).filter(Client.id == order.client_id).first()
            if client:
                if client.source not in summary["revenue_by_source"]:
                    summary["revenue_by_source"][client.source] = 0
                summary["revenue_by_source"][client.source] += order.mount_price
                
                for order_service in order_services:
                    summary["revenue_by_source"][client.source] += order_service.selling_price
        
        # Рассчитываем расходы
        expenses = expenses_query.all()
        for expense in expenses:
            summary["total_expenses"] += expense.amount
            
            # Статистика по категориям
            if expense.category not in summary["expenses_by_category"]:
                summary["expenses_by_category"][expense.category] = 0
            summary["expenses_by_category"][expense.category] += expense.amount
        
        # Итоговая прибыль
        summary["total_profit"] = summary["total_revenue"] - summary["total_expenses"] - summary["total_commissions"]
        
        return summary
    
    @staticmethod
    def get_cash_flow_forecast(db: Session, months_ahead: int = 3):
        """
        Получение прогноза денежных потоков на несколько месяцев вперед.
        """
        # Последние 3 месяца для анализа тренда
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Получаем среднемесячные показатели доходов
        orders_query = db.query(Order).filter(
            Order.status == "завершен",
            Order.order_date >= three_months_ago,
            Order.order_date <= current_date_str
        )
        
        total_revenue = 0
        orders_count = 0
        
        for order in orders_query.all():
            total_revenue += order.mount_price
            orders_count += 1
            
            order_services = db.query(OrderService).filter(OrderService.order_id == order.id).all()
            for os in order_services:
                total_revenue += os.selling_price
        
        avg_revenue = total_revenue / 3 if total_revenue > 0 else 0
        
        # Получаем среднемесячные показатели расходов
        expenses_query = db.query(Expense).filter(
            Expense.expense_date >= three_months_ago,
            Expense.expense_date <= current_date_str
        )
        
        total_expenses = sum(expense.amount for expense in expenses_query.all())
        avg_expenses = total_expenses / 3 if total_expenses > 0 else 0
        
        # Рассчитываем средние комиссии
        # Для простоты примем как процент от выручки
        avg_commissions = avg_revenue * 0.3
        
        # Средняя прибыль
        avg_profit = avg_revenue - avg_expenses - avg_commissions
        
        # Прогноз на заданное количество месяцев вперед
        forecast = []
        current_balance = db.query(CompanyBalance).first()
        balance = current_balance.balance if current_balance else 0
        
        for i in range(1, months_ahead + 1):
            month_date = (datetime.now() + timedelta(days=30 * i)).strftime("%Y-%m")
            forecast_balance = balance + (avg_profit * i)
            
            forecast.append({
                "month": month_date,
                "forecasted_revenue": round(avg_revenue, 2),
                "forecasted_expenses": round(avg_expenses, 2),
                "forecasted_profit": round(avg_profit, 2),
                "forecasted_balance": round(forecast_balance, 2)
            })
        
        return {"forecast": forecast}
    
    @staticmethod
    def add_expense(db: Session, expense_data):
        """
        Добавление нового расхода и обновление баланса компании.
        """
        # Создаем новый расход
        expense = Expense(
            category=expense_data.category,
            amount=expense_data.amount,
            description=expense_data.description,
            expense_date=expense_data.expense_date,
            expense_type=expense_data.expense_type,
            related_order_id=expense_data.related_order_id,
            related_service_id=expense_data.related_service_id
        )
        db.add(expense)
        db.flush()
        
        # Обновляем баланс компании
        result = FinanceService.update_company_balance_on_expense(db, expense.id)
        
        if "error" in result:
            db.rollback()
            return {"error": result["error"]}
        
        db.commit()
        db.refresh(expense)
        
        return {"success": True, "id": expense.id}