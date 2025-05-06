"""
Роутер для работы с заказами.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services import OrderService as OrderServiceClass
from schemas import OrderCreate, OrderUpdate, OrderResponse, OrderProfitResponse

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.get("", response_model=dict)
async def get_orders(
    status: Optional[str] = Query(None),
    client_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Получение списка заказов с фильтрацией и пагинацией.
    """
    return OrderServiceClass.get_orders(db, status, client_name, date_from, date_to, page, limit)

@router.get("/{order_id}", response_model=dict)
async def get_order(order_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Получение информации о конкретном заказе.
    """
    order = OrderServiceClass.get_order_details(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order

@router.post("", response_model=dict)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    Создание нового заказа.
    """
    result = OrderServiceClass.create_order(db, order)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "id": result["id"]}

@router.put("/{order_id}", response_model=dict)
async def update_order(
    order_id: int = Path(...),
    order: OrderUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Обновление данных заказа.
    """
    result = OrderServiceClass.update_order(db, order_id, order)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "id": result["id"]}

@router.delete("/{order_id}", response_model=dict)
async def delete_order(order_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Удаление заказа.
    """
    result = OrderServiceClass.delete_order(db, order_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True}

@router.get("/{order_id}/profit", response_model=dict)
async def get_order_profit(order_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Расчет прибыли по заказу.
    """
    result = OrderServiceClass.calculate_order_profit(db, order_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result