import logging
from io import BytesIO
from telegram import (
    Update,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from config import BOT_TOKEN
from crypto import encrypt_card, decrypt_card
from db import get_session, create_all
from models import Card
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

MAX_CARDS = 10
MAX_TOTAL_SIZE = 20 * 1024 * 1024  # 20 MB
ITEMS_PER_PAGE = 6  # store buttons per pagination page

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для хранения дисконтных карт.\n"
        "Используй /addcard для добавления карты,\n"
        "/mycards — для просмотра,\n"
        "/deletecard — для удаления."
    )

# /addcard
async def addcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название магазина:")
    context.user_data["mode"] = "add_store"

# /mycards — starts store pagination
async def mycards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        async for session in get_session():
            result = await session.execute(Card.__table__.select().where(Card.user_id == user_id))
            cards = result.fetchall()
            if not cards:
                await update.message.reply_text("У тебя пока нет сохранённых карт.")
                return
            # Save cards and unique store names in user_data
            context.user_data["cards"] = cards
            stores = sorted(list({c.store for c in cards}))
            context.user_data["stores"] = stores
            context.user_data["page"] = 0
            await send_store_page(update, context, 0)
    except SQLAlchemyError as e:
        logging.error(e)
        await update.message.reply_text("Ошибка при получении карт.")

# Send a paginated page of store buttons
async def send_store_page(update_or_query, context, page: int):
    stores = context.user_data.get("stores", [])
    total_pages = (len(stores) - 1) // ITEMS_PER_PAGE + 1
    page = max(0, min(page, total_pages - 1))
    context.user_data["page"] = page

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_stores = stores[start:end]

    keyboard = []
    for store in page_stores:
        keyboard.append([InlineKeyboardButton(store, callback_data=f"store|{store}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("‹ Назад", callback_data=f"page|{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперёд ›", callback_data=f"page|{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):
        # Triggered by /mycards command
        await update_or_query.message.reply_text("Выбери магазин:", reply_markup=reply_markup)
    else:
        # Triggered by inline keyboard callback
        await update_or_query.edit_message_reply_markup(reply_markup=reply_markup)

# Inline keyboard callback handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("page|"):
        page_num = int(data.split("|")[1])
        await send_store_page(query, context, page_num)
        return

    if data.startswith("store|"):
        store = data.split("|", 1)[1]
        cards = context.user_data.get("cards", [])
        matched = [c for c in cards if c.store == store]
        if not matched:
            await query.message.reply_text("Карта не найдена.")
            return
        for card in matched:
            decrypted = decrypt_card(card.encrypted_data)
            bio = BytesIO(decrypted)
            bio.name = f"{store}.jpg"
            await query.message.reply_photo(photo=bio)
        # Reset mode after showing the card
        context.user_data["mode"] = None
        # Remove keyboard to avoid confusing the user
        await query.edit_message_reply_markup(reply_markup=None)

# /deletecard
async def deletecard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        async for session in get_session():
            result = await session.execute(Card.__table__.select().where(Card.user_id == user_id))
            cards = result.fetchall()
            if not cards:
                await update.message.reply_text("У тебя нет карт для удаления.")
                return
            store_names = list({row.store for row in cards})
            context.user_data["cards"] = cards
            context.user_data["mode"] = "delete_card"
            reply_markup = ReplyKeyboardMarkup([[s] for s in store_names], resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Выбери магазин для удаления:", reply_markup=reply_markup)
    except SQLAlchemyError as e:
        logging.error(e)
        await update.message.reply_text("Ошибка при получении карт.")

# Text message handler
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if mode == "add_store":
        context.user_data["store"] = update.message.text.strip()
        context.user_data["mode"] = "add_photo"
        await update.message.reply_text("Теперь отправь фото карты.")
        return

    if mode == "show_card":
        store = update.message.text.strip()
        matched = [c for c in context.user_data.get("cards", []) if c.store == store]
        if not matched:
            await update.message.reply_text("Карта не найдена.")
            return
        for card in matched:
            decrypted = decrypt_card(card.encrypted_data)
            bio = BytesIO(decrypted)
            bio.name = f"{store}.jpg"
            await update.message.reply_photo(photo=bio)
        context.user_data["mode"] = None
        return

    if mode == "delete_card":
        store = update.message.text.strip()
        user_id = update.effective_user.id
        try:
            async for session in get_session():
                await session.execute(
                    Card.__table__.delete().where((Card.user_id == user_id) & (Card.store == store))
                )
                await session.commit()
                await update.message.reply_text(f"Карта для {store} удалена.")
        except SQLAlchemyError as e:
            logging.error(e)
            await update.message.reply_text("Ошибка при удалении карты.")
        context.user_data["mode"] = None
        return

# Photo handler (with storage limits)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode") != "add_photo":
        return
    photo = update.message.photo[-1]
    file = await photo.get_file()
    byte_data = await file.download_as_bytearray()
    size_new_card = len(byte_data)

    user_id = update.effective_user.id
    store = context.user_data.get("store", "Без названия")

    try:
        async for session in get_session():
            result = await session.execute(Card.__table__.select().where(Card.user_id == user_id))
            cards = result.fetchall()

            if len(cards) >= MAX_CARDS:
                await update.message.reply_text(f"Достигнуто максимальное количество карт ({MAX_CARDS}).")
                context.user_data["mode"] = None
                return

            total_size = sum(len(card.encrypted_data) for card in cards)
            if total_size + size_new_card > MAX_TOTAL_SIZE:
                await update.message.reply_text(
                    f"Общий размер карт превышает лимит в {MAX_TOTAL_SIZE // (1024*1024)} МБ."
                )
                context.user_data["mode"] = None
                return

            encrypted = encrypt_card(bytes(byte_data))
            card = Card(user_id=user_id, store=store, encrypted_data=encrypted)
            session.add(card)
            await session.commit()
            await update.message.reply_text("Карта успешно сохранена!")

    except SQLAlchemyError as e:
        logging.error(e)
        await update.message.reply_text("Ошибка при сохранении карты.")

    context.user_data["mode"] = None

async def post_init(application):
    await create_all()
    await application.bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("addcard", "Добавить карту"),
        BotCommand("mycards", "Показать мои карты"),
        BotCommand("deletecard", "Удалить карту"),
    ])


def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcard", addcard))
    app.add_handler(CommandHandler("mycards", mycards))
    app.add_handler(CommandHandler("deletecard", deletecard))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()