from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN  = "ВСТАВЬ_ТОКЕН"
OWNER_ID   = 123456789
OWNER_NICK = "@твой_ник"

MASTERS = {
    "alex": {"name": "Алексей", "spec": "Классика, fade, борода", "emoji": "✂️"},
    "ivan": {"name": "Иван",    "spec": "Модельные стрижки, кератин", "emoji": "💈"},
}
SERVICES = {
    "cut":   {"name": "Стрижка",        "price": "800 ₽",  "time": "45 мин"},
    "beard": {"name": "Борода",         "price": "500 ₽",  "time": "30 мин"},
    "combo": {"name": "Стрижка + борода","price": "1 200 ₽","time": "60 мин"},
}
SLOTS = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "18:00", "19:00"]

async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("✂️ Записаться", callback_data="book")],
        [InlineKeyboardButton("💰 Цены",       callback_data="prices")],
        [InlineKeyboardButton("📍 Адрес и время работы", callback_data="address")],
        [InlineKeyboardButton("📞 Связаться",  callback_data="contact")],
    ]
    await update.message.reply_text(
        "Привет! 👋 Добро пожаловать в барбершоп.\n\nЧто тебя интересует?",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def prices(update: Update, context):
    q = update.callback_query; await q.answer()
    text = "💰 <b>Наши услуги и цены:</b>\n\n"
    for s in SERVICES.values():
        text += f"• {s['name']} — {s['price']} ({s['time']})\n"
    kb = [[InlineKeyboardButton("✂️ Записаться", callback_data="book")],
          [InlineKeyboardButton("◀️ Назад",      callback_data="back")]]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def address(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "📍 <b>Адрес:</b> ул. Ленина, 42\n\n"
        "🕐 <b>Режим работы:</b>\n"
        "Пн–Пт: 10:00 – 20:00\n"
        "Сб–Вс: 10:00 – 18:00",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )

async def book_step1(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(f"{s['name']} — {s['price']}", callback_data=f"svc_{k}")]
          for k, s in SERVICES.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text("Выбери услугу:", reply_markup=InlineKeyboardMarkup(kb))

async def book_step2(update: Update, context):
    q = update.callback_query; await q.answer()
    context.user_data["service"] = q.data.replace("svc_", "")
    kb = [[InlineKeyboardButton(f"{m['emoji']} {m['name']} — {m['spec']}", callback_data=f"mst_{k}")]
          for k, m in MASTERS.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="book")])
    await q.edit_message_text("Выбери мастера:", reply_markup=InlineKeyboardMarkup(kb))

async def book_step3(update: Update, context):
    q = update.callback_query; await q.answer()
    context.user_data["master"] = q.data.replace("mst_", "")
    kb = [[InlineKeyboardButton(t, callback_data=f"time_{t}")] for t in SLOTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data=f"svc_{context.user_data['service']}")])
    await q.edit_message_text("Выбери время:", reply_markup=InlineKeyboardMarkup(kb))

async def book_confirm(update: Update, context):
    q = update.callback_query; await q.answer()
    user = q.from_user
    time    = q.data.replace("time_", "")
    svc_key = context.user_data.get("service", "")
    mst_key = context.user_data.get("master", "")
    svc = SERVICES.get(svc_key, {}); mst = MASTERS.get(mst_key, {})

    await q.edit_message_text(
        f"✅ <b>Запись подтверждена!</b>\n\n"
        f"📋 Услуга: {svc.get('name','')}\n"
        f"👤 Мастер: {mst.get('name','')}\n"
        f"🕐 Время: {time}\n\n"
        f"Напомним за 2 часа до визита.\nЕсли нужно перенести — {OWNER_NICK}",
        parse_mode="HTML"
    )
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"📅 <b>Новая запись!</b>\n"
                 f"Клиент: {user.full_name} (@{user.username or '—'})\n"
                 f"Услуга: {svc.get('name','')}\n"
                 f"Мастер: {mst.get('name','')}\n"
                 f"Время: {time}",
            parse_mode="HTML"
        )
    except Exception: pass

async def contact(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        f"📞 Связаться с нами:\nTelegram: {OWNER_NICK}\n",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
    )

async def back(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [
        [InlineKeyboardButton("✂️ Записаться", callback_data="book")],
        [InlineKeyboardButton("💰 Цены",       callback_data="prices")],
        [InlineKeyboardButton("📍 Адрес",      callback_data="address")],
        [InlineKeyboardButton("📞 Связаться",  callback_data="contact")],
    ]
    await q.edit_message_text("Что тебя интересует?", reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(book_step1,   pattern="^book$"))
    app.add_handler(CallbackQueryHandler(book_step2,   pattern="^svc_"))
    app.add_handler(CallbackQueryHandler(book_step3,   pattern="^mst_"))
    app.add_handler(CallbackQueryHandler(book_confirm, pattern="^time_"))
    app.add_handler(CallbackQueryHandler(prices,       pattern="^prices$"))
    app.add_handler(CallbackQueryHandler(address,      pattern="^address$"))
    app.add_handler(CallbackQueryHandler(contact,      pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(back,         pattern="^back$"))
    print("Барбер-бот запущен ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
