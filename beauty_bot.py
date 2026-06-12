from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN  = "ВСТАВЬ_ТОКЕН"
OWNER_ID   = 123456789
OWNER_NICK = "@твой_ник"

SERVICES = {
    "manicure": {
        "cat": "Маникюр",
        "emoji": "💅",
        "items": {
            "classic": ("Классический маникюр", "800 ₽",  "60 мин"),
            "gel":     ("Гель-лак",              "1 200 ₽","75 мин"),
            "design":  ("Дизайн (1 ноготь)",     "100 ₽",  "10 мин"),
        }
    },
    "brows": {
        "cat": "Брови и ресницы",
        "emoji": "👁️",
        "items": {
            "shape":  ("Коррекция бровей",  "600 ₽",  "30 мин"),
            "tint":   ("Окрашивание бровей","700 ₽",  "45 мин"),
            "lashes": ("Ламинирование ресниц","2 500 ₽","90 мин"),
        }
    },
    "hair": {
        "cat": "Волосы",
        "emoji": "💇",
        "items": {
            "cut":      ("Стрижка",          "1 000 ₽","45 мин"),
            "color":    ("Окрашивание",      "3 500 ₽","120 мин"),
            "keratin":  ("Кератин",          "5 000 ₽","180 мин"),
        }
    },
}

MASTERS = {
    "master1": {"name": "Анна",   "spec": "Маникюр, педикюр"},
    "master2": {"name": "Мария",  "spec": "Брови, ресницы"},
    "master3": {"name": "Оксана", "spec": "Волосы, окрашивание"},
}

SLOTS = ["10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"]

async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("💅 Услуги и цены",      callback_data="services")],
        [InlineKeyboardButton("📅 Записаться",          callback_data="book")],
        [InlineKeyboardButton("👩 Наши мастера",        callback_data="masters")],
        [InlineKeyboardButton("⭐ Отзывы",              callback_data="reviews")],
        [InlineKeyboardButton("📍 Адрес",               callback_data="address")],
    ]
    await update.message.reply_text(
        "Привет! 💅\nДобро пожаловать в студию красоты.\n\nЧем помочь?",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def services(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(f"{v['emoji']} {v['cat']}", callback_data=f"scat_{k}")]
          for k, v in SERVICES.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text("Выбери категорию:", reply_markup=InlineKeyboardMarkup(kb))

async def service_cat(update: Update, context):
    q = update.callback_query; await q.answer()
    key = q.data.replace("scat_", "")
    cat = SERVICES.get(key, {})
    text = f"{cat['emoji']} <b>{cat['cat']}</b>\n\n"
    for _, (name, price, time) in cat["items"].items():
        text += f"• {name} — {price} ({time})\n"
    kb = [
        [InlineKeyboardButton("📅 Записаться", callback_data="book")],
        [InlineKeyboardButton("◀️ Назад",      callback_data="services")],
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def book(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(f"{v['emoji']} {v['cat']}", callback_data=f"bcat_{k}")]
          for k, v in SERVICES.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text("Что записываемся делать?", reply_markup=InlineKeyboardMarkup(kb))

async def book_cat(update: Update, context):
    q = update.callback_query; await q.answer()
    key = q.data.replace("bcat_", "")
    context.user_data["book_cat"] = key
    cat = SERVICES.get(key, {})
    kb = [[InlineKeyboardButton(f"{name} — {price}", callback_data=f"bsvc_{skey}")]
          for skey, (name, price, _) in cat["items"].items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="book")])
    await q.edit_message_text("Выбери услугу:", reply_markup=InlineKeyboardMarkup(kb))

async def book_svc(update: Update, context):
    q = update.callback_query; await q.answer()
    context.user_data["book_svc"] = q.data.replace("bsvc_", "")
    kb = [[InlineKeyboardButton(f"{m['name']} — {m['spec']}", callback_data=f"bmst_{mk}")]
          for mk, m in MASTERS.items()]
    kb.append([InlineKeyboardButton("Любой свободный", callback_data="bmst_any")])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data=f"bcat_{context.user_data.get('book_cat','')}")])
    await q.edit_message_text("Выбери мастера:", reply_markup=InlineKeyboardMarkup(kb))

async def book_master(update: Update, context):
    q = update.callback_query; await q.answer()
    mst_key = q.data.replace("bmst_", "")
    context.user_data["book_master"] = mst_key
    kb = [[InlineKeyboardButton(t, callback_data=f"btime_{t}")] for t in SLOTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data=f"bsvc_{context.user_data.get('book_svc','')}")])
    await q.edit_message_text("Выбери время:", reply_markup=InlineKeyboardMarkup(kb))

async def book_time(update: Update, context):
    q = update.callback_query; await q.answer()
    user = q.from_user
    time    = q.data.replace("btime_", "")
    cat_key = context.user_data.get("book_cat", "")
    svc_key = context.user_data.get("book_svc", "")
    mst_key = context.user_data.get("book_master", "any")
    cat = SERVICES.get(cat_key, {})
    svc_name, svc_price, _ = cat.get("items", {}).get(svc_key, ("—", "—", "—"))
    mst = MASTERS.get(mst_key, {}) if mst_key != "any" else {"name": "Любой свободный"}

    await q.edit_message_text(
        f"✅ <b>Запись подтверждена!</b>\n\n"
        f"💅 Услуга: {svc_name} — {svc_price}\n"
        f"👩 Мастер: {mst.get('name','')}\n"
        f"🕐 Время: {time}\n\n"
        f"Напомним за 2 часа. Если нужно перенести — {OWNER_NICK}",
        parse_mode="HTML"
    )
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"📅 <b>Новая запись!</b>\n"
            f"Клиент: {user.full_name} (@{user.username or '—'})\n"
            f"Услуга: {svc_name} ({svc_price})\n"
            f"Мастер: {mst.get('name','')}\n"
            f"Время: {time}",
            parse_mode="HTML"
        )
    except Exception: pass

async def masters(update: Update, context):
    q = update.callback_query; await q.answer()
    text = "👩 <b>Наши мастера:</b>\n\n"
    for m in MASTERS.values():
        text += f"<b>{m['name']}</b> — {m['spec']}\n"
    kb = [
        [InlineKeyboardButton("📅 Записаться", callback_data="book")],
        [InlineKeyboardButton("◀️ Назад",      callback_data="back")],
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def reviews(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "⭐⭐⭐⭐⭐\n\n"
        "<i>«Анна — лучший мастер! Маникюр держится 3 недели без сколов»</i> — Юля\n\n"
        "<i>«Записалась к Марии на брови — просто идеально»</i> — Света\n\n"
        "<i>«Очень уютная студия, буду приходить постоянно»</i> — Катя",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )

async def address(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "📍 <b>Адрес:</b> ул. Примерная, 10\n\n"
        "🕐 <b>Время работы:</b> 10:00 – 21:00 (без выходных)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )

async def back(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [
        [InlineKeyboardButton("💅 Услуги и цены",   callback_data="services")],
        [InlineKeyboardButton("📅 Записаться",       callback_data="book")],
        [InlineKeyboardButton("👩 Наши мастера",     callback_data="masters")],
        [InlineKeyboardButton("⭐ Отзывы",           callback_data="reviews")],
        [InlineKeyboardButton("📍 Адрес",            callback_data="address")],
    ]
    await q.edit_message_text("Чем помочь?", reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(services,   pattern="^services$"))
    app.add_handler(CallbackQueryHandler(service_cat,pattern="^scat_"))
    app.add_handler(CallbackQueryHandler(book,       pattern="^book$"))
    app.add_handler(CallbackQueryHandler(book_cat,   pattern="^bcat_"))
    app.add_handler(CallbackQueryHandler(book_svc,   pattern="^bsvc_"))
    app.add_handler(CallbackQueryHandler(book_master,pattern="^bmst_"))
    app.add_handler(CallbackQueryHandler(book_time,  pattern="^btime_"))
    app.add_handler(CallbackQueryHandler(masters,    pattern="^masters$"))
    app.add_handler(CallbackQueryHandler(reviews,    pattern="^reviews$"))
    app.add_handler(CallbackQueryHandler(address,    pattern="^address$"))
    app.add_handler(CallbackQueryHandler(back,       pattern="^back$"))
    print("Красота-бот запущен ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
