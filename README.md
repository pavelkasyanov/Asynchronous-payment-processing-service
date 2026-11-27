# Payment Processing Service

Асинхронный микросервис для обработки платежей с использованием:
- **FastAPI** — веб-фреймворк
- **PostgreSQL** — база данных
- **RabbitMQ** — брокер сообщений
- **FastStream** — асинхронный consumer

## Архитектура

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  API Server │───▶│  Outbox    │───▶│  RabbitMQ    │
│ (FastAPI)   │    │  Pattern   │    │               │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
                   ┌──────────┐        ┌──────────┐        ┌──────────┐
                   │ Consumer │        │  DB      │        │  Webhook │
                   │ (Fast-   │        │          │        │  Client  │
                   │ Stream) │        │  PGSQL   │        │          │
                   └──────────┘        └──────────┘        └──────────┘
```

## Паттерны и гарантии

- **Outbox Pattern** — гарантия доставки событий через транзакционную запись
- **Idempotency** — защита от дублей через Idempotency-Key
- **Retry with Backoff** — повторные попытки с экспоненциальной задержкой
- **Dead Letter Queue** — изоляция неуспешных сообщений

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd Asynchronous-payment-processing-service
```

### 2. Создание файла окружения

```bash
cp .env.example .env
# Отредактируйте .env под ваши нужды
```

### 3. Запуск с Docker Compose

```bash
docker-compose up -d --build
```

### 4. Применение миграций

```bash
docker-compose exec api alembic upgrade head
```

### 5. Проверка запуска

```bash
# API доступен по адресу: http://localhost:8000
# RabbitMQ management: http://localhost:15672 (логин: guest, пароль: guest)
```

## API документация

После запуска откройте Swagger UI:
```
http://localhost:8000/docs
```

## Примеры использования

### Создание платежа

```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "amount": 1500.00,
    "currency": "RUB",
    "description": "Платёж за товар",
    "meta": {"order_id": "12345"},
    "webhook_url": "https://example.com/webhook"
  }'
```

### Получение информации о платеже

```bash
curl http://localhost:8000/api/v1/payments/{payment_id}
```

## Структура проекта

```
Asynchronous-payment-processing-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   ├── config.py            # Конфигурация
│   ├── database.py          # База данных
│   ├── models/              # SQLAlchemy модели
│   │   ├── __init__.py
│   │   ├── payment.py       # Payment модель
│   │   └── outbox.py        # Outbox модель
│   └── schemas/             # Pydantic схемы
│       ├── __init__.py
│       └── payment.py       # Схемы платежа
├── api/
│   └── v1/                  # API версии
│       └── endpoints.py     # Эндпоинты
├── workers/
│   └── consumer.py          # RabbitMQ consumer
├── migrations/              # Alembic миграции
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
├── docker-compose.yml
├── Dockerfile.api
├── requirements.txt
└── README.md
```

## Ключевые особенности

### Outbox Pattern

```python
# Транзакционная запись платежа и события
async with session.begin():
    # Запись платежа
    payment = Payment(**data)
    session.add(payment)

    # Запись в outbox (в той же транзакции!)
    outbox = Outbox(payment_id=payment.id, event_type="payments.new", payload=data)
    session.add(outbox)
```

### Idempotency

```python
# Проверка дублей перед созданием
existing = await session.get(Payment, idempotency_key)
if existing:
    return existing  # Возвращаем существующий платеж
```

### Retry с экспоненциальной задержкой

```python
for attempt in range(3):
    await asyncio.sleep(2**attempt)  # 1с, 2с, 4с
    response = await http.post(url, json=payload)
    if response.status_code == 200:
        return True
```

## Лицензия

MIT License
