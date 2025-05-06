// Функция для загрузки последних заказов
async function loadRecentOrders() {
    try {
        // Показываем индикатор загрузки
        const loadingElement = document.getElementById('orders-loading');
        const tableContainer = document.getElementById('orders-table-container');
        
        if (loadingElement) loadingElement.classList.remove('hidden');
        if (tableContainer) tableContainer.classList.add('hidden');
        
        // Загружаем данные
        const data = await fetchWithErrorHandling(`${API_BASE_URL}/orders?limit=4`);
        
        // Заполняем таблицу заказов
        const tableBody = document.getElementById('orders-table-body');
        if (tableBody) {
            tableBody.innerHTML = '';
            
            data.orders.forEach(order => {
                const row = document.createElement('tr');
                row.className = 'hover:bg-gray-50';
                
                row.innerHTML = `
                    <td class="py-4 px-6">
                        <div class="flex items-center">
                            <div class="h-10 w-10 flex-shrink-0 bg-gray-200 rounded mr-3"></div>
                            <span>${order.service}</span>
                        </div>
                    </td>
                    <td class="py-4 px-6">${order.client}</td>
                    <td class="py-4 px-6 text-gray-500">#${order.id}</td>
                    <td class="py-4 px-6 font-medium">${formatCurrency(order.total_price)}</td>
                    <td class="py-4 px-6">
                        <span class="status-pill status-${order.status_color}">${order.status}</span>
                    </td>
                `;
                
                tableBody.appendChild(row);
            });
        }
        
        // Скрываем индикатор загрузки
        if (loadingElement) loadingElement.classList.add('hidden');
        if (tableContainer) tableContainer.classList.remove('hidden');
        
        // Обработчик для кнопки обновления
        const refreshButton = document.getElementById('refresh-orders');
        if (refreshButton) {
            refreshButton.addEventListener('click', function() {
                this.querySelector('i').classList.add('fa-spin');
                
                // Перезагружаем заказы
                setTimeout(() => {
                    loadRecentOrders().then(() => {
                        this.querySelector('i').classList.remove('fa-spin');
                        showNotification('Данные заказов обновлены', 'success');
                    });
                }, 500);
            });
        }
        
    } catch (error) {
        console.error('Ошибка при загрузке заказов:', error);
    }
}