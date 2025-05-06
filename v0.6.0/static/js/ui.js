// Обработка переключения пунктов меню
function setupMenuNavigation() {
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Убираем активный класс со всех пунктов
            menuItems.forEach(menuItem => {
                menuItem.classList.remove('active');
                menuItem.classList.add('text-gray-700');
            });
            
            // Устанавливаем активный класс текущему пункту
            this.classList.add('active');
            this.classList.remove('text-gray-700');
            
            // Получаем имя страницы
            const pageName = this.dataset.page;
            
            // Здесь может быть навигация между страницами
            // В реальном SPA-приложении здесь бы был код для загрузки нужной страницы
            console.log(`Переход на страницу: ${pageName}`);
            
            // Можно было бы использовать History API для изменения URL без перезагрузки
            // history.pushState(null, null, `/${pageName}`);
        });
    });
}

// Обработка переключения периодов
function setupPeriodSwitching(callback) {
    document.querySelectorAll('.period-btn').forEach(button => {
        button.addEventListener('click', function() {
            // Убрать активный класс со всех кнопок
            document.querySelectorAll('.period-btn').forEach(btn => {
                btn.classList.remove('bg-gray-700', 'text-white');
                btn.classList.add('bg-white', 'text-gray-700');
            });
            
            // Добавить активный класс на текущую кнопку
            this.classList.remove('bg-white', 'text-gray-700');
            this.classList.add('bg-gray-700', 'text-white');
            
            // Обновляем диапазон дат в зависимости от выбранного периода
            updateDateRange(this.dataset.period);
            
            // Вызываем колбэк с выбранным периодом
            if (typeof callback === 'function') {
                callback(this.dataset.period);
            }
        });
    });
}

// Обновление отображаемого диапазона дат
function updateDateRange(period) {
    const dateRangeElement = document.getElementById('date-range');
    if (!dateRangeElement) return;
    
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    
    let startDate, endDate;
    
    switch(period) {
        case 'day':
            startDate = endDate = now;
            dateRangeElement.textContent = formatDate(now);
            break;
        case 'week':
            startDate = new Date(now);
            startDate.setDate(now.getDate() - now.getDay() + 1);
            endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 6);
            dateRangeElement.textContent = `${formatDate(startDate)} - ${formatDate(endDate)}`;
            break;
        case 'month':
            startDate = new Date(year, month, 1);
            endDate = new Date(year, month + 1, 0);
            dateRangeElement.textContent = `1 ${getMonthName(month)} ${year} - ${endDate.getDate()} ${getMonthName(month)} ${year}`;
            break;
        case 'year':
            startDate = new Date(year, 0, 1);
            endDate = new Date(year, 11, 31);
            dateRangeElement.textContent = `1 Янв ${year} - 31 Дек ${year}`;
            break;
    }
}

// Получение названия месяца
function getMonthName(monthIndex) {
    const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
    return months[monthIndex];
}

// Инициализация пользовательского интерфейса
function initUI() {
    setupMenuNavigation();
    setupPeriodSwitching();
    
    // Инициализация поиска
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                console.log('Поиск:', this.value);
                // Здесь бы был код для выполнения поиска
            }
        });
    }
    
    // Инициализация уведомлений
    const notificationBtn = document.getElementById('notification-btn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            showNotification('У вас нет новых уведомлений');
        });
    }
}

// Вызываем инициализацию при загрузке страницы
document.addEventListener('DOMContentLoaded', initUI);