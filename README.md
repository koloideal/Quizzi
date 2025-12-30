# Trudex

Telegram платформа для тестирования по охране труда

## Архитектура

Проект построен на принципах Clean Architecture с разделением на три слоя:

- **Application** - координация и UI логика (aiogram, aiogram-dialog)
- **Domain** - бизнес-логика и доменные модели
- **Infrastructure** - технические детали (БД, API, планировщик)

## Технологический стек

- aiogram 3.x - Telegram Bot API
- aiogram-dialog - state machine для диалогов
- dishka - Dependency Injection
- SQLAlchemy 2.x async - ORM для PostgreSQL
- Alembic - миграции БД
- APScheduler - фоновые задачи
- httpx - HTTP-клиент
- Pydantic - валидация конфигурации

## Структура проекта

```
src/trudex/
├── application/          # Слой приложения
│   └── bot/
│       ├── middlewares/  # Промежуточные обработчики
│       ├── user_dialogs/ # Диалоги пользователей
│       ├── admin_dialogs/# Диалоги администраторов
│       └── handlers.py   # Обработчики событий
├── domain/               # Доменный слой
│   └── schemas.py        # Доменные модели
└── infrastructure/       # Инфраструктурный слой
    ├── api/              # Внешние API
    ├── database/         # Работа с БД
    │   ├── dao/          # Data Access Objects
    │   ├── models.py     # ORM модели
    │   └── config.py     # Конфигурация БД
    ├── scheduling/       # Фоновые задачи
    └── utils/            # Утилиты и конфигурация
```

## Запуск

1. Установить зависимости: `uv sync`
2. Настроить `config.toml`
3. Запустить миграции: `alembic upgrade head`
4. Запустить бота: `python -m trudex`
