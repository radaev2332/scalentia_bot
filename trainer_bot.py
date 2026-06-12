from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN  = "ВСТАВЬ_ТОКЕН"
OWNER_ID   = 123456789
OWNER_NICK = "@твой_ник"

PROGRAMS = {
    "fat":     {"name": "Похудение",       "price": "2 900 ₽/мес", "desc": "Кардио + дефицит, 3 тренировки в неделю"},
    "muscle":  {"name": "Набор массы",     "price": "2 900 ₽/мес", "desc": "Силовые тренировки, план питания"},
    "home":    {"name": "Дома без железа", "price": "1 900 ₽/мес", "desc": "Только собственный вес, без зала"},
    "personal":{"name": "Личное ведение",  "price": "7 900 ₽/мес", "desc": "Индивидуальный план + ежедневная связь"},
}

async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("💪 Программы тренировок", callback_data="programs")],
        [InlineKeyboardButton("📅 Записаться на тренировку", callback_data="book_trial")],
        [InlineKeyboardButton("📊 Рассчитать калории", callback_data="calories")],
        [InlineKeyboardButton("💬 Задать вопрос тренеру", callback_data="ask")],
    ]
    await update.message.reply_text(
        "Привет! 💪\nЯ помогу достичь твоей фитнес-цели.\n\nС чего начнём?",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def programs(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(f"{p['name']} — {p['price']}", callback_data=f"prog_{k}")]
          for k, p in PROGRAMS.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text("Выбери программу:", reply_markup=InlineKeyboardMarkup(kb))

async def prog_detail(update: Update, context):
    q = update.callback_query; await q.answer()
    key = q.data.replace("prog_", "")
    p = PROGRAMS.get(key, {})
    kb = [
        [InlineKeyboardButton(f"✅ Хочу эту — {p['price']}", callback_data=f"buy_{key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="programs")],
    ]
    await q.edit_message_text(
        f"<b>{p['name']}</b>\n\n{p['desc']}\n\nСтоимость: <b>{p['price']}</b>",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML"
    )

async def buy_prog(update: Update, context):
    q = update.callback_query; await q.answer()
    user = q.from_user
    key = q.data.replace("buy_", "")
    p = PROGRAMS.get(key, {})
    await q.edit_message_text(
        f"🎉 Отличный выбор!\n\nОставь своё имя и я свяжусь с тобой сегодня чтобы начать.\n"
        f"Или напиши напрямую: {OWNER_NICK}"
    )
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"💰 <b>Хочет купить программу!</b>\n"
                 f"Клиент: {user.full_name} (@{user.username or '—'})\n"
                 f"Программа: {p['name']} ({p['price']})",
            parse_mode="HTML"
        )
    except Exception: pass

async def book_trial(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "Отлично! Первая пробная тренировка — <b>бесплатно</b>.\n\n"
        "Напиши своё имя и удобное время — я подберу слот 👇",
        parse_mode="HTML"
    )
    context.user_data["expecting_trial"] = True

async def calories(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "📊 <b>Быстрый расчёт:</b>\n\n"
        "Для похудения: вес × 28 = ккал/день\n"
        "Для поддержания: вес × 33 = ккал/день\n"
        "Для набора: вес × 38 = ккал/день\n\n"
        "<i>Пример: 80 кг для похудения = 80 × 28 = 2240 ккал</i>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )

async def ask(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Напиши свой вопрос тренеру 👇")
    context.user_data["expecting_question"] = True

async def handle_text(update: Update, context):
    user = update.effective_user
    text = update.message.text
    if context.user_data.get("expecting_trial"):
        context.user_data["expecting_trial"] = False
        await update.message.reply_text(f"✅ Принял! Напишу тебе сегодня чтобы согласовать время.\n{OWNER_NICK}")
        try:
            await context.bot.send_message(OWNER_ID,
                f"📅 <b>Хочет пробную тренировку!</b>\n"
                f"Клиент: {user.full_name} (@{user.username or '—'})\n"
                f"Сообщение: {text}", parse_mode="HTML")
        except Exception: pass
    elif context.user_data.get("expecting_question"):
        context.user_data["expecting_question"] = False
        await update.message.reply_text(f"Вопрос получил! Отвечу в течение нескольких часов. {OWNER_NICK}")
        try:
            await context.bot.send_message(OWNER_ID,
                f"❓ <b>Вопрос клиента</b>\n"
                f"Клиент: {user.full_name} (@{user.username or '—'})\n"
                f"Вопрос: {text}", parse_mode="HTML")
        except Exception: pass

async def back(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [
        [InlineKeyboardButton("💪 Программы тренировок", callback_data="programs")],
        [InlineKeyboardButton("📅 Пробная тренировка", callback_data="book_trial")],
        [InlineKeyboardButton("📊 Рассчитать калории", callback_data="calories")],
        [InlineKeyboardButton("💬 Задать вопрос", callback_data="ask")],
    ]
    await q.edit_message_text("С чего начнём?", reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(programs,   pattern="^programs$"))
    app.add_handler(CallbackQueryHandler(prog_detail,pattern="^prog_"))
    app.add_handler(CallbackQueryHandler(buy_prog,   pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(book_trial, pattern="^book_trial$"))
    app.add_handler(CallbackQueryHandler(calories,   pattern="^calories$"))
    app.add_handler(CallbackQueryHandler(ask,        pattern="^ask$"))
    app.add_handler(CallbackQueryHandler(back,       pattern="^back$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Тренер-бот запущен ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
