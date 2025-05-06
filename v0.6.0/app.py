"""
Основной файл FastAPI-приложения для CRM-системы компании по установке кондиционеров.
"""
from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

# Импорт настроек
from config import APP_NAME, APP_VERSION, DEBUG
from database import init_db, get_db, fill_initial_data

# Импорт роутеров
from routers import employee_router, client_router, service_router, order_router, finance_router, export_router

# Инициализация логгера
logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(APP_NAME)

# Создание приложения FastAPI
app = FastAPI(
    title=APP_NAME,
    description="CRM для компании по установке кондиционеров",
    version=APP_VERSION,
    debug=DEBUG
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники (в продакшене лучше указать конкретные домены)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")

# Загрузка шаблонов
templates = Jinja2Templates(directory="templates")

# Подключение роутеров
app.include_router(employee_router)
app.include_router(client_router)
app.include_router(service_router)
app.include_router(order_router)
app.include_router(finance_router)
app.include_router(export_router)

# Инициализация базы данных при запуске
@app.on_event("startup")
async def startup_event():
    """
    Инициализация базы данных при запуске приложения.
    """
    logger.info(f"Инициализация базы данных {APP_NAME}")
    init_db()
    fill_initial_data()
    logger.info(f"База данных {APP_NAME} инициализирована")

# Главная страница (дашборд)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    """
    Отображение главной страницы (дашборда).
    """
    return templates.TemplateResponse("index.html", {"request": request, "app_name": APP_NAME})

# Страница сотрудников
@app.get("/employees", response_class=HTMLResponse)
async def employees_page(request: Request, db: Session = Depends(get_db)):
    """
    Отображение страницы сотрудников.
    """
    return templates.TemplateResponse("employees.html", {"request": request})

# Страница клиентов
@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request, db: Session = Depends(get_db)):
    """
    Отображение страницы клиентов.
    """
    return templates.TemplateResponse("clients.html", {"request": request})

# Страница услуг
@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request, db: Session = Depends(get_db)):
    """
    Отображение страницы услуг.
    """
    return templates.TemplateResponse("services.html", {"request": request})

# Страница заказов
@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, db: Session = Depends(get_db)):
    """
    Отображение страницы заказов.
    """
    return templates.TemplateResponse("orders.html", {"request": request})

# Страница финансов
@app.get("/finance", response_class=HTMLResponse)
async def finance_page(request: Request, db: Session = Depends(get_db)):
    """
    Отображение страницы финансов.
    """
    return templates.TemplateResponse("finance.html", {"request": request})

# Страница экспорта
@app.get("/export", response_class=HTMLResponse)
async def export_page(request: Request, db: Session = Depends(get_db)):
    """
    Отображение страницы экспорта.
    """
    return templates.TemplateResponse("export.html", {"request": request})

# Страница зарплат 
@app.get("/salary", response_class=HTMLResponse)
async def salary_page(request: Request, db: Session = Depends(get_db)):
    """
    Отображение страницы зарплат.
    """
    return templates.TemplateResponse("salary.html", {"request": request})

# Запуск приложения (при запуске скрипта напрямую)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)