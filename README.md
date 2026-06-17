# CartholderBot

**Self-hosted Telegram bot for storing discount and loyalty cards with encrypted photo storage.**

**Self-hosted Telegram-бот для хранения дисконтных и бонусных карт с шифрованием фотографий.**

---

## English

### What is CartholderBot?

CartholderBot is an open-source, self-hosted Telegram bot designed to replace the physical wallet of discount, loyalty, and membership cards. Instead of carrying paper or plastic cards, users photograph them once and access them anytime directly in Telegram.

The bot is intended for personal or small-team use: you deploy it on your own server, connect your own Telegram bot token, and generate your own encryption key. **No third-party cloud service ever sees your card images** — all data stays on your infrastructure.

### What problem does it solve?

Discount cards accumulate quickly: supermarkets, pharmacies, coffee shops, gyms. They clutter wallets and are easy to lose. Mobile apps from individual retailers only cover their own stores. CartholderBot provides a single, private place for all your cards, accessible from any device where Telegram is installed.

### What does the bot do?

1. **Add a card** — the user sends `/addcard`, enters a store name (e.g. "Lidl", "Auchan"), and uploads a photo of the card (barcode, QR code, or card number).
2. **View cards** — `/mycards` shows a paginated list of stores. Tapping a store sends back the decrypted card photo.
3. **Delete a card** — `/deletecard` lets the user remove a card by store name.

Each Telegram user is isolated by their `user_id`. One user cannot see another user's cards.

### How is data stored?

```
User (Telegram)
      │
      ▼  photo (JPEG/PNG, in transit via Telegram API)
┌─────────────┐
│  Bot (app)  │  ← decrypts only in memory when user requests a card
└──────┬──────┘
       │  Fernet encrypt (AES-128-CBC + HMAC-SHA256)
       ▼
┌─────────────┐
│ PostgreSQL  │  ← stores ciphertext only
│  table:     │
│  cards      │
└─────────────┘
```

**What is stored in the database:**

| Field | Type | Content |
|-------|------|---------|
| `id` | integer | Internal record ID |
| `user_id` | bigint | Telegram user ID (for isolation) |
| `store` | string | Store name as entered by the user |
| `encrypted_data` | binary | **Encrypted** card photo (Fernet ciphertext) |

**What is NOT stored:**

- Plaintext photos — never written to disk or database
- User names, phone numbers, or Telegram profile data
- Card numbers or barcodes in text form (only inside the encrypted image)
- Any analytics or telemetry

**Encryption details:**

- Algorithm: [Fernet](https://github.com/fernet/spec/blob/master/Spec.md) (symmetric authenticated encryption from the `cryptography` library)
- Key: 32-byte URL-safe base64 string, set via `FERNET_KEY` in `.env`
- The key is loaded once at application startup; each photo is encrypted before `INSERT` and decrypted only when the owner requests it
- **If you lose `FERNET_KEY`, encrypted cards cannot be recovered** — back up the key securely

**Storage limits (per user):**

- Maximum 10 cards
- Maximum 20 MB total encrypted storage

### Architecture

| Component | Role |
|-----------|------|
| `app/main.py` | Telegram handlers, user state machine, business logic |
| `app/crypto.py` | Fernet encrypt / decrypt |
| `app/models.py` | SQLAlchemy `Card` model |
| `app/db.py` | Async PostgreSQL connection (SQLAlchemy + asyncpg) |
| `app/config.py` | Environment variable loading |
| PostgreSQL 15 | Persistent storage |
| Docker Compose | Orchestration of `app` + `db` services |

User interaction state is managed via `context.user_data["mode"]` (e.g. `add_store` → `add_photo`).

### Bot commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and usage instructions |
| `/addcard` | Add a new card: store name → photo |
| `/mycards` | Browse saved cards by store (inline keyboard with pagination) |
| `/deletecard` | Delete a card by store name |

### Quick start

**Prerequisites:** Docker and Docker Compose installed.

1. **Create a Telegram bot** via [@BotFather](https://t.me/BotFather):
   - Send `/newbot`, follow the prompts, copy the `BOT_TOKEN`
   - If you are rotating a compromised token, use `/revoke` on the old bot first

2. **Clone the repository:**
   ```bash
   git clone https://github.com/webdoker/cardholder.git
   cd cardholder
   ```

3. **Create your `.env` file:**
   ```bash
   cp .env.example .env
   ```

4. **Generate a Fernet encryption key** (each deployment must have its own unique key):
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Paste the output as `FERNET_KEY` in `.env`.

5. **Fill in `BOT_TOKEN`** in `.env` with the token from BotFather.

6. **Start the stack:**
   ```bash
   docker compose up --build -d
   ```

7. Open your bot in Telegram and send `/start`.

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `FERNET_KEY` | Yes | Fernet key for encrypting card photos (generate your own) |
| `DATABASE_URL` | Yes | PostgreSQL connection string (default in `.env.example` works with Docker Compose) |

> **Never commit `.env` to version control.** Each operator generates their own `BOT_TOKEN` and `FERNET_KEY`.

### Security notes

- Run behind a firewall; only the Telegram API needs outbound internet access
- Change default PostgreSQL credentials in production
- Back up `FERNET_KEY` — without it, stored cards are unrecoverable
- Revoke and reissue `BOT_TOKEN` if it was ever exposed in logs or git history

### License

MIT — see [LICENSE](LICENSE).

---

## Русский

### Что такое CartholderBot?

CartholderBot — это open-source Telegram-бот с развёртыванием на собственном сервере. Он заменяет физический бумажник с дисконтными, бонусными и клубными картами: пользователь один раз фотографирует карту и в любой момент открывает её в Telegram.

Бот предназначен для личного использования или небольших команд. Вы разворачиваете его на своём сервере, подключаете свой токен Telegram-бота и генерируете свой ключ шифрования. **Сторонние облачные сервисы не получают доступ к фотографиям карт** — все данные остаются на вашей инфраструктуре.

### Какую задачу решает?

Дисконтные карты быстро накапливаются: супермаркеты, аптеки, кофейни, фитнес-клубы. Они занимают место в кошельке и легко теряются. Мобильные приложения отдельных сетей покрывают только свои магазины. CartholderBot даёт единое приватное хранилище для всех карт, доступное с любого устройства с Telegram.

### Что умеет бот?

1. **Добавить карту** — пользователь отправляет `/addcard`, вводит название магазина (например, «Пятёрочка», «Лента») и загружает фото карты (штрихкод, QR-код или номер).
2. **Посмотреть карты** — `/mycards` показывает список магазинов с пагинацией. Нажатие на магазин отправляет расшифрованное фото карты.
3. **Удалить карту** — `/deletecard` удаляет карту по названию магазина.

Каждый пользователь Telegram изолирован по `user_id`. Один пользователь не видит карты другого.

### Как хранятся данные?

```
Пользователь (Telegram)
      │
      ▼  фото (JPEG/PNG, передаётся через Telegram API)
┌─────────────┐
│  Бот (app)  │  ← расшифровка только в памяти по запросу пользователя
└──────┬──────┘
       │  шифрование Fernet (AES-128-CBC + HMAC-SHA256)
       ▼
┌─────────────┐
│ PostgreSQL  │  ← хранится только шифротекст
│  таблица:   │
│  cards      │
└─────────────┘
```

**Что хранится в базе данных:**

| Поле | Тип | Содержимое |
|------|-----|------------|
| `id` | integer | Внутренний ID записи |
| `user_id` | bigint | Telegram ID пользователя (для изоляции) |
| `store` | string | Название магазина, введённое пользователем |
| `encrypted_data` | binary | **Зашифрованное** фото карты (шифротекст Fernet) |

**Что НЕ хранится:**

- Фотографии в открытом виде — никогда не записываются на диск или в БД
- Имена, телефоны и данные профиля Telegram
- Номера карт или штрихкоды в текстовом виде (только внутри зашифрованного изображения)
- Аналитика и телеметрия

**Детали шифрования:**

- Алгоритм: [Fernet](https://github.com/fernet/spec/blob/master/Spec.md) (симметричное аутентифицированное шифрование из библиотеки `cryptography`)
- Ключ: 32-байтовая строка в base64, задаётся через `FERNET_KEY` в `.env`
- Ключ загружается один раз при старте; каждое фото шифруется перед записью в БД и расшифровывается только по запросу владельца
- **При потере `FERNET_KEY` восстановить карты невозможно** — храните ключ в надёжном месте

**Лимиты (на пользователя):**

- Не более 10 карт
- Не более 20 МБ суммарного зашифрованного объёма

### Архитектура

| Компонент | Назначение |
|-----------|------------|
| `app/main.py` | Обработчики Telegram, машина состояний, бизнес-логика |
| `app/crypto.py` | Шифрование / расшифровка Fernet |
| `app/models.py` | SQLAlchemy-модель `Card` |
| `app/db.py` | Асинхронное подключение к PostgreSQL (SQLAlchemy + asyncpg) |
| `app/config.py` | Загрузка переменных окружения |
| PostgreSQL 15 | Постоянное хранилище |
| Docker Compose | Оркестрация сервисов `app` + `db` |

Состояние диалога управляется через `context.user_data["mode"]` (например, `add_store` → `add_photo`).

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и инструкция |
| `/addcard` | Добавить карту: магазин → фото |
| `/mycards` | Просмотр карт по магазинам (inline-клавиатура с пагинацией) |
| `/deletecard` | Удалить карту по названию магазина |

### Быстрый старт

**Требования:** установленные Docker и Docker Compose.

1. **Создайте Telegram-бота** через [@BotFather](https://t.me/BotFather):
   - Отправьте `/newbot`, следуйте инструкциям, скопируйте `BOT_TOKEN`
   - Если перевыпускаете скомпрометированный токен — сначала выполните `/revoke` у старого бота

2. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/webdoker/cardholder.git
   cd cardholder
   ```

3. **Создайте файл `.env`:**
   ```bash
   cp .env.example .env
   ```

4. **Сгенерируйте ключ шифрования Fernet** (у каждого развёртывания должен быть свой уникальный ключ):
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Вставьте результат в `FERNET_KEY` в `.env`.

5. **Укажите `BOT_TOKEN`** в `.env` — токен от BotFather.

6. **Запустите:**
   ```bash
   docker compose up --build -d
   ```

7. Откройте бота в Telegram и отправьте `/start`.

### Переменные окружения

| Переменная | Обязательна | Описание |
|------------|-------------|----------|
| `BOT_TOKEN` | Да | Токен Telegram-бота от @BotFather |
| `FERNET_KEY` | Да | Ключ Fernet для шифрования фото карт (генерируется самостоятельно) |
| `DATABASE_URL` | Да | Строка подключения к PostgreSQL (значение по умолчанию в `.env.example` подходит для Docker Compose) |

> **Никогда не коммитьте `.env` в репозиторий.** Каждый оператор генерирует свой `BOT_TOKEN` и `FERNET_KEY`.

### Безопасность

- Запускайте за файрволом; боту нужен только исходящий доступ к Telegram API
- В продакшене смените стандартные учётные данные PostgreSQL
- Делайте резервную копию `FERNET_KEY` — без него сохранённые карты не восстановить
- Перевыпустите `BOT_TOKEN` через BotFather, если он попадал в логи или историю git

### Лицензия

MIT — см. [LICENSE](LICENSE).
