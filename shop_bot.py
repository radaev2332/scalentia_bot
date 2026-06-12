from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN  = "ВСТАВЬ_ТОКЕН"
OWNER_ID   = 123456789
OWNER_NICK = "@твой_ник"

CATALOG = {
    "cat1": {
        "name": "Категория 1",
        "emoji": "📦",
        "products": {
            "p1": {"name": "Товар 1", "price": "990 ₽",  "desc": "Описание товара 1"},
            "p2": {"name": "Товар 2", "price": "1 490 ₽", "desc": "Описание товара 2"},
            "p3": {"name": "Товар 3", "price": "2 200 ₽", "desc": "Описание товара 3"},
        }
    },
    "cat2": {
        "name": "Категория 2",
        "emoji": "🎁",
        "products": {
            "p4": {"name": "Товар 4", "price": "590 ₽",  "desc": "Описание товара 4"},
            "p5": {"name": "Товар 5", "price": "1 100 ₽", "desc": "Описание товара 5"},
        }
    },
    "cat3": {
        "name": "Хиты продаж",
        "emoji": "🔥",
        "products": {
            "p1": {"name": "Товар 1", "price": "990 ₽",  "desc": "Описание товара 1"},
            "p5": {"name": "Товар 5", "price": "1 100 ₽", "desc": "Описание товара 5"},
        }
    },
}

DELIVERY = {
    "courier": "Курьер (1–2 дня) — 300 ₽",
    "pickup":  "Самовывоз — бесплатно",
    "post":    "Почта России (3–7 дней) — 250 ₽",
}

def get_cart_text(cart):
    if not cart:
        return "Корзина пуста"
    lines = []
    total = 0
    for item in cart:
        lines.append(f"• {item['name']} — {item['price']}")
        try:
            total += int(item['price'].replace(" ","").replace("₽",""))
        except Exception: pass
    return "\n".join(lines) + f"\n\n<b>Итого: ~{total:,} ₽</b>".replace(",", " ")

async def start(update: Update, context):
    context.user_data.setdefault("cart", [])
    cart_count = len(context.user_data["cart"])
    cart_label = f"🛒 Корзина ({cart_count})" if cart_count else "🛒 Корзина"
    kb = [
        [InlineKeyboardButton("🛍️ Каталог",       callback_data="catalog")],
        [InlineKeyboardButton(cart_label,           callback_data="cart")],
        [InlineKeyboardButton("🔥 Акции",           callback_data="sales")],
        [InlineKeyboardButton("📦 Мой заказ",       callback_data="my_order")],
        [InlineKeyboardButton("💬 Написать нам",    callback_data="contact")],
    ]
    await update.message.reply_text(
        "Привет! 👋 Добро пожаловать в наш магазин.\n\nЧто ищешь?",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def catalog(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(f"{v['emoji']} {v['name']}", callback_data=f"cat_{k}")]
          for k, v in CATALOG.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text("Выбери категорию:", reply_markup=InlineKeyboardMarkup(kb))

async def show_category(update: Update, context):
    q = update.callback_query; await q.answer()
    key = q.data.replace("cat_", "")
    cat = CATALOG.get(key, {})
    kb = [[InlineKeyboardButton(f"{p['name']} — {p['price']}", callback_data=f"prod_{key}_{pk}")]
          for pk, p in cat.get("products", {}).items()]
    kb.append([InlineKeyboardButton("◀️ К категориям", callback_data="catalog")])
    await q.edit_message_text(
        f"{cat.get('emoji','')} <b>{cat.get('name','')}</b>\n\nВыбери товар:",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML"
    )

async def show_product(update: Update, context):
    q = update.callback_query; await q.answer()
    _, cat_key, prod_key = q.data.split("_", 2)
    prod = CATALOG.get(cat_key, {}).get("products", {}).get(prod_key, {})
    kb = [
        [InlineKeyboardButton("🛒 Добавить в корзину", callback_data=f"addcart_{cat_key}_{prod_key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"cat_{cat_key}")],
    ]
    await q.edit_message_text(
        f"<b>{prod.get('name','')}</b>\n\n"
        f"{prod.get('desc','')}\n\n"
        f"Цена: <b>{prod.get('price','')}</b>",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML"
    )

async def add_to_cart(update: Update, context):
    q = update.callback_query; await q.answer()
    _, cat_key, prod_key = q.data.split("_", 2)
    prod = CATALOG.get(cat_key, {}).get("products", {}).get(prod_key, {})
    context.user_data.setdefault("cart", []).append(prod)
    cart_count = len(context.user_data["cart"])
    kb = [
        [InlineKeyboardButton(f"🛒 Корзина ({cart_count})", callback_data="cart")],
        [InlineKeyboardButton("🛍️ Продолжить покупки",     callback_data="catalog")],
    ]
    await q.edit_message_text(
        f"✅ <b>{prod.get('name','')} добавлен в корзину!</b>",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML"
    )

async def show_cart(update: Update, context):
    q = update.callback_query; await q.answer()
    cart = context.user_data.get("cart", [])
    text = "🛒 <b>Твоя корзина:</b>\n\n" + get_cart_text(cart)
    kb = []
    if cart:
        kb.append([InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")])
        kb.append([InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def clear_cart(update: Update, context):
    q = update.callback_query; await q.answer()
    context.user_data["cart"] = []
    await q.edit_message_text(
        "Корзина очищена.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ К каталогу", callback_data="catalog")]])
    )

async def checkout(update: Update, context):
    q = update.callback_query; await q.answer()
    kb = [[InlineKeyboardButton(label, callback_data=f"dlv_{key}")]
          for key, label in DELIVERY.items()]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="cart")])
    await q.edit_message_text("Как доставить?", reply_markup=InlineKeyboardMarkup(kb))

async def delivery_chosen(update: Update, context):
    q = update.callback_query; await q.answer()
    dlv_key = q.data.replace("dlv_", "")
    context.user_data["delivery"] = DELIVERY.get(dlv_key, "")
    await q.edit_message_text(
        "Напиши своё имя и адрес доставки (или 'самовывоз') 👇"
    )
    context.user_data["expecting_address"] = True

async def handle_text(update: Update, context):
    user = update.effective_user
    text = update.message.text

    if context.user_data.get("expecting_address"):
        context.user_data["expecting_address"] = False
        cart   = context.user_data.get("cart", [])
        delivery = context.user_data.get("delivery", "")
        cart_text = get_cart_text(cart)

        await update.message.reply_text(
            f"✅ <b>Заказ оформлен!</b>\n\n"
            f"{cart_text}\n\n"
            f"📦 Доставка: {delivery}\n"
            f"📍 Адрес: {text}\n\n"
            f"Свяжусь с тобой для подтверждения оплаты в течение 1 часа.\n{OWNER_NICK}",
            parse_mode="HTML"
        )
        try:
            await context.bot.send_message(
                OWNER_ID,
                f"🛒 <b>НОВЫЙ ЗАКАЗ</b>\n"
                f"Клиент: {user.full_name} (@{user.username or '—'})\n"
                f"ID: <code>{user.id}</code>\n\n"
                f"{cart_text}\n\n"
                f"Доставка: {delivery}\n"
                f"Адрес: {text}",
                parse_mode="HTML"
            )
        except Exception: pass
        context.user_data["cart"] = []

    elif context.user_data.get("expecting_contact"):
        context.user_data["expecting_contact"] = False
        await update.message.reply_text(f"Сообщение получил! Отвечу скоро. {OWNER_NICK}")
        try:
            await context.bot.send_message(
                OWNER_ID,
                f"💬 <b>Сообщение от клиента</b>\n"
                f"Клиент: {user.full_name} (@{user.username or '—'})\n"
                f"Текст: {text}",
                parse_mode="HTML"
            )
        except Exception: pass

async def sales(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "🔥 <b>Акции</b>\n\n"
        "• Скидка 15% на первый заказ — промокод <code>FIRST15</code>\n"
        "• При заказе от 3 000 ₽ — бесплатная доставка\n"
        "• Подпишись на канал — узнай первым о новинках",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
        parse_mode="HTML"
    )

async def my_order(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        f"📦 Чтобы узнать статус заказа — напиши нам напрямую: {OWNER_NICK}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]]),
    )

async def contact(update: Update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Напиши свой вопрос 👇")
    context.user_data["expecting_contact"] = True

async def back(update: Update, context):
    q = update.callback_query; await q.answer()
    cart_count = len(context.user_data.get("cart", []))
    cart_label = f"🛒 Корзина ({cart_count})" if cart_count else "🛒 Корзина"
    kb = [
        [InlineKeyboardButton("🛍️ Каталог",    callback_data="catalog")],
        [InlineKeyboardButton(cart_label,        callback_data="cart")],
        [InlineKeyboardButton("🔥 Акции",        callback_data="sales")],
        [InlineKeyboardButton("📦 Мой заказ",    callback_data="my_order")],
        [InlineKeyboardButton("💬 Написать нам", callback_data="contact")],
    ]
    await q.edit_message_text("Чем помочь?", reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(catalog,         pattern="^catalog$"))
    app.add_handler(CallbackQueryHandler(show_category,   pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_product,    pattern="^prod_"))
    app.add_handler(CallbackQueryHandler(add_to_cart,     pattern="^addcart_"))
    app.add_handler(CallbackQueryHandler(show_cart,       pattern="^cart$"))
    app.add_handler(CallbackQueryHandler(clear_cart,      pattern="^clear_cart$"))
    app.add_handler(CallbackQueryHandler(checkout,        pattern="^checkout$"))
    app.add_handler(CallbackQueryHandler(delivery_chosen, pattern="^dlv_"))
    app.add_handler(CallbackQueryHandler(sales,           pattern="^sales$"))
    app.add_handler(CallbackQueryHandler(my_order,        pattern="^my_order$"))
    app.add_handler(CallbackQueryHandler(contact,         pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(back,            pattern="^back$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Магазин-бот запущен ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
