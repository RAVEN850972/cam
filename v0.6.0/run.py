import os

def create_directory(path):
    """Создаёт директорию, если она не существует"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Создана директория: {path}")

def create_file(path):
    """Создаёт пустой файл, если он не существует"""
    if not os.path.exists(path):
        with open(path, 'w') as f:
            pass  # Создаём пустой файл
        print(f"Создан файл: {path}")

def setup_project():
    # Базовая директория проекта
    project_dir = "conditioner-crm"
    create_directory(project_dir)
    
    # Создание структуры папок src
    src_dir = os.path.join(project_dir, "src")
    create_directory(src_dir)
    
    # Директории в src
    dirs = [
        os.path.join(src_dir, "app"),
        os.path.join(src_dir, "components"),
        os.path.join(src_dir, "services"),
        os.path.join(src_dir, "types"),
        os.path.join(src_dir, "hooks")
    ]
    
    for dir_path in dirs:
        create_directory(dir_path)
    
    # Поддиректории в app
    app_dirs = [
        os.path.join(src_dir, "app", "dashboard"),
        os.path.join(src_dir, "app", "clients"),
        os.path.join(src_dir, "app", "employees"),
        os.path.join(src_dir, "app", "services"),
        os.path.join(src_dir, "app", "orders"),
        os.path.join(src_dir, "app", "finances")
    ]
    
    for dir_path in app_dirs:
        create_directory(dir_path)
    
    # Создаем поддиректорию [id] в clients
    create_directory(os.path.join(src_dir, "app", "clients", "[id]"))
    
    # Поддиректории в components
    component_dirs = [
        os.path.join(src_dir, "components", "layout"),
        os.path.join(src_dir, "components", "common"),
        os.path.join(src_dir, "components", "providers")
    ]
    
    for dir_path in component_dirs:
        create_directory(dir_path)
    
    # Основные файлы
    files = [
        # Корневые файлы приложения
        os.path.join(src_dir, "app", "layout.tsx"),
        os.path.join(src_dir, "app", "page.tsx"),
        os.path.join(src_dir, "app", "globals.css"),
        
        # Страницы
        os.path.join(src_dir, "app", "dashboard", "page.tsx"),
        os.path.join(src_dir, "app", "clients", "page.tsx"),
        os.path.join(src_dir, "app", "clients", "[id]", "page.tsx"),
        os.path.join(src_dir, "app", "employees", "page.tsx"),
        os.path.join(src_dir, "app", "services", "page.tsx"),
        os.path.join(src_dir, "app", "orders", "page.tsx"),
        os.path.join(src_dir, "app", "finances", "page.tsx"),
        
        # Компоненты layout
        os.path.join(src_dir, "components", "layout", "Layout.tsx"),
        os.path.join(src_dir, "components", "layout", "Sidebar.tsx"),
        os.path.join(src_dir, "components", "layout", "Header.tsx"),
        
        # Провайдеры
        os.path.join(src_dir, "components", "providers", "QueryProvider.tsx"),
        
        # Сервисы
        os.path.join(src_dir, "services", "api.ts"),
        os.path.join(src_dir, "services", "dashboardService.ts"),
        os.path.join(src_dir, "services", "clientService.ts"),
        os.path.join(src_dir, "services", "employeeService.ts"),
        os.path.join(src_dir, "services", "serviceService.ts"),
        os.path.join(src_dir, "services", "orderService.ts"),
        os.path.join(src_dir, "services", "financeService.ts"),
        
        # Типы
        os.path.join(src_dir, "types", "api.ts"),
        os.path.join(src_dir, "types", "client.ts"),
        os.path.join(src_dir, "types", "employee.ts"),
        os.path.join(src_dir, "types", "service.ts"),
        os.path.join(src_dir, "types", "order.ts"),
        os.path.join(src_dir, "types", "finance.ts"),
        
        # Конфигурационные файлы в корне проекта
        os.path.join(project_dir, ".env.local"),
        os.path.join(project_dir, "next.config.js"),
        os.path.join(project_dir, "package.json"),
        os.path.join(project_dir, "tsconfig.json"),
    ]
    
    for file_path in files:
        create_file(file_path)
    
    print(f"\nСоздана структура проекта в папке: {project_dir}")
    print("Теперь вы можете заполнить файлы содержимым")

if __name__ == "__main__":
    setup_project()