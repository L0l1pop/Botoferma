# Ботоферма API

API для управления пользователями ботофермы для E2E-тестирования. Сервис предоставляет возможность регистрации пользователей, аутентификации и управления блокировками для параллельного выполнения тестов.

## 🚀 Функционал

- ✅ Регистрация пользователей с хешированием паролей (bcrypt)
- ✅ JWT аутентификация
- ✅ Блокировка/разблокировка пользователей для E2E-тестов
- ✅ REST API с автоматической документацией (Swagger/OpenAPI)
- ✅ Async PostgreSQL через SQLAlchemy 2.0
- ✅ Полное покрытие тестами (pytest)
- ✅ Docker поддержка

## 📋 Требования

- Python 3.10+
- PostgreSQL 14+
- Docker & Docker Compose (опционально)

## 🛠️ Стек технологий

- **Backend:** FastAPI, Uvicorn
- **Database:** PostgreSQL, SQLAlchemy 2.0 (async)
- **Authentication:** JWT (python-jose), bcrypt
- **Validation:** Pydantic v2
- **Testing:** pytest, pytest-asyncio, httpx
- **Containerization:** Docker, Docker Compose


### 📂 Описание директорий

**app/** - Исходный код приложения
- `main.py` - Точка входа FastAPI
- `config.py` - Настройки приложения
- `database.py` - Подключение к PostgreSQL
- `auth.py` - JWT токены и аутентификация

**app/users/** - Модуль пользователей
- `models.py` - SQLAlchemy ORM модели
- `schemas.py` - Pydantic схемы валидации
- `crud.py` - CRUD операции с БД
- `utils.py` - Утилиты (хеширование паролей)
- `router.py` - REST API endpoints

**tests/** - Тестирование
- `conftest.py` - Pytest fixtures
- `test_users.py` - E2E тесты API

**Конфигурационные файлы:**
- `docker-compose.yml` - Docker Compose конфигурация
- `Dockerfile` - Docker образ приложения
- `requirements.txt` - Python зависимости
- `pytest.ini` - Конфигурация pytest
- `.env` - Переменные окружения

## 🚀 Быстрый старт

### Вариант 1: Docker (рекомендуется)

Клонировать репозиторий

git clone [<repository-url>](https://github.com/L0l1pop/Botoferma.git)

cd botoferma

Создать .env файл

Запустить с Docker Compose

docker-compose up --build

Приложение доступно на http://localhost:8000

### Вариант 2: Локальная разработка

Создать виртуальное окружение

python -m venv venv

source venv/bin/activate # Linux/Mac

или

venv\Scripts\activate # Windows

Установить зависимости

pip install -r requirements.txt

Настроить .env файл

Запустить PostgreSQL (через Docker или локально)

docker run -d

--name botoferma_postgres

-e POSTGRES_USER=postgres

-e POSTGRES_PASSWORD=postgres

-e POSTGRES_DB=botoferma

-p 5432:5432

postgres:14-alpine

Инициализировать БД

python -m app.init_db

Запустить приложение

uvicorn app.main:app --reload


## 🔧 Конфигурация

Создайте `.env` файл в корне проекта:

Database

POSTGRES_USER=postgres

POSTGRES_PASSWORD=postgres

POSTGRES_HOST=localhost

POSTGRES_PORT=5432

POSTGRES_DB=botoferma

JWT

SECRET_KEY=your-secret-key-min-32-characters-long

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30

App

DEBUG=True

Для генерации `SECRET_KEY`:

openssl rand -hex 32


## 📚 API Документация

После запуска приложения:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Основные endpoints:

#### Аутентификация

POST /api/register # Регистрация пользователя

POST /api/login # Получение JWT токена

GET /api/users/me # Информация о текущем пользователе


#### Управление пользователями

GET /api/users # Список всех пользователей

POST /api/users/acquire # Заблокировать пользователя для теста

POST /api/users/release # Разблокировать пользователя


## 🧪 Тестирование

Запустить все тесты

pytest

С подробным выводом

pytest -v

С покрытием кода

pytest --cov=app --cov-report=html

Конкретный тест

pytest tests/test_users.py::test_register_user

В Docker

docker-compose exec app pytest -v


## 🐳 Docker команды

Собрать образы

docker-compose build

Запустить сервисы

docker-compose up -d

Остановить сервисы

docker-compose down

Удалить с volumes (БД)

docker-compose down -v

Логи приложения

docker-compose logs -f app

Логи PostgreSQL

docker-compose logs -f postgres

Войти в контейнер

docker-compose exec app bash

Перезапустить сервисы

docker-compose restart


## 📊 Модель данных

### User (Пользователь)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный идентификатор |
| `created_at` | DateTime | Дата создания |
| `login` | String | Email пользователя (уникальный) |
| `password` | String | Хешированный пароль |
| `project_id` | UUID | ID проекта |
| `env` | Enum | Окружение (prod, preprod, stage) |
| `domain` | Enum | Тип домена (canary, regular) |
| `locktime` | DateTime | Временная метка блокировки |

## 🔒 Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены для аутентификации
- CORS middleware настроен
- Валидация данных через Pydantic
- SQL injection защита через SQLAlchemy ORM