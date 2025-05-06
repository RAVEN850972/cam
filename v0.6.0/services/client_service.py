"""
Сервис для работы с клиентами.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from models import Client, Order
from schemas import ClientCreate, ClientUpdate

class ClientService:
    """
    Сервис для работы с клиентами.
    """
    
    @staticmethod
    def get_clients(
        db: Session, 
        search: Optional[str] = None,
        source: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ):
        """
        Получение списка клиентов с фильтрацией и пагинацией.
        """
        query = db.query(Client).order_by(desc(Client.created_at))
        
        # Поиск по имени или телефону
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
        
        # Подсчет заказов для каждого клиента
        clients_with_orders = []
        for client in clients:
            order_count = db.query(Order).filter(Order.client_id == client.id).count()
            
            client_dict = {
                "id": client.id,
                "name": client.name,
                "phone": client.phone,
                "source": client.source,
                "created_at": client.created_at,
                "updated_at": client.updated_at,
                "order_count": order_count
            }
            
            clients_with_orders.append(client_dict)
        
        # Общее количество страниц
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "clients": clients_with_orders,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "limit": limit
        }
    
    @staticmethod
    def get_client(db: Session, client_id: int):
        """
        Получение клиента по ID.
        """
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            return None
        
        # Получаем количество заказов
        order_count = db.query(Order).filter(Order.client_id == client_id).count()
        
        # Получаем заказы клиента
        orders = db.query(Order).filter(Order.client_id == client_id).order_by(desc(Order.order_date)).all()
        
        orders_list = []
        for order in orders:
            orders_list.append({
                "id": order.id,
                "order_date": order.order_date,
                "status": order.status,
                "mount_price": order.mount_price
            })
        
        return {
            "id": client.id,
            "name": client.name,
            "phone": client.phone,
            "source": client.source,
            "created_at": client.created_at,
            "updated_at": client.updated_at,
            "order_count": order_count,
            "orders": orders_list
        }
    
    @staticmethod
    def create_client(db: Session, client_data: ClientCreate):
        """
        Создание нового клиента.
        """
        # Проверяем, существует ли клиент с таким телефоном
        existing_client = db.query(Client).filter(Client.phone == client_data.phone).first()
        if existing_client:
            return {"error": "Клиент с таким номером телефона уже существует"}
        
        # Создаем нового клиента
        client = Client(
            name=client_data.name,
            phone=client_data.phone,
            source=client_data.source
        )
        
        try:
            db.add(client)
            db.commit()
            db.refresh(client)
            return client
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def update_client(db: Session, client_id: int, client_data: ClientUpdate):
        """
        Обновление данных клиента.
        """
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            return {"error": "Клиент не найден"}
        
        # Проверяем, существует ли другой клиент с таким телефоном
        if client_data.phone and client_data.phone != client.phone:
            existing_client = db.query(Client).filter(
                and_(
                    Client.phone == client_data.phone,
                    Client.id != client_id
                )
            ).first()
            
            if existing_client:
                return {"error": "Другой клиент с таким номером телефона уже существует"}
        
        # Обновляем поля
        if client_data.name:
            client.name = client_data.name
        
        if client_data.phone:
            client.phone = client_data.phone
        
        if client_data.source:
            client.source = client_data.source
        
        client.updated_at = datetime.now().strftime("%Y-%m-%d")
        
        try:
            db.commit()
            db.refresh(client)
            return client
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def delete_client(db: Session, client_id: int):
        """
        Удаление клиента.
        """
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            return {"error": "Клиент не найден"}
        
        # Проверяем, есть ли у клиента заказы
        has_orders = db.query(Order).filter(Order.client_id == client_id).first()
        if has_orders:
            return {"error": "Нельзя удалить клиента с существующими заказами"}
        
        try:
            db.delete(client)
            db.commit()
            return {"success": True}
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_clients_by_source(db: Session):
        """
        Получение статистики клиентов по источникам.
        """
        from sqlalchemy import func
        from config import CLIENT_SOURCES
        
        stats = {}
        
        # Подсчитываем количество клиентов по каждому источнику
        for source in CLIENT_SOURCES:
            count = db.query(func.count(Client.id)).filter(Client.source == source).scalar()
            stats[source] = count
        
        return stats