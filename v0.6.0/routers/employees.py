"""
Роутер для работы с сотрудниками.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from services import EmployeeService
from schemas import EmployeeCreate, EmployeeUpdate

router = APIRouter(prefix="/api/employees", tags=["employees"])

@router.get("", response_model=dict)
async def get_employees(
    employee_type: Optional[str] = None,
    active: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Получение списка сотрудников с фильтрацией и пагинацией.
    """
    return EmployeeService.get_employees(db, employee_type, active, page, limit)

@router.get("/list", response_model=dict)
async def get_employees_with_salary(
    employee_type: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Получение списка сотрудников с расчетом зарплаты за месяц.
    """
    # Получаем всех сотрудников
    employees_data = EmployeeService.get_employees(db, employee_type=employee_type, active=1, page=1, limit=100)
    
    # Добавляем информацию о зарплате
    employees_with_salary = []
    for employee in employees_data["employees"]:
        # Вычисляем зарплату для каждого сотрудника
        salary_data = EmployeeService.calculate_salary(db, employee["id"], month)
        
        employee_info = employee.copy()
        if salary_data:
            employee_info.update({
                "salary": salary_data["salary"],
                "paid": salary_data["paid"],
                "to_pay": salary_data["to_pay"],
                "base_salary_amount": salary_data["details"]["base_salary"],
                "order_payments": salary_data["details"]["order_payments"],
                "additional_commission": salary_data["details"]["additional_commission"],
                "ac_commission": salary_data["details"]["ac_commission"]
            })
        else:
            employee_info.update({
                "salary": 0,
                "paid": 0,
                "to_pay": 0,
                "base_salary_amount": 0,
                "order_payments": 0,
                "additional_commission": 0,
                "ac_commission": 0
            })
        
        employees_with_salary.append(employee_info)
    
    return {
        "employees": employees_with_salary,
        "total_count": len(employees_with_salary),
        "month": month or datetime.now().strftime("%Y-%m")
    }

@router.get("/{employee_id}", response_model=dict)
async def get_employee(employee_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Получение информации о конкретном сотруднике.
    """
    employee = EmployeeService.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return employee

@router.post("", response_model=dict)
async def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """
    Создание нового сотрудника.
    """
    try:
        created_employee = EmployeeService.create_employee(db, employee)
        return created_employee
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{employee_id}", response_model=dict)
async def update_employee(
    employee_id: int = Path(...),
    employee: EmployeeUpdate = ...,
    db: Session = Depends(get_db)
):
    """
    Обновление данных сотрудника.
    """
    try:
        updated_employee = EmployeeService.update_employee(db, employee_id, employee)
        if not updated_employee:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
        return updated_employee
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{employee_id}/deactivate", response_model=dict)
async def deactivate_employee(employee_id: int = Path(...), db: Session = Depends(get_db)):
    """
    Деактивация сотрудника.
    """
    try:
        deactivated_employee = EmployeeService.deactivate_employee(db, employee_id)
        if not deactivated_employee:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
        return deactivated_employee
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{employee_id}/salary", response_model=dict)
async def get_employee_salary(
    employee_id: int = Path(...),
    month: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получение зарплаты сотрудника за месяц.
    """
    salary_data = EmployeeService.calculate_salary(db, employee_id, month)
    if not salary_data:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return salary_data

@router.post("/{employee_id}/pay", response_model=dict)
async def pay_employee(
    employee_id: int = Path(...),
    amount: float = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Выплата зарплаты сотруднику.
    """
    result = EmployeeService.add_payment(db, employee_id, amount, description)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "id": result["id"]}