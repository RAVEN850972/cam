// Конфигурация API
const API_BASE_URL = 'http://localhost:8000/api';
const TOKEN = localStorage.getItem('token') || 'demo-token';

// Функция для отображения уведомлений
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');
    
    notification.className = 'notification';
    notification.classList.add(type === 'success' ? 'notification-success' : 'notification-error');
    
    notificationMessage.textContent = message;
    
    // Показываем уведомление
    setTimeout(() => {
        notification.classList.add('notification-show');
    }, 100);
    
    // Скрываем через 3 секунды
    setTimeout(() => {
        notification.classList.remove('notification-show');
    }, 3000);
}

// Обработка ошибок API
function handleApiError(error) {
    console.error('API Error:', error);
    showNotification('Ошибка при загрузке данных: ' + (error.message || 'Неизвестная ошибка'), 'error');
}

// Функция для загрузки данных с API с обработкой ошибок
async function fetchWithErrorHandling(url, options = {}) {
    try {
        // Реальное приложение использовало бы такой запрос:
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + TOKEN
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        handleApiError(error);
        throw error;
    }
}

// Форматирование валюты (рубли)
function formatCurrency(amount) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
    }).format(amount);
}

// Форматирование даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ru-RU', {
        day: 'numeric', 
        month: 'long', 
        year: 'numeric'
    }).format(date);
}

// Обновление индикатора изменения
function updateChangeIndicator(elementId, changeValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const isPositive = changeValue >= 0;
    element.className = 'flex items-center mt-2 text-sm';
    element.classList.add(isPositive ? 'text-green-500' : 'text-red-500');
    
    element.innerHTML = `
        <i class="fas fa-arrow-${isPositive ? 'up' : 'down'} mr-1"></i>
        <span>${isPositive ? '+' : ''}${changeValue.toFixed(1)}% от прошлого периода</span>
    `;
}