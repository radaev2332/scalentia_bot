from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN  = "ВСТАВЬ_ТОКЕН"
OWNER_ID   = 123456789
OWNER_NICK = "@твой_ник"

MENU = {
    "coffee": {
        "title": "Кофе",
        "emoji": "☕",
        "items": {
            "esp":   ("Эспрессо",       "120 ₽"),
            "cap":   ("Капучино",       "180 ₽"),
            "flat":  ("Флэт уайт",      "200 ₽"),
            "latte": ("Латте",          "210 ₽"),
            "raf":   ("Раф",            "230 ₽"),
        }
    },
    "food": {
        "title": "Еда",
        "emoji": "🥐",
        "items": {
            "croissant": ("Круассан",        "120 ₽"),
            "sandwich":  ("Сэндвич",         "250 ₽"),
            "cake":      ("Кусок торта",      "190 ₽"),
            "oatmeal":   ("Овсянка с ягодами","220 ₽"),
        }
    },
    "cold": {
        "title": "Холодные напитки",
        "emoji": "🧃",
        "items": {
            "lemonade": ("Лимонад",     "200 ₽"),
            "matcha":   ("Матча латте", "250 ₽"),
            "smoothie": ("Смузи",       "270 ₽"),
        }
    },
}

SLOTS = ["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"]
TABLE_SIZES = ["1–2 человека","3–4 человека","5+ человек"]

async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("☕ Меню",              callback_data="menu")],
        [InlineKeyboardButton("🛍️ Заказ с собой",    callback_data="takeaway")],
        [InlineKeyboardButton("🪑 Забронировать стол", callback_data="book_table")],
        [InlineKeyboardButton("🎁 Акции и новинки",   callback_data="promos")],
        [InlineKeyboardButton("📍 Адрес и время",     callback_data="address")],
    ]
    await update.message.reply_text(
        "Добро пожаловать! ☕\n\nРады видеть тебя. Чем помочь?",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def menu(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(f"{v['emoji']} {v['title']}", callback_data=f"cat_{k}")]
          for k, v in MENU.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text("Что смотрим?", reply_markup=InlineKeyboardMarkup(kb))

async def category(update: Update, context):
    q = update.callback_query; await q.answer()
    key = q.data.replace("cat_", "")
    cat = MENU.get(key, {})
    text = f"{cat['emoji']} <b>{cat['title']}</b>\n\n"
    for item_key, (name, price) in cat["items"].items():
        text += f"• {name} — {price}\n"
    kb = [
        [InlineKeyboardButton("🛍️ Заказать с собой", callback_data="takeaway")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu")],
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def takeaway(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "🛍️ <b>Предзаказ с собой</b>\n\n"
        "Напиши что хочешь заказать и через сколько придёшь — "
        "подготовим к твоему приходу ⏱",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )
    context.user_data["expecting_order"] = True

async def book_table(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(s, callback_data=f"tsize_{i}")] for i, s in enumerate(TABLE_SIZES)]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text("Сколько человек?", reply_markup=InlineKeyboardMarkup(kb))

async def table_size(update: Update, context):
    q = update.callback_query; await q.answer()
    context.user_data["table_size"] = TABLE_SIZES[int(q.data.replace("tsize_", ""))]
    kb = [[InlineKeyboardButton(t, callback_data=f"ttime_{t}")] for t in SLOTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="book_table")])
    await q.edit_message_text("Выбери время:", reply_markup=InlineKeyboardMarkup(kb))

async def table_time(update: Update, context):
    q = update.callback_query; await q.answer()
    user = q.from_user
    time = q.data.replace("ttime_", "")
    size = context.user_data.get("table_size", "—")
    await q.edit_message_text(
        f"✅ <b>Стол забронирован!</b>\n\n"
        f"🕐 Время: {time}\n"
        f"👥 Гостей: {size}\n\n"
        f"Ждём тебя! Если планы изменились — {OWNER_NICK}",
        parse_mode="HTML"
    )
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"🪑 <b>Бронь стола</b>\n"
            f"Гость: {user.full_name} (@{user.username or '—'})\n"
            f"Время: {time}\n"
            f"Гостей: {size}",
            parse_mode="HTML"
        )
    except Exception: pass

async def promos(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "🎁 <b>Акции</b>\n\n"
        "☕ Каждый 10-й кофе — бесплатно\n"
        "🥐 Завтрак до 11:00 — кофе + круассан за 250 ₽\n"
        "📱 Подпишись на канал — скидка 10% на первый заказ\n\n"
        "<i>Акции обновляются каждую неделю</i>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )

async def address(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "📍 <b>Адрес:</b> ул. Примерная, 15\n\n"
        "🕐 <b>Время работы:</b>\n"
        "Пн–Пт: 08:00 – 22:00\n"
        "Сб–Вс: 09:00 – 23:00",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )

async def handle_text(update: Update, context):
    user = update.effective_user
    text = update.message.text
    if context.user_data.get("expecting_order"):
        context.user_data["expecting_order"] = False
        await update.message.reply_text(
            f"✅ Заказ принят! Будем готовить к твоему приходу.\n{OWNER_NICK}"
        )
        try:
            await context.bot.send_message(
                OWNER_ID,
                f"🛍️ <b>Предзаказ с собой</b>\n"
                f"Гость: {user.full_name} (@{user.username or '—'})\n"
                f"Заказ: {text}",
                parse_mode="HTML"
            )
        except Exception: pass

async def back(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [
        [InlineKeyboardButton("☕ Меню",              callback_data="menu")],
        [InlineKeyboardButton("🛍️ Заказ с собой",    callback_data="takeaway")],
        [InlineKeyboardButton("🪑 Забронировать стол", callback_data="book_table")],
        [InlineKeyboardButton("🎁 Акции и новинки",   callback_data="promos")],
        [InlineKeyboardButton("📍 Адрес и время",     callback_data="address")],
    ]
    await q.edit_message_text("Чем помочь?", reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu,        pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(category,    pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(takeaway,    pattern="^takeaway$"))
    app.add_handler(CallbackQueryHandler(book_table,  pattern="^book_table$"))
    app.add_handler(CallbackQueryHandler(table_size,  pattern="^tsize_"))
    app.add_handler(CallbackQueryHandler(table_time,  pattern="^ttime_"))
    app.add_handler(CallbackQueryHandler(promos,      pattern="^promos$"))
    app.add_handler(CallbackQueryHandler(address,     pattern="^address$"))
    app.add_handler(CallbackQueryHandler(back,        pattern="^back$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Кофейня-бот запущен ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
