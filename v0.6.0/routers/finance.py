"""
Роутер для работы с финансами.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services import FinanceService
from schemas import ExpenseCreate, CompanyBalanceCreate, FinanceSummaryResponse

router = APIRouter(prefix="/api/finance", tags=["finance"])

@router.get("/summary", response_model=dict)
async def get_finance_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Получение финансовой сводки за период.
    """
    return FinanceService.get_finance_summary(db, date_from, date_to)

@router.get("/transactions", response_model=dict)
async def get_transactions(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Получение истории финансовых транзакций с фильтрацией и пагинацией.
    """
    return FinanceService.get_transaction_history(db, date_from, date_to, transaction_type, page, limit)

@router.get("/forecast", response_model=dict)
async def get_cash_flow_forecast(
    months_ahead: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db)
):
    """
    Получение прогноза денежных потоков на несколько месяцев вперед.
    """
    return FinanceService.get_cash_flow_forecast(db, months_ahead)

@router.post("/expenses", response_model=dict)
async def add_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    """
    Добавление нового расхода.
    """
    result = FinanceService.add_expense(db, expense)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "id": result["id"]}

@router.post("/initial-balance", response_model=dict)
async def set_initial_balance(
    initial_balance: CompanyBalanceCreate,
    db: Session = Depends(get_db)
):
    """
    Установка начального баланса компании.
    """
    result = FinanceService.set_initial_balance(db, initial_balance)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "balance": result["balance"]}

@router.get("/balance", response_model=dict)
async def get_balance(db: Session = Depends(get_db)):
    """
    Получение текущего баланса компании.
    """
    balance = FinanceService.get_company_balance(db)
    if not balance:
        return {
            "balance": None,
            "initial_balance": None,
            "initial_balance_set": False
        }
    return {
        "balance": balance.balance,
        "initial_balance": balance.initial_balance,
        "initial_balance_set": True,
        "updated_at": balance.updated_at
    }