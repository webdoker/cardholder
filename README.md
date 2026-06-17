# CartholderBot

Telegram bot for storing and managing discount/loyalty cards with encrypted photo storage.

Telegram-бот для хранения и управления дисконтными картами с шифрованием фотографий.

---

## English

### Description

**CartholderBot** is a self-hosted Telegram bot that lets you save photos of discount and loyalty cards, organize them by store name, and access them anytime from Telegram. Card images are encrypted before being stored in PostgreSQL.

### Features

- Add cards with a store name and photo
- Browse saved cards grouped by store (with pagination)
- Delete cards by store
- Fernet encryption for card images at rest
- Multi-user support (isolated by Telegram `user_id`)
- Limits: up to 10 cards per user, 20 MB total storage

### Tech stack

| Component | Description |
|-----------|-------------|
| Python 3.11 | Application language |
| python-telegram-bot | Telegram Bot API |
| SQLAlchemy (asyncio) + asyncpg | Async PostgreSQL ORM |
| PostgreSQL 15 | Database |
| cryptography (Fernet) | Image encryption |
| Docker + Docker Compose | Deployment |

### Project structure

```
app/
  main.py           # Bot logic and command handlers
  models.py         # Database models
  db.py             # Database connection and sessions
  crypto.py         # Encryption / decryption
  config.py         # Environment configuration
  init_db.py        # Database initialization script
  requirements.txt  # Python dependencies
Dockerfile
docker-compose.yml
.env.example        # Environment variables template
```

### Bot commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and usage hints |
| `/addcard` | Add a new card (store name + photo) |
| `/mycards` | View saved cards |
| `/deletecard` | Delete a card by store |

### Quick start

1. Create a bot via [@BotFather](https://t.me/BotFather) and get a `BOT_TOKEN`.
2. Clone the repository:
   ```bash
   git clone https://github.com/webdoker/cardholder.git
   cd cardholder
   ```
3. Create `.env` from the example:
   ```bash
   cp .env.example .env
   ```
4. Generate a Fernet key and set it in `.env`:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
5. Start with Docker Compose:
   ```bash
   docker compose up --build -d
   ```

### Security notes

- Never commit `.env` or real tokens to version control.
- Card photos are encrypted with Fernet before storage.
- The database is only accessible inside the Docker network.
- Use strong, unique values for `FERNET_KEY` and database credentials in production.

### License

MIT — see [LICENSE](LICENSE).

---

## Русский

### Описание

**CartholderBot** — self-hosted Telegram-бот для сохранения фотографий дисконтных и бонусных карт. Карты группируются по названию магазина, а изображения шифруются перед записью в PostgreSQL.

### Возможности

- Добавление карт: название магазина + фото
- Просмотр сохранённых карт по магазинам (с пагинацией)
- Удаление карт по магазину
- Шифрование изображений алгоритмом Fernet
- Поддержка нескольких пользователей (изоляция по `user_id`)
- Лимиты: до 10 карт на пользователя, до 20 МБ суммарно

### Стек технологий

| Компонент | Описание |
|-----------|----------|
| Python 3.11 | Язык приложения |
| python-telegram-bot | Telegram Bot API |
| SQLAlchemy (asyncio) + asyncpg | Асинхронная ORM для PostgreSQL |
| PostgreSQL 15 | База данных |
| cryptography (Fernet) | Шифрование изображений |
| Docker + Docker Compose | Развёртывание |

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и подсказки |
| `/addcard` | Добавить карту (магазин + фото) |
| `/mycards` | Показать сохранённые карты |
| `/deletecard` | Удалить карту по магазину |

### Быстрый старт

1. Создайте бота через [@BotFather](https://t.me/BotFather) и получите `BOT_TOKEN`.
2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/webdoker/cardholder.git
   cd cardholder
   ```
3. Создайте `.env` из шаблона:
   ```bash
   cp .env.example .env
   ```
4. Сгенерируйте ключ Fernet и укажите его в `.env`:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
5. Запустите через Docker Compose:
   ```bash
   docker compose up --build -d
   ```

### Безопасность

- Не коммитьте `.env` и реальные токены в репозиторий.
- Фотографии карт шифруются Fernet перед сохранением.
- База данных доступна только внутри Docker-сети.
- В продакшене используйте надёжные уникальные значения для `FERNET_KEY` и пароля БД.

### Лицензия

MIT — см. [LICENSE](LICENSE).
