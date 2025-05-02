#!/bin/bash

# Путь к проекту
PROJECT_DIR="$HOME/crm-cond"
PORT=8000

# Проверка, существует ли директория проекта
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Ошибка: Директория $PROJECT_DIR не найдена. Создайте проект и скопируйте файлы."
    exit 1
fi

# Переход в директорию проекта
cd "$PROJECT_DIR" || exit 1

# Проверка и создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
echo "Установка зависимостей..."
pip install fastapi uvicorn sqlalchemy python-multipart pydantic

# Запуск сервера
echo "Запуск сервера на порту $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT &

# Сохранение PID процесса
echo $! > server.pid

echo "Сервер запущен. Доступен по адресу: http://localhost:$PORT/finance"
echo "Для внешнего доступа настройте проброс портов или используйте ngrok."
echo "Для остановки сервера выполните: kill $(cat server.pid)"