import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ─── НАСТРОЙКИ ───────────────────────────────────────────────────────────────
BOT_TOKEN   = "ВСТАВЬ_ТОКЕН_БОТА"        # токен от @BotFather
OWNER_ID    = 123456789                   # твой Telegram user_id (узнай у @userinfobot)
OWNER_NICK  = "@scalentia"               # твой ник для связи

# ─── СОСТОЯНИЯ ВОРОНКИ ───────────────────────────────────────────────────────
(
    S_START, S_PROBLEM, S_NICHE, S_BUDGET,
    S_CONTACT, S_CUSTOM_NAME, S_CUSTOM_DESC
) = range(7)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ─── ШАБЛОНЫ БОТОВ (витрина) ─────────────────────────────────────────────────
TEMPLATES = {
    "barber": {
        "name": "Барбершоп / Салон",
        "desc": "Онлайн-запись, напоминания, прайс, авто-ответы",
        "price": "8 900 ₽",
        "emoji": "✂️",
        "features": ["Запись на услугу", "Выбор мастера", "Напоминание за 2 часа",
                     "Прайс-лист", "Авто-ответ ночью", "Уведомление владельцу"]
    },
    "cafe": {
        "name": "Кофейня / Ресторан",
        "desc": "Меню, предзаказ, бронь стола, акции",
        "price": "9 900 ₽",
        "emoji": "☕",
        "features": ["Электронное меню", "Предзаказ с собой", "Бронь стола",
                     "Акции и спецпредложения", "Сбор отзывов", "Push-рассылка"]
    },
    "trainer": {
        "name": "Фитнес / Тренер",
        "desc": "Запись на тренировку, программы, оплата",
        "price": "7 900 ₽",
        "emoji": "🏋️",
        "features": ["Запись на тренировку", "Расписание занятий",
                     "Продажа программ", "Напоминания клиентам",
                     "База клиентов", "Авто-follow up"]
    },
    "shop": {
        "name": "Магазин / Товары",
        "desc": "Каталог, корзина, оформление заказа",
        "price": "11 900 ₽",
        "emoji": "🛍️",
        "features": ["Каталог товаров", "Корзина", "Оформление заказа",
                     "Статус доставки", "Уведомления о заказе", "Промокоды"]
    },
}

# ─── УВЕДОМЛЕНИЕ ВЛАДЕЛЬЦУ ───────────────────────────────────────────────────
async def notify_owner(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=text, parse_mode="HTML")
    except Exception as e:
        log.error(f"Notify owner error: {e}")

# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kb = [
        [InlineKeyboardButton("🤖 Готовые шаблоны ботов", callback_data="show_templates")],
        [InlineKeyboardButton("🎯 Бот под мой бизнес", callback_data="custom_bot")],
        [InlineKeyboardButton("💬 Задать вопрос", callback_data="ask_question")],
    ]
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я помогу автоматизировать твой бизнес через Telegram-бота.\n\n"
        "Что тебя интересует?",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    await notify_owner(
        context,
        f"👤 <b>Новый пользователь</b>\n"
        f"Имя: {user.full_name}\n"
        f"Ник: @{user.username or '—'}\n"
        f"ID: <code>{user.id}</code>"
    )
    return S_START

# ─── ВИТРИНА ШАБЛОНОВ ─────────────────────────────────────────────────────────
async def show_templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = []
    for key, t in TEMPLATES.items():
        kb.append([InlineKeyboardButton(
            f"{t['emoji']} {t['name']} — {t['price']}",
            callback_data=f"tpl_{key}"
        )])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back_start")])
    await query.edit_message_text(
        "Выбери шаблон — покажу что входит и как это выглядит:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return S_START

async def show_template_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("tpl_", "")
    t = TEMPLATES.get(key)
    if not t:
        return S_START

    features_text = "\n".join([f"  ✅ {f}" for f in t["features"]])
    kb = [
        [InlineKeyboardButton(f"💳 Купить за {t['price']}", callback_data=f"buy_{key}")],
        [InlineKeyboardButton("🎯 Хочу под свой бизнес", callback_data="custom_bot")],
        [InlineKeyboardButton("◀️ К шаблонам", callback_data="show_templates")],
    ]
    await query.edit_message_text(
        f"{t['emoji']} <b>{t['name']}</b>\n\n"
        f"{t['desc']}\n\n"
        f"<b>Что входит:</b>\n{features_text}\n\n"
        f"<b>Стоимость:</b> {t['price']}\n"
        f"<i>Настройка под твой бизнес + обучение включены</i>",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )
    return S_START

# ─── ПОКУПКА ШАБЛОНА ─────────────────────────────────────────────────────────
async def buy_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("buy_", "")
    t = TEMPLATES.get(key)
    context.user_data["chosen_template"] = key

    kb = [[InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid_{key}")],
          [InlineKeyboardButton("◀️ Назад", callback_data=f"tpl_{key}")]]

    await query.edit_message_text(
        f"💳 <b>Оплата — {t['name']}</b>\n\n"
        f"Сумма: <b>{t['price']}</b>\n\n"
        f"Переведи на:\n"
        f"<code>Тинькофф: +7 XXX XXX XX XX</code>\n"
        f"<i>Комментарий: Scalentia {t['name']}</i>\n\n"
        f"После оплаты нажми кнопку — я свяжусь с тобой в течение 1 часа.",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )
    return S_START

async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    key = query.data.replace("paid_", "")
    t = TEMPLATES.get(key, {})

    await query.edit_message_text(
        "✅ <b>Отлично! Заявка принята.</b>\n\n"
        "Я проверю оплату и свяжусь с тобой в течение 1 часа.\n"
        f"Пока можешь написать напрямую: {OWNER_NICK}",
        parse_mode="HTML"
    )
    await notify_owner(
        context,
        f"💰 <b>ОПЛАТА — {t.get('name','?')}</b>\n"
        f"Клиент: {user.full_name}\n"
        f"Ник: @{user.username or '—'}\n"
        f"ID: <code>{user.id}</code>\n"
        f"Шаблон: {t.get('name','?')} ({t.get('price','?')})\n\n"
        f"⚡ Свяжись в течение часа!"
    )
    return S_START

# ─── ВОРОНКА: ИНДИВИДУАЛЬНЫЙ БОТ ─────────────────────────────────────────────
async def custom_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("Услуги (барбер/салон/тренер)", callback_data="niche_services")],
        [InlineKeyboardButton("Магазин / товары", callback_data="niche_shop")],
        [InlineKeyboardButton("Онлайн-школа / курсы", callback_data="niche_edu")],
        [InlineKeyboardButton("Другое", callback_data="niche_other")],
    ]
    await query.edit_message_text(
        "Отлично! Расскажи немного о бизнесе.\n\n"
        "Какая у тебя ниша?",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return S_NICHE

async def niche_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["niche"] = query.data.replace("niche_", "")
    kb = [
        [InlineKeyboardButton("до 15 000 ₽", callback_data="budget_low")],
        [InlineKeyboardButton("15 000 – 40 000 ₽", callback_data="budget_mid")],
        [InlineKeyboardButton("от 40 000 ₽", callback_data="budget_high")],
        [InlineKeyboardButton("Не знаю — посоветуйте", callback_data="budget_unknown")],
    ]
    await query.edit_message_text(
        "Какой бюджет рассматриваешь?",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return S_BUDGET

async def budget_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["budget"] = query.data.replace("budget_", "")
    await query.edit_message_text(
        "Напиши кратко — что должен делать твой бот?\n\n"
        "<i>Например: принимать запись на стрижку, отвечать на вопросы о ценах, "
        "напоминать клиентам за день до визита</i>",
        parse_mode="HTML"
    )
    return S_CUSTOM_DESC

async def custom_desc_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    desc = update.message.text
    context.user_data["desc"] = desc
    niche_map = {
        "services": "Услуги", "shop": "Магазин",
        "edu": "Онлайн-школа", "other": "Другое"
    }
    budget_map = {
        "low": "до 15 000 ₽", "mid": "15–40 тыс ₽",
        "high": "от 40 000 ₽", "unknown": "не определился"
    }
    niche  = niche_map.get(context.user_data.get("niche", ""), "—")
    budget = budget_map.get(context.user_data.get("budget", ""), "—")

    await update.message.reply_text(
        "✅ <b>Принял заявку!</b>\n\n"
        "Свяжусь с тобой в течение 2 часов — обсудим детали и стоимость.\n"
        f"Если срочно — {OWNER_NICK}",
        parse_mode="HTML"
    )
    await notify_owner(
        context,
        f"🎯 <b>ЗАЯВКА — Индивидуальный бот</b>\n"
        f"Клиент: {user.full_name}\n"
        f"Ник: @{user.username or '—'}\n"
        f"ID: <code>{user.id}</code>\n"
        f"Ниша: {niche}\n"
        f"Бюджет: {budget}\n"
        f"Задача: {desc}\n\n"
        f"⚡ Горячий лид — свяжись сегодня!"
    )
    return ConversationHandler.END

# ─── ВОПРОС → ПЕРЕСЫЛКА ВЛАДЕЛЬЦУ ────────────────────────────────────────────
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Напиши свой вопрос — я передам его команде и ответим быстро 👇"
    )
    context.user_data["expecting_question"] = True
    return S_START

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if context.user_data.get("expecting_question"):
        context.user_data["expecting_question"] = False
        await update.message.reply_text(
            "Вопрос получил! Отвечу в течение нескольких часов.\n"
            f"Или напиши напрямую: {OWNER_NICK}"
        )
        await notify_owner(
            context,
            f"❓ <b>Вопрос от клиента</b>\n"
            f"Клиент: {user.full_name}\n"
            f"Ник: @{user.username or '—'}\n"
            f"ID: <code>{user.id}</code>\n\n"
            f"Вопрос: {text}"
        )
    else:
        kb = [[InlineKeyboardButton("Посмотреть шаблоны", callback_data="show_templates")]]
        await update.message.reply_text(
            "Не совсем понял 🙂 Лучше выбери что тебя интересует:",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def back_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("🤖 Готовые шаблоны ботов", callback_data="show_templates")],
        [InlineKeyboardButton("🎯 Бот под мой бизнес", callback_data="custom_bot")],
        [InlineKeyboardButton("💬 Задать вопрос", callback_data="ask_question")],
    ]
    await query.edit_message_text(
        "Что тебя интересует?",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return S_START

# ─── ОБРАБОТКА ОШИБОК ─────────────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Exception:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_user:
        user = update.effective_user
        await notify_owner(
            context,
            f"⚠️ <b>Ошибка в боте</b>\n"
            f"Клиент: {user.full_name} (@{user.username or '—'})\n"
            f"ID: <code>{user.id}</code>\n"
            f"Ошибка: <code>{context.error}</code>"
        )
        try:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "Что-то пошло не так 😔 Уже разбираюсь.\n"
                    f"Напиши напрямую: {OWNER_NICK}"
                )
        except Exception:
            pass

# ─── ЗАПУСК ───────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(custom_bot_start, pattern="^custom_bot$"),
        ],
        states={
            S_START: [
                CallbackQueryHandler(show_templates,        pattern="^show_templates$"),
                CallbackQueryHandler(custom_bot_start,      pattern="^custom_bot$"),
                CallbackQueryHandler(ask_question,          pattern="^ask_question$"),
                CallbackQueryHandler(show_template_detail,  pattern="^tpl_"),
                CallbackQueryHandler(buy_template,          pattern="^buy_"),
                CallbackQueryHandler(payment_done,          pattern="^paid_"),
                CallbackQueryHandler(back_start,            pattern="^back_start$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            ],
            S_NICHE: [
                CallbackQueryHandler(niche_chosen, pattern="^niche_"),
            ],
            S_BUDGET: [
                CallbackQueryHandler(budget_chosen, pattern="^budget_"),
            ],
            S_CUSTOM_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_desc_received),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False,
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)

    print("Scalentia бот запущен ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
