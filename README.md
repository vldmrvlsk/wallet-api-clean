# Wallet API

Асинхронное REST API для управления электронными кошельками. Приложение позволяет получать баланс кошелька, пополнять его и списывать средства с проверкой достаточности баланса.

## Возможности

- Получение баланса кошелька по UUID.
- Пополнение и списание средств.
- Валидация входных данных.
- Обработка ошибок: кошелёк не найден, недостаточно средств, некорректные данные.
- Асинхронная работа с PostgreSQL.
- Транзакции и блокировка строки при изменении баланса.
- Миграции базы данных через Alembic.
- Автоматизированные тесты, включая проверку параллельных списаний.
- Запуск API и PostgreSQL через Docker Compose.

## Технологии

- Python 3.13
- FastAPI
- Pydantic
- PostgreSQL 17
- SQLAlchemy 2 (async)
- asyncpg
- Alembic
- pytest, httpx
- Docker, Docker Compose
- Git, GitHub

## Запуск через Docker

Необходим установленный Docker Desktop с поддержкой Docker Compose.

### 1. Клонирование репозитория

```bash
git clone https://github.com/vldmrvlsk/wallet-api-clean.git
cd wallet-api-clean
```

### 2. Настройка переменных окружения

Создайте локальный файл `.env` на основе шаблона.

**Windows CMD:**

```cmd
copy .env.example .env
```

Откройте `.env` и замените значение `POSTGRES_PASSWORD` на собственный уникальный пароль.

Не публикуйте `.env` в GitHub и не передавайте пароль другим людям.

### 3. Запуск приложения

```bash
docker compose up -d --build
```

Проверьте состояние контейнеров:

```bash
docker compose ps
```

Откройте документацию API:

- Главная страница: http://localhost:18010/
- Swagger UI: http://localhost:18010/docs

Остановка контейнеров:

```bash
docker compose down
```

Данные PostgreSQL хранятся в Docker volume, созданном Docker Compose, и сохраняются после обычной остановки контейнеров. Команда `docker compose down -v` удаляет этот volume вместе с данными, поэтому без необходимости её использовать не следует.

## Переменные окружения

Приложение использует следующие переменные:

| Переменная | Назначение |
| --- | --- |
| `POSTGRES_DB` | Имя основной базы данных |
| `POSTGRES_USER` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Пароль пользователя PostgreSQL |
| `DATABASE_URL` | URL подключения приложения к базе данных |

В Docker Compose переменная `DATABASE_URL` формируется из настроек PostgreSQL. Для локального запуска приложения и тестов её нужно задавать отдельно.

## API endpoints

| Метод | Endpoint | Описание |
| --- | --- | --- |
| GET | `/` | Проверка доступности API |
| GET | `/api/v1/wallets/{wallet_uuid}` | Получение кошелька и его баланса |
| POST | `/api/v1/wallets/{wallet_uuid}/operation` | Пополнение или списание средств |

### Получение кошелька

Пример запроса:

```http
GET /api/v1/wallets/c2b2683e-cfec-491a-bae7-792bd9e7bbeb
```

Пример успешного ответа `200 OK`:

```json
{
  "wallet_uuid": "c2b2683e-cfec-491a-bae7-792bd9e7bbeb",
  "balance": "2506.00"
}
```

Баланс приведён как пример. Фактическое значение зависит от данных в базе.

### Пополнение кошелька

Запрос:

```http
POST /api/v1/wallets/c2b2683e-cfec-491a-bae7-792bd9e7bbeb/operation
Content-Type: application/json
```

Тело запроса:

```json
{
  "operation_type": "DEPOSIT",
  "amount": "100.00"
}
```

При успешном выполнении баланс увеличивается на указанную сумму.

### Списание средств

Тело запроса:

```json
{
  "operation_type": "WITHDRAW",
  "amount": "50.00"
}
```

Если средств достаточно, операция выполняется и баланс уменьшается на указанную сумму.

### Коды ответов

- `200 OK` — запрос или операция выполнены успешно.
- `404 Not Found` — кошелёк не найден.
- `409 Conflict` — недостаточно средств для списания.
- `422 Unprocessable Entity` — входные данные не прошли валидацию.

Сумма операции должна быть положительной.

## Миграции базы данных

Для применения миграций внутри контейнера API:

```bash
docker compose exec api alembic upgrade head
```

Для проверки текущей применённой миграции:

```bash
docker compose exec api alembic current
```

При локальном запуске Alembic необходимо предварительно задать `DATABASE_URL`.

## Тестирование

Тесты используют отдельную базу данных `wallet_test_db`. Не запускайте тесты против основной базы `wallet_db`, поскольку тесты могут изменять данные.

### 1. Запуск контейнеров

Убедитесь, что Docker Desktop запущен, и выполните:

```cmd
docker compose up -d
```

### 2. Создание тестовой базы данных

Создайте отдельную базу для тестов:

```cmd
docker compose exec db psql -U wallet_user -d wallet_db -c "CREATE DATABASE wallet_test_db"
```

Эту команду нужно выполнить только один раз для конкретной базы данных. Если `wallet_test_db` уже существует, повторно создавать её не нужно.

### 3. Применение миграций к тестовой базе

```cmd
docker compose exec api python -c "import os; u=os.environ['DATABASE_URL']; os.environ['DATABASE_URL']=u.rsplit('/',1)[0]+'/wallet_test_db'; import alembic.config; alembic.config.main(argv=['upgrade','head'])"
```

### 4. Запуск тестов

```cmd
docker compose exec api python -c "import os; u=os.environ['DATABASE_URL']; os.environ['DATABASE_URL']=u.rsplit('/',1)[0]+'/wallet_test_db'; import pytest; raise SystemExit(pytest.main(['-v']))"
```

Тесты проверяют:

- получение существующего кошелька;
- получение несуществующего кошелька;
- пополнение;
- успешное списание;
- списание при недостаточном балансе;
- параллельные списания.

После первоначальной настройки тестовой базы повторять шаги 2 и 3 при каждом запуске тестов не требуется, если база и миграции сохранены.

Не используйте `docker compose down -v` для обычной остановки проекта: эта команда удаляет тома Docker с данными.

## Структура проекта

```text
wallet-api-clean/
├── app/
│   ├── db.py
│   └── models.py
├── migrations/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── conftest.py
│   └── test_wallets.py
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yaml
├── alembic.ini
├── main.py
├── requirements.txt
└── README.md
```

## Авторизация и безопасность

Проект является учебным примером. Перед использованием в production необходимо отдельно проработать:

- управление секретами;
- настройки доступа к базе данных;
- аутентификацию и авторизацию;
- логирование и мониторинг;
- резервное копирование и восстановление базы данных.

## Репозиторий

Исходный код: https://github.com/vldmrvlsk/wallet-api-clean