"""
Роутер для работы с услугами.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services import ServiceService
from schemas import ServiceCreate, ServiceUpdate, ServiceResponse

router = APIRouter(prefix="/api/services", tags=["services"])

@router.get("", response_model=dict)
async def get_services(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Получение списка услуг с фильтрацией и пагинацией.
    """
    return ServiceService.get_services(db, search, category, page, limit)

@router.get("/{service_id}", response_model=dict)
async def get_service(service_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Получение информации о конкретной услуге.
    """
    service = ServiceService.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return service

@router.post("", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, db: Session = Depends(get_db)):
    """
    Создание новой услуги.
    """
    try:
        return ServiceService.create_service(db, service)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{service_id}", response_model=dict)
async def update_service(
    service_id: int = Path(...),
    service: ServiceUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Обновление данных услуги.
    """
    try:
        result = ServiceService.update_service(db, service_id, service)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{service_id}", response_model=dict)
async def delete_service(service_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Удаление услуги.
    """
    result = ServiceService.delete_service(db, service_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True}

@router.get("/stats/by-category", response_model=dict)
async def get_services_by_category(db: Session = Depends(get_db)):
    """
    Получение статистики услуг по категориям.
    """
    return ServiceService.get_services_by_category(db)