# PolicyMesh: Custom RBAC Auth Service

Сервис аутентификации и авторизации на базе FastAPI с реализацией **кастомной системы прав доступа** (Matrix Access Control).
Проект разработан без использования готовых auth-библиотек (FastAPI Users, etc.) для демонстрации глубокого понимания механизмов безопасности.

## Подробнее

- [Архитектурные решения](DECISIONS.md) — обоснование ключевых технических выборов
- [Диаграммы и архитектура](docs-diagrams/README.md) — ER- и sequence-диаграммы RBAC-системы

##  Технологический стек
*   **Core:** Python 3.12, FastAPI
*   **DB:** PostgreSQL 15, SQLAlchemy 2.0 (Async), Alembic
*   **Security:** JWT (python-jose), Bcrypt (passlib)
*   **Package Manager:** Poetry

##  Быстрый старт
### Для удобства рекумендуется использовать Makefile команды, подробнее см.
```bash
make help
```
### 1. Настройка окружения
Склонируйте репозиторий и создайте `.env` файл:
```bash
cp .env.dev.example .env.dev
# Убедитесь, что DATABASE_URL соответствует настройкам вашего Docker/Postgres
```

### 2. Запуск инфраструктуры
Поднимите базу данных через Docker Compose:
```bash
docker-compose --env-file .env.dev -f docker/docker-compose-dev.yml up -d
```

### 3. Установка зависимостей и Миграции
```bash
poetry install
poetry run alembic upgrade head
```

- Проект использует pre-commit для автоматического форматирования кода и проверки типов перед каждым коммитом.
```bash
# Активируйте хуки в проекте
pre-commit install
```
### 4. Наполнение тестовыми данными (Seed)
Скрипт создаст роли (Admin, User), ресурсы (Orders) и суперюзера:
```bash
poetry run python -m app.db.seed
```

### 5. Запуск сервера
```bash
poetry run uvicorn app.main:app --reload
```

#### Документация API доступна по адресу: http://127.0.0.1:8000/docs
### Тестовые аккаунты (создаются сидом)
```markdown
Администратор (Полный доступ, управление правами):
Email: admin@example.com
Password: admin123

Пользователь (Ограниченный доступ):
Email: user@example.com (если создан вручную или расширен сид)
Password: user123
```

### Архитектура Безопасности
```markdown
1. Аутентификация (Кто ты?)
Реализована через кастомный Middleware (app/middleware/authentication.py).
Перехватывает каждый запрос.
Валидирует JWT токен в заголовке Authorization.
Загружает пользователя из БД.
Проверяет флаг is_active.
Помещает объект пользователя в request.state.user.

2. Авторизация (Что тебе можно?)
Реализована через Dependency Injection (app/api/deps.py) и таблицу-матрицу.
Таблица access_roles_rules: Хранит права для пар Role <-> BusinessElement.
```

### Флаги

```markdown
create_permission
read_permission (свои) / read_all_permission (чужие)
update_permission / update_all_permission
delete_permission / delete_all_permission
Проверка: Декоратор Depends(RequirePermission("orders", "create"))
проверяет наличие флага в БД перед выполнением ручки.
```
### Демонстрация (Mock View)
```markdown
В разделе /api/v1/mock-orders реализована имитация бизнес-логики.
Администратор может видеть и удалять любые заказы.
Пользователь может создавать заказы, но видеть и удалять может только свои.
Вы можете изменить эти правила "на лету" через API Администратора: PUT /api/v1/admin/rules/...
```
