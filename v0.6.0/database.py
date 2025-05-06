"""
Настройки базы данных для CRM-системы кондиционеров.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

# Создаем движок SQLAlchemy для SQLite
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Необходимо для SQLite
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии базы данных
def get_db():
    """
    Получение сессии базы данных для использования в запросах.
    Автоматически закрывает сессию после завершения запроса.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для инициализации базы данных
def init_db():
    """
    Создает все таблицы базы данных на основе моделей.
    """
    from models import base  # Импортируем сюда для предотвращения цикличных импортов
    Base.metadata.create_all(bind=engine)

# Функция для заполнения базы данных начальными данными
def fill_initial_data():
    """
    Заполняет базу данных начальными данными (если необходимо).
    """
    db = SessionLocal()
    
    # Здесь можно добавить код для создания начальных данных:
    # - базовых услуг
    # - владельца бизнеса
    # - категорий расходов и т.д.
    
    db.close()