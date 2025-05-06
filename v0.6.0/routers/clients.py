"""
Роутер для работы с клиентами.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services import ClientService
from schemas import ClientCreate, ClientUpdate, ClientResponse

router = APIRouter(prefix="/api/clients", tags=["clients"])

@router.get("", response_model=dict)
async def get_clients(
    search: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Получение списка клиентов с фильтрацией и пагинацией.
    """
    return ClientService.get_clients(db, search, source, page, limit)

@router.get("/{client_id}", response_model=dict)
async def get_client(client_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Получение информации о конкретном клиенте.
    """
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client

@router.post("", response_model=ClientResponse)
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    """
    Создание нового клиента.
    """
    try:
        result = ClientService.create_client(db, client)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{client_id}", response_model=dict)
async def update_client(
    client_id: int = Path(...),
    client: ClientUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Обновление данных клиента.
    """
    try:
        result = ClientService.update_client(db, client_id, client)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{client_id}", response_model=dict)
async def delete_client(client_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Удаление клиента.
    """
    result = ClientService.delete_client(db, client_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True}

@router.get("/stats/by-source", response_model=dict)
async def get_clients_by_source(db: Session = Depends(get_db)):
    """
    Получение статистики клиентов по источникам.
    """
    return ClientService.get_clients_by_source(db)