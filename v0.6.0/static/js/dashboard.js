// Константы и глобальные переменные
const API_BASE_URL = 'http://localhost:8000/api';
let currentPeriod = 'month';
let revenueChart = null;
let conversionChart = null;

// Инициализация дашборда
document.addEventListener('DOMContentLoaded', function() {
    // Мобильное меню
    setupMobileMenu();
    
    // Настройка переключателя периода
    setupPeriodSwitcher();
    
    // Загрузка начальных данных
    loadFinanceSummary();
    loadRecentOrders();
    initCalendar();
    
    // Кнопка обновления заказов
    document.getElementById('refresh-orders').addEventListener('click', function() {
        loadRecentOrders();
    });
});

// Настройка мобильного меню
function setupMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMenuBtn = document.getElementById('close-mobile-menu');
    
    mobileMenuBtn.addEventListener('click', function() {
        mobileMenu.classList.remove('hidden');
    });
    
    closeMenuBtn.addEventListener('click', function() {
        mobileMenu.classList.add('hidden');
    });
    
    // Закрытие при клике вне меню
    mobileMenu.addEventListener('click', function(e) {
        if (e.target === mobileMenu) {
            mobileMenu.classList.add('hidden');
        }
    });
    
    // Закрытие при клике на пункт меню
    const menuLinks = mobileMenu.querySelectorAll('.menu-item');
    menuLinks.forEach(link => {
        link.addEventListener('click', function() {
            mobileMenu.classList.add('hidden');
        });
    });
}

// Настройка переключателя периода
function setupPeriodSwitcher() {
    const periodBtns = document.querySelectorAll('.period-btn');
    
    periodBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Убираем активный класс у всех кнопок
            periodBtns.forEach(b => {
                b.classList.remove('bg-gray-700', 'text-white');
                b.classList.add('bg-white', 'text-gray-700', 'hover:bg-gray-100');
            });
            
            // Добавляем активный класс выбранной кнопке
            this.classList.remove('bg-white', 'text-gray-700', 'hover:bg-gray-100');
            this.classList.add('bg-gray-700', 'text-white');
            
            // Обновляем текущий период и загружаем данные
            currentPeriod = this.dataset.period;
            loadFinanceSummary();
            updateDateRange();
        });
    });
}

// Обновление диапазона дат
function updateDateRange() {
    const dateRange = document.getElementById('date-range');
    const now = new Date();
    let startDate, endDate;
    
    switch (currentPeriod) {
        case 'day':
            const options = { day: 'numeric', month: 'long', year: 'numeric' };
            dateRange.textContent = now.toLocaleDateString('ru-RU', options);
            break;
        case 'week':
            // Находим начало и конец текущей недели (понедельник-пятница)
            const day = now.getDay();
            const diff = day === 0 ? 6 : day - 1; // Преобразуем воскресенье в 6, остальные дни смещаем
            startDate = new Date(now);
            startDate.setDate(now.getDate() - diff);
            endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 4); // +4 дня для Пт
            
            dateRange.textContent = `${startDate.getDate()} ${getMonthName(startDate)} - ${endDate.getDate()} ${getMonthName(endDate)} ${endDate.getFullYear()}`;
            break;
        case 'month':
            // Текущий месяц
            const monthName = getMonthName(now);
            dateRange.textContent = `1 ${monthName} - ${getDaysInMonth(now.getFullYear(), now.getMonth()+1)} ${monthName} ${now.getFullYear()}`;
            break;
        case 'year':
            // Текущий год
            dateRange.textContent = now.getFullYear().toString();
            break;
    }
}

// Получение названия месяца
function getMonthName(date) {
    const monthNames = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
    return monthNames[date.getMonth()];
}

// Получение количества дней в месяце
function getDaysInMonth(year, month) {
    return new Date(year, month, 0).getDate();
}

// Загрузка финансовой сводки
async function loadFinanceSummary() {
    try {
        // Показываем индикатор загрузки
        document.getElementById('stats-loading').classList.remove('hidden');
        document.getElementById('stats-cards').classList.add('hidden');
        document.getElementById('chart-loading').classList.remove('hidden');
        
        // Параметры запроса
        let params = {};
        if (currentPeriod === 'day') {
            const today = new Date().toISOString().slice(0, 10);
            params.date_from = today;
            params.date_to = today;
        } else if (currentPeriod === 'week') {
            const now = new Date();
            const day = now.getDay();
            const diff = day === 0 ? 6 : day - 1;
            const startDate = new Date(now);
            startDate.setDate(now.getDate() - diff);
            const endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 4);
            
            params.date_from = startDate.toISOString().slice(0, 10);
            params.date_to = endDate.toISOString().slice(0, 10);
        } else if (currentPeriod === 'month') {
            const now = new Date();
            const startDate = new Date(now.getFullYear(), now.getMonth(), 1);
            const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
            
            params.date_from = startDate.toISOString().slice(0, 10);
            params.date_to = endDate.toISOString().slice(0, 10);
        } else if (currentPeriod === 'year') {
            const now = new Date();
            const startDate = new Date(now.getFullYear(), 0, 1);
            const endDate = new Date(now.getFullYear(), 11, 31);
            
            params.date_from = startDate.toISOString().slice(0, 10);
            params.date_to = endDate.toISOString().slice(0, 10);
        }
        
        // Формируем URL с параметрами
        const queryParams = new URLSearchParams(params);
        const url = `${API_BASE_URL}/finance/summary?${queryParams}`;
        
        // Запрос к API
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Обновляем карточки статистики
        document.getElementById('total-revenue').textContent = formatCurrency(data.total_revenue);
        
        // Получаем активные заказы
        const ordersResponse = await fetch(`${API_BASE_URL}/orders?status=в работе&limit=1`);
        if (ordersResponse.ok) {
            const ordersData = await ordersResponse.json();
            document.getElementById('active-orders').textContent = ordersData.total_count;
        }
        
        // Получаем новых клиентов за период
        const clientsResponse = await fetch(`${API_BASE_URL}/clients?${queryParams}&limit=1`);
        if (clientsResponse.ok) {
            const clientsData = await clientsResponse.json();
            document.getElementById('new-clients').textContent = clientsData.total_count;
        }
        
        // Получаем количество монтажей за период
        document.getElementById('total-installations').textContent = data.installations_count || 0;
        
        // Обновляем изменения с прошлым периодом
        updateChangeIndicator('revenue-change', data.revenue_change || 2.5);
        updateChangeIndicator('orders-change', data.orders_change || 1.7);
        updateChangeIndicator('clients-change', data.clients_change || -2.9);
        updateChangeIndicator('installations-change', data.installations_change || 3.2);
        
        // Обновляем график выручки
        updateRevenueChart(data.monthly_revenue || generateMockRevenueData());
        
        // Обновляем процент конверсии
        updateConversionChart(data.conversion_rate || 78, data.conversion_change || 2.1);
        
        // Скрываем индикатор загрузки и показываем карточки
        document.getElementById('stats-loading').classList.add('hidden');
        document.getElementById('stats-cards').classList.remove('hidden');
        document.getElementById('chart-loading').classList.add('hidden');
    } catch (error) {
        console.error('Ошибка при загрузке финансовой сводки:', error);
        showNotification('Ошибка при загрузке данных', 'error');
        
        // Убираем индикаторы загрузки и показываем карточки с дефолтными данными
        document.getElementById('stats-loading').classList.add('hidden');
        document.getElementById('stats-cards').classList.remove('hidden');
        document.getElementById('chart-loading').classList.add('hidden');
    }
}

// Обновление индикатора изменения
function updateChangeIndicator(elementId, changeValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Очищаем предыдущее содержимое
    element.innerHTML = '';
    
    // Создаем иконку стрелки
    const icon = document.createElement('i');
    icon.classList.add('fas', 'mr-1');
    
    // Определяем класс и иконку в зависимости от значения
    if (changeValue > 0) {
        icon.classList.add('fa-arrow-up');
        element.classList.add('text-green-500');
        element.classList.remove('text-red-500', 'text-gray-500');
    } else if (changeValue < 0) {
        icon.classList.add('fa-arrow-down');
        element.classList.add('text-red-500');
        element.classList.remove('text-green-500', 'text-gray-500');
    } else {
        icon.classList.add('fa-minus');
        element.classList.add('text-gray-500');
        element.classList.remove('text-green-500', 'text-red-500');
    }
    
    // Добавляем иконку
    element.appendChild(icon);
    
    // Добавляем текст
    const span = document.createElement('span');
    span.textContent = `${Math.abs(changeValue).toFixed(1)}% от прошлого ${getPeriodName()}`;
    element.appendChild(span);
}

// Получение названия периода в родительном падеже
function getPeriodName() {
    switch (currentPeriod) {
        case 'day': return 'дня';
        case 'week': return 'недели';
        case 'month': return 'месяца';
        case 'year': return 'года';
        default: return 'периода';
    }
}

// Обновление графика выручки
function updateRevenueChart(data) {
    // Если данные не предоставлены, используем моки
    if (!data || !Array.isArray(data) || data.length === 0) {
        data = generateMockRevenueData();
    }
    
    // Получаем контекст canvas
    const ctx = document.getElementById('revenue-chart-canvas').getContext('2d');
    
    // Если график уже существует, уничтожаем его
    if (revenueChart) {
        revenueChart.destroy();
    }
    
    // Генерируем метки в зависимости от периода
    const labels = generateLabels();
    
    // Создаем новый график
    revenueChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Выручка',
                data: data,
                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value, true);
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.raw);
                        }
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
}

// Генерирование меток в зависимости от периода
function generateLabels() {
    switch (currentPeriod) {
        case 'day':
            return ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'];
        case 'week':
            return ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'];
        case 'month':
            return ['1 нед', '2 нед', '3 нед', '4 нед'];
        case 'year':
            return ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
        default:
            return ['1', '2', '3', '4', '5', '6'];
    }
}

// Генерация тестовых данных для графика выручки
function generateMockRevenueData() {
    const data = [];
    const labels = generateLabels();
    
    for (let i = 0; i < labels.length; i++) {
        data.push(Math.floor(Math.random() * 50000) + 10000);
    }
    
    return data;
}

// Обновление графика конверсии
function updateConversionChart(value, change) {
    // Устанавливаем текст процента
    document.getElementById('conversion-percent').textContent = `${value}%`;
    
    // Обновляем изменение
    const conversionChange = document.getElementById('conversion-change');
    conversionChange.innerHTML = '';
    
    const icon = document.createElement('i');
    icon.classList.add('fas', 'mr-1');
    
    if (change > 0) {
        icon.classList.add('fa-arrow-up');
        conversionChange.classList.add('text-green-500');
        conversionChange.classList.remove('text-red-500', 'text-gray-500');
    } else if (change < 0) {
        icon.classList.add('fa-arrow-down');
        conversionChange.classList.add('text-red-500');
        conversionChange.classList.remove('text-green-500', 'text-gray-500');
    } else {
        icon.classList.add('fa-minus');
        conversionChange.classList.add('text-gray-500');
        conversionChange.classList.remove('text-green-500', 'text-red-500');
    }
    
    conversionChange.appendChild(icon);
    
    const span = document.createElement('span');
    span.textContent = `${Math.abs(change).toFixed(1)}% от прошлого ${getPeriodName()}`;
    conversionChange.appendChild(span);
    
    // Получаем контекст canvas
    const ctx = document.getElementById('conversion-chart-canvas').getContext('2d');
    
    // Если график уже существует, уничтожаем его
    if (conversionChart) {
        conversionChart.destroy();
    }
    
    // Создаем новый график (круговой)
    conversionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Конверсия', 'Не конвертировано'],
            datasets: [{
                data: [value, 100 - value],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(229, 231, 235, 0.5)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '75%',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        }
    });
}

// Загрузка последних заказов
async function loadRecentOrders() {
    try {
        document.getElementById('orders-loading').classList.remove('hidden');
        document.getElementById('orders-table-container').classList.add('hidden');
        
        // Запрос к API
        const response = await fetch(`${API_BASE_URL}/orders?limit=5`);
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Заполняем таблицу заказов
        const tableBody = document.getElementById('orders-table-body');
        tableBody.innerHTML = '';
        
        if (data.orders && data.orders.length > 0) {
            data.orders.forEach(order => {
                const row = document.createElement('tr');
                row.className = 'hover:bg-gray-50';
                
                // Определяем основную услугу (первая в списке или монтаж)
                let mainService = "Монтаж";
                if (order.services && order.services.length > 0) {
                    mainService = order.services[0].name;
                }
                
                // Определяем класс для статуса
                let statusClass = '';
                switch (order.status) {
                    case 'новый':
                        statusClass = 'status-pending';
                        break;
                    case 'в работе':
                        statusClass = 'status-processing';
                        break;
                    case 'завершен':
                        statusClass = 'status-completed';
                        break;
                    case 'отменен':
                        statusClass = 'status-canceled';
                        break;
                }
                
                row.innerHTML = `
                    <td class="py-3 px-4 md:px-6 font-medium">
                        <div class="flex items-center">
                            <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3 text-blue-600">
                                <i class="fas fa-snowflake"></i>
                            </div>
                            <div>
                                <div class="font-medium">${mainService}</div>
                                <div class="text-xs text-gray-500">${formatDate(order.order_date)}</div>
                            </div>
                        </div>
                    </td>
                    <td class="py-3 px-4 md:px-6">
                        ${order.client ? order.client.name : '-'}
                    </td>
                    <td class="py-3 px-4 md:px-6 hidden md:table-cell">#${order.id}</td>
                    <td class="py-3 px-4 md:px-6 font-medium">${formatCurrency(order.total_price)}</td>
                    <td class="py-3 px-4 md:px-6">
                        <span class="status-pill ${statusClass}">${order.status}</span>
                    </td>
                `;
                
                tableBody.appendChild(row);
            });
        } else {
            // Если заказов нет
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="5" class="py-4 text-center text-gray-500">Нет заказов</td>
            `;
            tableBody.appendChild(row);
        }
        
        document.getElementById('orders-loading').classList.add('hidden');
        document.getElementById('orders-table-container').classList.remove('hidden');
    } catch (error) {
        console.error('Ошибка при загрузке заказов:', error);
        showNotification('Ошибка при загрузке заказов', 'error');
        
        // Показываем таблицу с сообщением об ошибке
        const tableBody = document.getElementById('orders-table-body');
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="py-4 text-center text-gray-500">Ошибка при загрузке заказов</td>
            </tr>
        `;
        
        document.getElementById('orders-loading').classList.add('hidden');
        document.getElementById('orders-table-container').classList.remove('hidden');
    }
}

// Инициализация календаря
function initCalendar() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    
    // Получаем первый день месяца
    const firstDay = new Date(year, month, 1);
    
    // Получаем последний день месяца
    const lastDay = new Date(year, month + 1, 0);
    
    // Получаем день недели для первого дня (0 - воскресенье, 1 - понедельник, и т.д.)
    let firstDayOfWeek = firstDay.getDay();
    // Преобразуем воскресенье (0) в 7, чтобы корректно отображать в календаре, где неделя начинается с понедельника
    if (firstDayOfWeek === 0) firstDayOfWeek = 7;
    
    // Корректируем, так как в нашем календаре неделя начинается с понедельника (1)
    const offset = firstDayOfWeek - 1;
    
    const calendarGrid = document.getElementById('calendar-grid');
    
    // Очищаем предыдущий календарь, оставляя заголовки дней недели
    const headers = calendarGrid.querySelectorAll('.text-gray-400');
    calendarGrid.innerHTML = '';
    headers.forEach(header => calendarGrid.appendChild(header));
    
    // Добавляем пустые ячейки для дней до начала месяца
    for (let i = 0; i < offset; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'text-center py-1';
        calendarGrid.appendChild(emptyCell);
    }
    
    // Добавляем дни месяца
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const date = new Date(year, month, day);
        const cell = document.createElement('div');
        
        // Если день уже в прошлом, делаем его неактивным
        const isToday = day === now.getDate();
        
        if (isToday) {
            cell.className = 'text-center py-1 font-bold bg-blue-100 rounded text-blue-600';
        } else {
            cell.className = 'text-center py-1 hover:bg-gray-100 cursor-pointer';
        }
        
        cell.textContent = day;
        
        // Добавляем метки для дней с заказами (упрощенно)
        if (day % 3 === 0) {  // Для примера, каждый третий день имеет заказы
            const dot = document.createElement('div');
            dot.className = 'mx-auto mt-1 w-1 h-1 bg-green-500 rounded-full';
            cell.appendChild(dot);
        }
        
        calendarGrid.appendChild(cell);
    }
}

// Форматирование валюты
function formatCurrency(value, short = false) {
    if (!value && value !== 0) return '₽ 0';
    
    // Для больших чисел в кратком формате используем сокращения К и М
    if (short && value >= 1000) {
        if (value >= 1000000) {
            return `₽ ${(value / 1000000).toFixed(1)}M`;
        } else {
            return `₽ ${(value / 1000).toFixed(0)}K`;
        }
    }
    
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

// Форматирование даты
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short'
    });
}

// Показать уведомление
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const content = document.getElementById('notification-content');
    
    // Устанавливаем класс в зависимости от типа уведомления
    notification.className = 'notification fixed top-4 right-4 max-w-xs bg-white shadow-lg rounded-lg overflow-hidden z-50';
    
    if (type === 'error') {
        content.className = 'p-4 bg-red-50 border-l-4 border-red-500 text-red-700';
        content.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i> ${message}`;
    } else if (type === 'warning') {
        content.className = 'p-4 bg-yellow-50 border-l-4 border-yellow-500 text-yellow-700';
        content.innerHTML = `<i class="fas fa-exclamation-triangle mr-2"></i> ${message}`;
    } else {
        content.className = 'p-4 bg-green-50 border-l-4 border-green-500 text-green-700';
        content.innerHTML = `<i class="fas fa-check-circle mr-2"></i> ${message}`;
    }
    
    // Показываем уведомление
    notification.classList.remove('hidden');
    
    // Скрываем через 3 секунды
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}