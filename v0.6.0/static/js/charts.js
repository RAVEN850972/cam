// Функция для обновления графика выручки
function updateRevenueChart(data) {
    const chartContainer = document.getElementById('chart-bars');
    const labelsContainer = document.getElementById('chart-labels');
    
    if (!chartContainer || !labelsContainer) return;
    
    // Очищаем содержимое
    chartContainer.innerHTML = '';
    labelsContainer.innerHTML = '';
    
    // Названия месяцев
    const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
    
    // Находим максимальное значение для масштабирования
    const maxValue = Math.max(...data);
    
    // Добавляем столбцы графика
    data.forEach((value, index) => {
        // Рассчитываем высоту столбца (в процентах от максимального значения)
        const height = Math.round((value / maxValue) * 80);
        
        // Создаем столбец
        const bar = document.createElement('div');
        bar.className = 'chart-bar bg-blue-500 rounded-t-lg';
        bar.style.height = '0%';
        bar.style.width = `${90 / data.length}%`;
        
        // Добавляем столбец в контейнер
        chartContainer.appendChild(bar);
        
        // Добавляем метку месяца
        const label = document.createElement('div');
        label.textContent = months[index];
        labelsContainer.appendChild(label);
        
        // Анимируем высоту столбца
        setTimeout(() => {
            bar.style.height = `${height}%`;
        }, 100 + index * 100);
    });
    
    // Скрываем индикатор загрузки
    document.getElementById('chart-loading')?.classList.add('hidden');
}

// Функция для обновления круговой диаграммы конверсии
function updateConversionChart(percentage, change) {
    // Обновляем процент конверсии
    const percentElement = document.getElementById('conversion-percent');
    if (percentElement) {
        percentElement.textContent = `${percentage}%`;
    }
    
    // Обновляем круговую диаграмму
    const circleElement = document.getElementById('conversion-circle');
    if (circleElement) {
        // Устанавливаем процент заполнения круга
        circleElement.setAttribute('stroke-dasharray', `${percentage}, 100`);
    }
    
    // Обновляем изменение с прошлого периода
    updateChangeIndicator('conversion-change', change);
}

// Функция для инициализации календаря с отмеченными днями
function initCalendar() {
    const calendarGrid = document.getElementById('calendar-grid');
    if (!calendarGrid) return;
    
    // Добавляем заголовки дней недели (у нас уже есть первые 5 дней в HTML)
    
    // Текущий месяц и год
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();
    
    // Первый день месяца
    const firstDay = new Date(currentYear, currentMonth, 1);
    const firstDayWeekday = firstDay.getDay() || 7; // 1-7 (пн-вс)
    
    // Количество дней в месяце
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    
    // Дни с заказами (для демонстрации)
    const daysWithOrders = [4, 8, 12, 15, 19, 23, 27];
    
    // Добавляем пустые ячейки до первого дня месяца
    for (let i = 1; i < firstDayWeekday; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'py-2';
        calendarGrid.appendChild(emptyCell);
    }
    
    // Добавляем дни месяца
    for (let day = 1; day <= daysInMonth; day++) {
        const dayCell = document.createElement('div');
        dayCell.textContent = day;
        dayCell.className = 'py-2';
        
        // Выделяем дни с заказами
        if (daysWithOrders.includes(day)) {
            dayCell.classList.add('bg-blue-100', 'rounded-lg');
        }
        
        // Выделяем текущий день
        if (day === now.getDate()) {
            dayCell.classList.add('font-bold', 'border', 'border-blue-500');
        }
        
        calendarGrid.appendChild(dayCell);
    }
    
    // Обработчики для кнопок переключения месяцев
    document.getElementById('prev-month')?.addEventListener('click', () => {
        console.log('Переключение на предыдущий месяц');
    });
    
    document.getElementById('next-month')?.addEventListener('click', () => {
        console.log('Переключение на следующий месяц');
    });
}