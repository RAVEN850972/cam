FROM python:3.10-slim

# Установка рабочей директории
WORKDIR /app

# Обновление pip
RUN pip install --no-cache-dir --upgrade pip

# Установка необходимых пакетов для сборки некоторых зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директорий для хранения данных
RUN mkdir -p /app/data

# Настройка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:///data/aircon_crm.db

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]