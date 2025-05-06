# API-документация CRM-системы для бизнеса по установке кондиционеров

Данная документация описывает доступные API-endpoints для работы с CRM-системой компании по установке кондиционеров.

## Базовая информация

**Базовый URL**: `http://localhost:8000`  
**Формат данных**: JSON  
**Аутентификация**: Не требуется в текущей версии

## Содержание

1. [Сотрудники](#1-сотрудники)
2. [Клиенты](#2-клиенты)
3. [Услуги](#3-услуги)
4. [Заказы](#4-заказы)
5. [Финансы](#5-финансы)
6. [Экспорт данных](#6-экспорт-данных)

---

## 1. Сотрудники

### 1.1 Получение списка сотрудников

```
GET /api/employees
```

**Параметры запроса:**
- `employee_type` (опционально): тип сотрудника (менеджер, монтажник, владелец)
- `active` (опционально): статус сотрудника (1 - активный, 0 - неактивный)
- `page` (опционально, по умолчанию 1): страница
- `limit` (опционально, по умолчанию 20): количество записей на странице

**Пример ответа:**
```json
{
  "employees": [
    {
      "id": 1,
      "name": "Иван Иванов",
      "phone": "+79001234567",
      "employee_type": "менеджер",
      "base_salary": 30000,
      "active": 1,
      "created_at": "2023-01-15",
      "updated_at": "2023-02-20"
    }
  ],
  "total_count": 1,
  "page": 1,
  "total_pages": 1,
  "limit": 20
}
```

### 1.2 Получение информации о сотруднике

```
GET /api/employees/{employee_id}
```

**Параметры пути:**
- `employee_id`: ID сотрудника

**Пример ответа:**
```json
{
  "id": 1,
  "name": "Иван Иванов",
  "phone": "+79001234567",
  "employee_type": "менеджер",
  "base_salary": 30000,
  "active": 1,
  "created_at": "2023-01-15",
  "updated_at": "2023-02-20"
}
```

### 1.3 Создание нового сотрудника

```
POST /api/employees
```

**Тело запроса:**
```json
{
  "name": "Петр Петров",
  "phone": "+79001234568",
  "employee_type": "монтажник",
  "base_salary": null
}
```

**Пример ответа:**
```json
{
  "id": 2,
  "name": "Петр Петров",
  "phone": "+79001234568",
  "employee_type": "монтажник",
  "base_salary": null,
  "active": 1,
  "created_at": "2023-05-03",
  "updated_at": null
}
```

### 1.4 Обновление данных сотрудника

```
PUT /api/employees/{employee_id}
```

**Параметры пути:**
- `employee_id`: ID сотрудника

**Тело запроса:**
```json
{
  "name": "Петр Иванович Петров",
  "phone": "+79001234569"
}
```

**Пример ответа:**
```json
{
  "id": 2,
  "name": "Петр Иванович Петров",
  "phone": "+79001234569",
  "employee_type": "монтажник",
  "base_salary": null,
  "active": 1,
  "created_at": "2023-05-03",
  "updated_at": "2023-05-03"
}
```

### 1.5 Деактивация сотрудника

```
PUT /api/employees/{employee_id}/deactivate
```

**Параметры пути:**
- `employee_id`: ID сотрудника

**Пример ответа:**
```json
{
  "id": 2,
  "name": "Петр Иванович Петров",
  "phone": "+79001234569",
  "employee_type": "монтажник",
  "base_salary": null,
  "active": 0,
  "created_at": "2023-05-03",
  "updated_at": "2023-05-03"
}
```

### 1.6 Получение зарплаты сотрудника

```
GET /api/employees/{employee_id}/salary
```

**Параметры пути:**
- `employee_id`: ID сотрудника

**Параметры запроса:**
- `month` (опционально): месяц в формате "YYYY-MM"

**Пример ответа:**
```json
{
  "employee": {
    "id": 1,
    "name": "Иван Иванов",
    "type": "менеджер"
  },
  "salary": 35750,
  "paid": 20000,
  "to_pay": 15750,
  "details": {
    "base_salary": 30000,
    "order_payments": 1250,
    "additional_commission": 3000,
    "ac_commission": 1500,
    "breakdown": {
      "orders": [
        {
          "id": 1,
          "date": "2023-05-01 10:00",
          "amount": 250,
          "type": "Менеджер - фиксированная ставка"
        }
      ],
      "payments": [
        {
          "id": 1,
          "date": "2023-05-15",
          "amount": 20000,
          "description": "Аванс"
        }
      ]
    }
  },
  "month": "2023-05"
}
```

### 1.7 Выплата сотруднику

```
POST /api/employees/{employee_id}/pay
```

**Параметры пути:**
- `employee_id`: ID сотрудника

**Форма (Form Data):**
- `amount`: сумма выплаты
- `description` (опционально): описание выплаты

**Пример ответа:**
```json
{
  "success": true,
  "id": 2
}
```

---

## 2. Клиенты

### 2.1 Получение списка клиентов

```
GET /api/clients
```

**Параметры запроса:**
- `search` (опционально): поиск по имени или телефону
- `source` (опционально): источник клиента
- `page` (опционально, по умолчанию 1): страница
- `limit` (опционально, по умолчанию 20): количество записей на странице

**Пример ответа:**
```json
{
  "clients": [
    {
      "id": 1,
      "name": "Алексей Смирнов",
      "phone": "+79001234570",
      "source": "Авито",
      "created_at": "2023-04-10",
      "updated_at": null,
      "order_count": 2
    }
  ],
  "total_count": 1,
  "page": 1,
  "total_pages": 1,
  "limit": 20
}
```

### 2.2 Получение информации о клиенте

```
GET /api/clients/{client_id}
```

**Параметры пути:**
- `client_id`: ID клиента

**Пример ответа:**
```json
{
  "id": 1,
  "name": "Алексей Смирнов",
  "phone": "+79001234570",
  "source": "Авито",
  "created_at": "2023-04-10",
  "updated_at": null,
  "order_count": 2,
  "orders": [
    {
      "id": 1,
      "order_date": "2023-05-01 10:00",
      "status": "завершен",
      "mount_price": 10000
    },
    {
      "id": 2,
      "order_date": "2023-05-15 14:30",
      "status": "в работе",
      "mount_price": 12000
    }
  ]
}
```

### 2.3 Создание нового клиента

```
POST /api/clients
```

**Тело запроса:**
```json
{
  "name": "Мария Иванова",
  "phone": "+79001234571",
  "source": "ВК"
}
```

**Пример ответа:**
```json
{
  "id": 2,
  "name": "Мария Иванова",
  "phone": "+79001234571",
  "source": "ВК",
  "created_at": "2023-05-03",
  "updated_at": null
}
```

### 2.4 Обновление данных клиента

```
PUT /api/clients/{client_id}
```

**Параметры пути:**
- `client_id`: ID клиента

**Тело запроса:**
```json
{
  "name": "Мария Ивановна Иванова",
  "source": "Рекомендации"
}
```

**Пример ответа:**
```json
{
  "id": 2,
  "name": "Мария Ивановна Иванова",
  "phone": "+79001234571",
  "source": "Рекомендации",
  "created_at": "2023-05-03",
  "updated_at": "2023-05-03"
}
```

### 2.5 Удаление клиента

```
DELETE /api/clients/{client_id}
```

**Параметры пути:**
- `client_id`: ID клиента

**Пример ответа:**
```json
{
  "success": true
}
```

### 2.6 Получение статистики по источникам

```
GET /api/clients/stats/by-source
```

**Пример ответа:**
```json
{
  "Авито": 10,
  "ВК": 5,
  "Яндекс услуги": 8,
  "Листовки": 2,
  "Рекомендации": 15,
  "Другое": 3
}
```

---

## 3. Услуги

### 3.1 Получение списка услуг

```
GET /api/services
```

**Параметры запроса:**
- `search` (опционально): поиск по названию
- `category` (опционально): категория услуги
- `page` (опционально, по умолчанию 1): страница
- `limit` (опционально, по умолчанию 20): количество записей на странице

**Пример ответа:**
```json
{
  "services": [
    {
      "id": 1,
      "name": "Стандартный монтаж",
      "category": "Монтаж",
      "purchase_price": 0,
      "selling_price": 10000,
      "default_price": 10000,
      "is_manager_bonus": false,
      "installer_bonus_fixed": 250,
      "profit_margin_percent": 0.3,
      "created_at": "2023-01-01",
      "updated_at": null,
      "total_usage": 15
    }
  ],
  "total_count": 1,
  "page": 1,
  "total_pages": 1,
  "limit": 20
}
```

### 3.2 Получение информации об услуге

```
GET /api/services/{service_id}
```

**Параметры пути:**
- `service_id`: ID услуги

**Пример ответа:**
```json
{
  "id": 1,
  "name": "Стандартный монтаж",
  "category": "Монтаж",
  "purchase_price": 0,
  "selling_price": 10000,
  "default_price": 10000,
  "is_manager_bonus": false,
  "installer_bonus_fixed": 250,
  "profit_margin_percent": 0.3,
  "created_at": "2023-01-01",
  "updated_at": null,
  "total_usage": 15,
  "usage_details": {
    "main_service": 15,
    "additional_service": 0
  }
}
```

### 3.3 Создание новой услуги

```
POST /api/services
```

**Тело запроса:**
```json
{
  "name": "Кондиционер MDV",
  "category": "Кондиционер",
  "purchase_price": 15000,
  "selling_price": 25000,
  "is_manager_bonus": false,
  "profit_margin_percent": 0.4
}
```

**Пример ответа:**
```json
{
  "id": 2,
  "name": "Кондиционер MDV",
  "category": "Кондиционер",
  "purchase_price": 15000,
  "selling_price": 25000,
  "default_price": null,
  "is_manager_bonus": false,
  "installer_bonus_fixed": 250,
  "profit_margin_percent": 0.4,
  "created_at": "2023-05-03",
  "updated_at": null
}
```

### 3.4 Обновление данных услуги

```
PUT /api/services/{service_id}
```

**Параметры пути:**
- `service_id`: ID услуги

**Тело запроса:**
```json
{
  "name": "Кондиционер MDV 12",
  "purchase_price": 16000,
  "selling_price": 26000
}
```

**Пример ответа:**
```json
{
  "id": 2,
  "name": "Кондиционер MDV 12",
  "category": "Кондиционер",
  "purchase_price": 16000,
  "selling_price": 26000,
  "default_price": null,
  "is_manager_bonus": false,
  "installer_bonus_fixed": 250,
  "profit_margin_percent": 0.4,
  "created_at": "2023-05-03",
  "updated_at": "2023-05-03"
}
```

### 3.5 Удаление услуги

```
DELETE /api/services/{service_id}
```

**Параметры пути:**
- `service_id`: ID услуги

**Пример ответа:**
```json
{
  "success": true
}
```

### 3.6 Получение статистики по категориям

```
GET /api/services/stats/by-category
```

**Пример ответа:**
```json
{
  "Монтаж": {
    "count": 3,
    "avg_price": 11000
  },
  "Кондиционер": {
    "count": 10,
    "avg_price": 25000
  },
  "Монтажный комплект": {
    "count": 2,
    "avg_price": 3000
  },
  "Виброопора": {
    "count": 1,
    "avg_price": 1500
  },
  "Доп услуга": {
    "count": 5,
    "avg_price": 2000
  }
}
```

---

## 4. Заказы

### 4.1 Получение списка заказов

```
GET /api/orders
```

**Параметры запроса:**
- `status` (опционально): статус заказа
- `client_name` (опционально): имя клиента
- `date_from` (опционально): дата начала периода
- `date_to` (опционально): дата окончания периода
- `page` (опционально, по умолчанию 1): страница
- `limit` (опционально, по умолчанию 10): количество записей на странице

**Пример ответа:**
```json
{
  "orders": [
    {
      "id": 1,
      "client": {
        "id": 1,
        "name": "Алексей Смирнов",
        "phone": "+79001234570"
      },
      "manager": {
        "id": 1,
        "name": "Иван Иванов"
      },
      "order_date": "2023-05-01 10:00",
      "completion_date": "2023-05-02 15:30",
      "status": "завершен",
      "notes": "Стандартный монтаж",
      "mount_price": 10000,
      "owner_commission": 1500,
      "employees": [
        {
          "id": 2,
          "name": "Петр Петров",
          "employee_type": "монтажник",
          "base_payment": 1500
        }
      ],
      "services": [
        {
          "id": 2,
          "name": "Кондиционер MDV",
          "category": "Кондиционер",
          "selling_price": 25000,
          "is_manager_bonus": false,
          "sold_by": {
            "id": 1,
            "name": "Иван Иванов"
          }
        }
      ],
      "total_price": 35000,
      "created_at": "2023-05-01",
      "updated_at": "2023-05-02"
    }
  ],
  "total_count": 1,
  "page": 1,
  "total_pages": 1,
  "limit": 10
}
```

### 4.2 Получение информации о заказе

```
GET /api/orders/{order_id}
```

**Параметры пути:**
- `order_id`: ID заказа

**Пример ответа:**
```json
{
  "id": 1,
  "client": {
    "id": 1,
    "name": "Алексей Смирнов",
    "phone": "+79001234570"
  },
  "manager": {
    "id": 1,
    "name": "Иван Иванов"
  },
  "order_date": "2023-05-01 10:00",
  "completion_date": "2023-05-02 15:30",
  "status": "завершен",
  "notes": "Стандартный монтаж",
  "mount_price": 10000,
  "owner_commission": 1500,
  "employees": [
    {
      "id": 2,
      "name": "Петр Петров",
      "employee_type": "монтажник",
      "base_payment": 1500
    }
  ],
  "services": [
    {
      "id": 2,
      "name": "Кондиционер MDV",
      "category": "Кондиционер",
      "selling_price": 25000,
      "is_manager_bonus": false,
      "sold_by": {
        "id": 1,
        "name": "Иван Иванов"
      }
    }
  ],
  "total_price": 35000,
  "created_at": "2023-05-01",
  "updated_at": "2023-05-02"
}
```

### 4.3 Создание нового заказа

```
POST /api/orders
```

**Тело запроса:**
```json
{
  "client_id": 1,
  "manager_id": 1,
  "order_date": "2023-05-03 11:00",
  "status": "новый",
  "mount_price": 12000,
  "notes": "Сложный монтаж на высоте",
  "services": [
    {
      "service_id": 2,
      "selling_price": 25000,
      "sold_by_id": 1
    },
    {
      "service_id": 3,
      "selling_price": 3000,
      "sold_by_id": 1
    }
  ],
  "employees": [
    {
      "employee_id": 2,
      "employee_type": "монтажник",
      "base_payment": 1500
    }
  ]
}
```

**Пример ответа:**
```json
{
  "success": true,
  "id": 3
}
```

### 4.4 Обновление данных заказа

```
PUT /api/orders/{order_id}
```

**Параметры пути:**
- `order_id`: ID заказа

**Тело запроса:**
```json
{
  "status": "в работе",
  "mount_price": 13000,
  "employees": [
    {
      "employee_id": 2,
      "employee_type": "монтажник",
      "base_payment": 1500
    },
    {
      "employee_id": 3,
      "employee_type": "монтажник",
      "base_payment": 1500
    }
  ]
}
```

**Пример ответа:**
```json
{
  "success": true,
  "id": 3
}
```

### 4.5 Удаление заказа

```
DELETE /api/orders/{order_id}
```

**Параметры пути:**
- `order_id`: ID заказа

**Пример ответа:**
```json
{
  "success": true
}
```

### 4.6 Расчет прибыли по заказу

```
GET /api/orders/{order_id}/profit
```

**Параметры пути:**
- `order_id`: ID заказа

**Пример ответа:**
```json
{
  "revenue": 40000,
  "cost": 16000,
  "commissions": 6100,
  "profit": 17900,
  "details": {
    "manager_order_commission": 250,
    "manager_mount_bonus": 900,
    "manager_services_commission": 1800,
    "installers_base_commission": 3000,
    "installer_services_commission": 250,
    "owner_commission": 1500
  }
}
```

---

## 5. Финансы

### 5.1 Получение финансовой сводки

```
GET /api/finance/summary
```

**Параметры запроса:**
- `date_from` (опционально): дата начала периода
- `date_to` (опционально): дата окончания периода

**Пример ответа:**
```json
{
  "total_revenue": 350000,
  "total_expenses": 180000,
  "total_commissions": 45000,
  "total_profit": 125000,
  "expenses_by_category": {
    "Материалы": 30000,
    "Бензин": 15000,
    "Закупка кондиционеров": 120000,
    "Прочее": 15000
  },
  "revenue_by_source": {
    "Авито": 150000,
    "ВК": 50000,
    "Яндекс услуги": 80000,
    "Рекомендации": 70000
  },
  "current_balance": 200000
}
```

### 5.2 Получение истории транзакций

```
GET /api/finance/transactions
```

**Параметры запроса:**
- `date_from` (опционально): дата начала периода
- `date_to` (опционально): дата окончания периода
- `transaction_type` (опционально): тип транзакции (доход, расход)
- `page` (опционально, по умолчанию 1): страница
- `limit` (опционально, по умолчанию 20): количество записей на странице

**Пример ответа:**
```json
{
  "transactions": [
    {
      "id": 1,
      "transaction_date": "2023-05-01",
      "amount": 35000,
      "transaction_type": "доход",
      "source_type": "заказ",
      "source_id": 1,
      "description": "Заказ №1 - завершен",
      "created_at": "2023-05-01",
      "updated_at": null
    },
    {
      "id": 2,
      "transaction_date": "2023-05-02",
      "amount": 16000,
      "transaction_type": "расход",
      "source_type": "расход",
      "source_id": 1,
      "description": "Расход: Закупка кондиционеров - Поставка кондиционеров MDV",
      "created_at": "2023-05-02",
      "updated_at": null
    }
  ],
  "total_count": 2,
  "page": 1,
  "limit": 20
}
```

### 5.3 Получение прогноза денежных потоков

```
GET /api/finance/forecast
```

**Параметры запроса:**
- `months_ahead` (опционально, по умолчанию 3): количество месяцев для прогноза

**Пример ответа:**
```json
{
  "forecast": [
    {
      "month": "2023-06",
      "forecasted_revenue": 120000,
      "forecasted_expenses": 60000,
      "forecasted_profit": 60000,
      "forecasted_balance": 260000
    },
    {
      "month": "2023-07",
      "forecasted_revenue": 120000,
      "forecasted_expenses": 60000,
      "forecasted_profit": 60000,
      "forecasted_balance": 320000
    },
    {
      "month": "2023-08",
      "forecasted_revenue": 120000,
      "forecasted_expenses": 60000,
      "forecasted_profit": 60000,
      "forecasted_balance": 380000
    }
  ]
}
```

### 5.4 Добавление расхода

```
POST /api/finance/expenses
```

**Тело запроса:**
```json
{
  "category": "Закупка кондиционеров",
  "amount": 16000,
  "description": "Поставка кондиционеров MDV",
  "expense_date": "2023-05-02",
  "expense_type": "закупка товара",
  "related_service_id": 2
}
```

**Пример ответа:**
```json
{
  "success": true,
  "id": 1
}
```

### 5.5 Установка начального баланса

```
POST /api/finance/initial-balance
```

**Тело запроса:**
```json
{
  "initial_balance": 100000
}
```

**Пример ответа:**
```json
{
  "success": true,
  "balance": 100000
}
```

### 5.6 Получение текущего баланса

```
GET /api/finance/balance
```

**Пример ответа:**
```json
{
  "balance": 200000,
  "initial_balance": 100000,
  "initial_balance_set": true,
  "updated_at": "2023-05-02"
}
```

---

## 6. Экспорт данных

### 6.1 Экспорт заказов

```
GET /api/export/orders
```

**Параметры запроса:**
- `format` (опционально, по умолчанию "csv"): формат экспорта (csv, xlsx)
- `status` (опционально): статус заказа
- `client_name` (опционально): имя клиента
- `date_from` (опционально): дата начала периода
- `date_to` (опционально): дата окончания периода

**Ответ:**
Файл в выбранном формате с данными о заказах.

### 6.2 Экспорт клиентов

```
GET /api/export/clients
```

**Параметры запроса:**
- `format` (опционально, по умолчанию "csv"): формат экспорта (csv, xlsx)
- `search` (опционально): поиск по имени или телефону
- `source` (опционально): источник клиента

**Ответ:**
Файл в выбранном формате с данными о клиентах.

### 6.3 Экспорт услуг

```
GET /api/export/services
```

**Параметры запроса:**
- `format` (опционально, по умолчанию "csv"): формат экспорта (csv, xlsx)
- `search` (опционально): поиск по названию
- `category` (опционально): категория услуги

**Ответ:**
Файл в выбранном формате с данными об услугах.

### 6.4 Экспорт сотрудников

```
GET /api/export/employees
```

**Параметры запроса:**
- `format` (опционально, по умолчанию "csv"): формат экспорта (csv, xlsx)
- `employee_type` (опционально): тип сотрудника
- `active` (опционально): статус сотрудника
- `month` (опционально): месяц для расчета зарплаты

**Ответ:**
Файл в выбранном формате с данными о сотрудниках и их зарплатах.

### 6.5 Экспорт финансовых данных

```
GET /api/export/finances
```

**Параметры запроса:**
- `format` (опционально, по умолчанию "csv"): формат экспорта (csv, xlsx)
- `date_from` (опционально): дата начала периода
- `date_to` (опционально): дата окончания периода

**Ответ:**
Файл в выбранном формате с финансовыми данными.

---

## Коды статусов HTTP

| Код | Описание |
|-|-|
| 200 | OK - запрос выполнен успешно |
| 400 | Bad Request - ошибка в запросе, например невалидные данные |
| 404 | Not Found - запрашиваемый ресурс не найден |
| 500 | Internal Server Error - внутренняя ошибка сервера |

## Общие правила использования API

1. Все запросы к API должны использовать метод, указанный в документации.
2. Если метод требует параметров в пути, они должны быть включены в URL.
3. Если метод требует параметров запроса, они должны быть добавлены к URL в виде query-параметров.
4. Если метод требует тела запроса, оно должно быть отправлено в формате JSON с соответствующим заголовком `Content-Type: application/json`.
5. Все ответы возвращаются в формате JSON, если не указано иное (например, экспорт данных).

## Примеры использования API

### Создание заказа с услугами и монтажниками

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "manager_id": 1,
    "order_date": "2023-05-03 11:00",
    "mount_price": 12000,
    "notes": "Стандартный монтаж с доп. услугами",
    "services": [
      {
        "service_id": 2,
        "selling_price": 25000,
        "sold_by_id": 1
      },
      {
        "service_id": 3,
        "selling_price": 3000,
        "sold_by_id": 2
      }
    ],
    "employees": [
      {
        "employee_id": 2,
        "employee_type": "монтажник",
        "base_payment": 1500
      },
      {
        "employee_id": 3,
        "employee_type": "монтажник",
        "base_payment": 1500
      }
    ]
  }'
```

### Получение зарплаты сотрудника за конкретный месяц

**Запрос:**
```bash
curl -X GET "http://localhost:8000/api/employees/1/salary?month=2023-05"
```

### Экспорт списка заказов в Excel

**Запрос:**
```bash
curl -X GET "http://localhost:8000/api/export/orders?format=xlsx&date_from=2023-01-01&date_to=2023-05-31&status=завершен" \
  -o orders_export.xlsx
```

## Рекомендации по оптимизации использования API

1. **Фильтрация данных на сервере**: Всегда используйте параметры фильтрации в запросах для получения только необходимых данных, это уменьшит размер ответа и время ожидания.

2. **Пагинация**: При работе с большими объемами данных используйте параметры `page` и `limit` для пагинации результатов.

3. **Кэширование**: Кэшируйте на клиенте редко изменяемые данные, такие как списки услуг или сотрудников, чтобы сократить количество запросов к API.

4. **Объединение запросов**: Когда это возможно, объединяйте несколько операций в один запрос, например, при создании заказа сразу добавляйте услуги и монтажников.

5. **Обработка ошибок**: Всегда обрабатывайте возможные ошибки при работе с API и предоставляйте понятные сообщения пользователям.