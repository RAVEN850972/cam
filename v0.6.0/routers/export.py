"""
Роутер для экспорта данных.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services import ExportService

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/orders")
async def export_orders(
    format: str = Query("csv"),
    status: Optional[str] = Query(None),
    client_name: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Экспорт данных о заказах.
    """
    result = ExportService.export_orders(db, format, status, client_name, date_from, date_to)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return StreamingResponse(
        iter([result["data"]]),
        media_type=result["media_type"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.get("/clients")
async def export_clients(
    format: str = Query("csv"),
    search: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Экспорт данных о клиентах.
    """
    result = ExportService.export_clients(db, format, search, source)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return StreamingResponse(
        iter([result["data"]]),
        media_type=result["media_type"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.get("/services")
async def export_services(
    format: str = Query("csv"),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Экспорт данных об услугах.
    """
    result = ExportService.export_services(db, format, search, category)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return StreamingResponse(
        iter([result["data"]]),
        media_type=result["media_type"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.get("/employees")
async def export_employees(
    format: str = Query("csv"),
    employee_type: Optional[str] = Query(None),
    active: Optional[int] = Query(None),
    month: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Экспорт данных о сотрудниках.
    """
    result = ExportService.export_employees(db, format, employee_type, active, month)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return StreamingResponse(
        iter([result["data"]]),
        media_type=result["media_type"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.get("/finances")
async def export_finances(
    format: str = Query("csv"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Экспорт финансовых данных.
    """
    result = ExportService.export_finances(db, format, date_from, date_to)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return StreamingResponse(
        iter([result["data"]]),
        media_type=result["media_type"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )