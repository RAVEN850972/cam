"""
Сервис для работы с услугами.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models import Service, Order, OrderService
from schemas import ServiceCreate, ServiceUpdate

class ServiceService:
    """
    Сервис для работы с услугами.
    """
    
    @staticmethod
    def get_services(
        db: Session, 
        search: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ):
        """
        Получение списка услуг с фильтрацией и пагинацией.
        """
        query = db.query(Service).order_by(Service.name)
        
        # Фильтрация по названию
        if search:
            query = query.filter(Service.name.ilike(f"%{search}%"))
        
        # Фильтрация по категории
        if category and category != "Все":
            query = query.filter(Service.category == category)
        
        # Получаем общее количество записей
        total_count = query.count()
        
        # Применяем пагинацию
        services = query.offset((page - 1) * limit).limit(limit).all()
        
        # Подсчет использования каждой услуги
        services_with_usage = []
        for service in services:
            # Подсчет использования услуги в заказах
            usage = db.query(OrderService).filter(OrderService.service_id == service.id).count()
            
            service_dict = {
                "id": service.id,
                "name": service.name,
                "category": service.category,
                "purchase_price": service.purchase_price,
                "selling_price": service.selling_price,
                "default_price": service.default_price,
                "is_manager_bonus": service.is_manager_bonus,
                "installer_bonus_fixed": service.installer_bonus_fixed,
                "profit_margin_percent": service.profit_margin_percent,
                "created_at": service.created_at,
                "updated_at": service.updated_at,
                "total_usage": usage
            }
            
            services_with_usage.append(service_dict)
        
        # Общее количество страниц
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "services": services_with_usage,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "limit": limit
        }
    
    @staticmethod
    def get_service(db: Session, service_id: int):
        """
        Получение услуги по ID.
        """
        service = db.query(Service).filter(Service.id == service_id).first()
        
        if not service:
            return None
        
        # Подсчет использования услуги в заказах через таблицу OrderService
        usage = db.query(OrderService).filter(OrderService.service_id == service_id).count()
        
        return {
            "id": service.id,
            "name": service.name,
            "category": service.category,
            "purchase_price": service.purchase_price,
            "selling_price": service.selling_price,
            "default_price": service.default_price,
            "is_manager_bonus": service.is_manager_bonus,
            "installer_bonus_fixed": service.installer_bonus_fixed,
            "profit_margin_percent": service.profit_margin_percent,
            "created_at": service.created_at,
            "updated_at": service.updated_at,
            "total_usage": usage,
            "usage_details": {
                "in_orders": usage
            }
        }
    
    @staticmethod
    def create_service(db: Session, service_data: ServiceCreate):
        """
        Создание новой услуги.
        """
        service = Service(
            name=service_data.name,
            category=service_data.category,
            purchase_price=service_data.purchase_price,
            selling_price=service_data.selling_price,
            default_price=service_data.default_price,
            is_manager_bonus=service_data.is_manager_bonus,
            installer_bonus_fixed=service_data.installer_bonus_fixed,
            profit_margin_percent=service_data.profit_margin_percent
        )
        
        try:
            db.add(service)
            db.commit()
            db.refresh(service)
            return service
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def update_service(db: Session, service_id: int, service_data: ServiceUpdate):
        """
        Обновление данных услуги.
        """
        service = db.query(Service).filter(Service.id == service_id).first()
        
        if not service:
            return {"error": "Услуга не найдена"}
        
        # Обновляем поля
        if service_data.name is not None:
            service.name = service_data.name
        
        if service_data.category is not None:
            service.category = service_data.category
        
        if service_data.purchase_price is not None:
            service.purchase_price = service_data.purchase_price
        
        if service_data.selling_price is not None:
            service.selling_price = service_data.selling_price
        
        if service_data.default_price is not None:
            service.default_price = service_data.default_price
        
        if service_data.is_manager_bonus is not None:
            service.is_manager_bonus = service_data.is_manager_bonus
        
        if service_data.installer_bonus_fixed is not None:
            service.installer_bonus_fixed = service_data.installer_bonus_fixed
        
        if service_data.profit_margin_percent is not None:
            service.profit_margin_percent = service_data.profit_margin_percent
        
        service.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        try:
            db.commit()
            db.refresh(service)
            return service
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def delete_service(db: Session, service_id: int):
        """
        Удаление услуги.
        """
        service = db.query(Service).filter(Service.id == service_id).first()
        
        if not service:
            return {"error": "Услуга не найдена"}
        
        # Проверяем, используется ли услуга в заказах
        used_in_orders = db.query(Order).filter(Order.service_id == service_id).first()
        used_in_additional = db.query(OrderService).filter(OrderService.service_id == service_id).first()
        
        if used_in_orders or used_in_additional:
            return {"error": "Нельзя удалить услугу, она используется в заказах"}
        
        try:
            db.delete(service)
            db.commit()
            return {"success": True}
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_services_by_category(db: Session):
        """
        Получение статистики услуг по категориям.
        """
        from sqlalchemy import func
        from config import SERVICE_CATEGORIES
        
        stats = {}
        
        # Подсчитываем количество услуг по каждой категории
        for category in SERVICE_CATEGORIES:
            count = db.query(func.count(Service.id)).filter(Service.category == category).scalar()
            avg_price = db.query(func.avg(Service.selling_price)).filter(Service.category == category).scalar() or 0
            
            stats[category] = {
                "count": count,
                "avg_price": round(avg_price, 2)
            }
        
        return stats