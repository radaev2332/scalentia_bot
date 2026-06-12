from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN  = "ВСТАВЬ_ТОКЕН"
OWNER_ID   = 123456789
OWNER_NICK = "@твой_ник"

COURSES = {
    "c1": {
        "name": "Курс 1",
        "emoji": "📚",
        "price": "4 900 ₽",
        "old_price": "7 900 ₽",
        "duration": "4 недели",
        "desc": "Описание первого курса. Что получит студент.",
        "modules": ["Модуль 1: Основы", "Модуль 2: Практика", "Модуль 3: Проект", "Модуль 4: Результат"],
    },
    "c2": {
        "name": "Курс 2",
        "emoji": "🎯",
        "price": "7 900 ₽",
        "old_price": None,
        "duration": "8 недель",
        "desc": "Описание второго курса. Для кого и что даст.",
        "modules": ["Модуль 1", "Модуль 2", "Модуль 3", "Модуль 4", "Модуль 5"],
    },
    "c3": {
        "name": "Бесплатный мини-курс",
        "emoji": "🎁",
        "price": "Бесплатно",
        "old_price": None,
        "duration": "3 урока",
        "desc": "Вводный мини-курс. Познакомься с методикой.",
        "modules": ["Урок 1", "Урок 2", "Урок 3"],
    },
}

async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("🎁 Бесплатный урок",   callback_data="free_lesson")],
        [InlineKeyboardButton("📚 Все курсы",          callback_data="all_courses")],
        [InlineKeyboardButton("❓ Как это работает",   callback_data="how_it_works")],
        [InlineKeyboardButton("💬 Задать вопрос",      callback_data="ask")],
    ]
    await update.message.reply_text(
        "Привет! 👋\nДобро пожаловать в онлайн-школу.\n\n"
        "С чего начнём?",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def free_lesson(update: Update, context):
    q = update.callback_query; await q.answer()
    user = q.from_user
    await q.edit_message_text(
        "🎁 <b>Бесплатный урок</b>\n\n"
        "Напиши свой email — пришлю доступ к первому уроку прямо сейчас.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )
    context.user_data["expecting_email"] = True
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"👆 <b>Хочет бесплатный урок</b>\n"
            f"Клиент: {user.full_name} (@{user.username or '—'})",
            parse_mode="HTML"
        )
    except Exception: pass

async def all_courses(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(f"{v['emoji']} {v['name']} — {v['price']}", callback_data=f"course_{k}")]
          for k, v in COURSES.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text("Выбери курс:", reply_markup=InlineKeyboardMarkup(kb))

async def course_detail(update: Update, context):
    q = update.callback_query; await q.answer()
    key = q.data.replace("course_", "")
    c = COURSES.get(key, {})
    modules_text = "\n".join([f"  ✅ {m}" for m in c.get("modules", [])])
    old = f"~~{c['old_price']}~~ → " if c.get("old_price") else ""
    kb = [
        [InlineKeyboardButton(f"✅ Записаться — {c['price']}", callback_data=f"enroll_{key}")],
        [InlineKeyboardButton("◀️ К курсам", callback_data="all_courses")],
    ]
    await q.edit_message_text(
        f"{c['emoji']} <b>{c['name']}</b>\n\n"
        f"{c['desc']}\n\n"
        f"<b>Программа:</b>\n{modules_text}\n\n"
        f"⏱ Длительность: {c['duration']}\n"
        f"💰 Цена: {old}<b>{c['price']}</b>",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML"
    )

async def enroll(update: Update, context):
    q = update.callback_query; await q.answer()
    user = q.from_user
    key = q.data.replace("enroll_", "")
    c = COURSES.get(key, {})
    await q.edit_message_text(
        f"🎉 Отличный выбор!\n\n"
        f"Напиши свой email — пришлю счёт и доступ к курсу.\n{OWNER_NICK}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"course_{key}")]]),
    )
    context.user_data["expecting_email"] = True
    context.user_data["enrolling_course"] = c.get("name", "")
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"🎓 <b>ХОЧЕТ КУПИТЬ КУРС!</b>\n"
            f"Клиент: {user.full_name} (@{user.username or '—'})\n"
            f"Курс: {c.get('name','')} ({c.get('price','')})\n\n"
            f"⚡ Горячий лид!",
            parse_mode="HTML"
        )
    except Exception: pass

async def how_it_works(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "❓ <b>Как это работает:</b>\n\n"
        "1️⃣ Выбираешь курс и оплачиваешь\n"
        "2️⃣ Получаешь доступ к урокам сразу\n"
        "3️⃣ Учишься в своём темпе\n"
        "4️⃣ Задаёшь вопросы в чате\n"
        "5️⃣ Получаешь сертификат по итогам\n\n"
        "Доступ к урокам — навсегда.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Посмотреть курсы", callback_data="all_courses")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        ]),
        parse_mode="HTML"
    )

async def ask(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Напиши свой вопрос 👇")
    context.user_data["expecting_question"] = True

async def handle_text(update: Update, context):
    user = update.effective_user
    text = update.message.text
    if context.user_data.get("expecting_email"):
        context.user_data["expecting_email"] = False
        course = context.user_data.get("enrolling_course", "")
        await update.message.reply_text(
            f"✅ Принял! Пришлю доступ на {text} в течение часа.\n{OWNER_NICK}"
        )
        try:
            await context.bot.send_message(
                OWNER_ID,
                f"📧 <b>Email от клиента</b>\n"
                f"Клиент: {user.full_name} (@{user.username or '—'})\n"
                f"Email: {text}\n"
                f"Курс: {course or 'бесплатный урок'}",
                parse_mode="HTML"
            )
        except Exception: pass
    elif context.user_data.get("expecting_question"):
        context.user_data["expecting_question"] = False
        await update.message.reply_text(f"Вопрос получил! Отвечу скоро. {OWNER_NICK}")
        try:
            await context.bot.send_message(
                OWNER_ID,
                f"❓ <b>Вопрос</b>\nОт: {user.full_name} (@{user.username or '—'})\n{text}",
                parse_mode="HTML"
            )
        except Exception: pass

async def back(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [
        [InlineKeyboardButton("🎁 Бесплатный урок", callback_data="free_lesson")],
        [InlineKeyboardButton("📚 Все курсы",        callback_data="all_courses")],
        [InlineKeyboardButton("❓ Как это работает", callback_data="how_it_works")],
        [InlineKeyboardButton("💬 Задать вопрос",    callback_data="ask")],
    ]
    await q.edit_message_text("С чего начнём?", reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(free_lesson,   pattern="^free_lesson$"))
    app.add_handler(CallbackQueryHandler(all_courses,   pattern="^all_courses$"))
    app.add_handler(CallbackQueryHandler(course_detail, pattern="^course_"))
    app.add_handler(CallbackQueryHandler(enroll,        pattern="^enroll_"))
    app.add_handler(CallbackQueryHandler(how_it_works,  pattern="^how_it_works$"))
    app.add_handler(CallbackQueryHandler(ask,           pattern="^ask$"))
    app.add_handler(CallbackQueryHandler(back,          pattern="^back$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Онлайн-школа-бот запущен ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
