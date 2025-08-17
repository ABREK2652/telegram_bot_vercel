import os
import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ["TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])
ADMIN_ID = int(os.environ["ADMIN_ID"])

bot = Bot(TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

user_states = {}

def get_user_link(user):
    if user.username:
        return f"@{user.username}"
    else:
        return f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

# /start
def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("💳 1000 ₽ — 1 месяц", callback_data="plan_1000_1")],
        [InlineKeyboardButton("💳 2500 ₽ — 3 месяца", callback_data="plan_2500_3")],
        [InlineKeyboardButton("💳 5000 ₽ — 6 месяцев", callback_data="plan_5000_6")],
        [InlineKeyboardButton("💳 10 000 ₽ — 12 месяцев", callback_data="plan_10000_12")],
        [InlineKeyboardButton("📩 Помощь", url="https://t.me/Russian_2652")]
    ]
    update.message.reply_text(
        "💳 Выберите тариф и переведите указанную сумму на карту:\n"
        "📌 2204 3101 7224 7291 Получатель Татьяна Д. Банк Яндекс\n\n"
        "После перевода отправьте скриншот чека.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

dispatcher.add_handler(CommandHandler("start", start))

# Обработка callback от кнопок
def callback_handler(update: Update, context):
    query = update.callback_query
    query.answer()
    if query.data.startswith("plan_"):
        parts = query.data.split("_")
        price, months = parts[1], parts[2]
        user_id = query.from_user.id
        user_states[user_id] = {"state": "waiting_screenshot", "plan": f"{price}₽ / {months} мес."}

        keyboard = [
            [InlineKeyboardButton("✅ Я оплатил", callback_data="paid")],
            [InlineKeyboardButton("📩 Помощь", url="https://t.me/Russian_2652")]
        ]
        query.message.reply_text(
            f"📷 Отправьте скриншот оплаты тарифа {price}₽ за {months} мес.\n"
            "📌 2204 3101 7224 7291 Получатель Татьяна Д. Банк Яндекс\n\n"
            "После оплаты нажмите «Я оплатил».",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == "paid":
        user_id = query.from_user.id
        user_states[user_id] = "waiting_screenshot"
        query.message.reply_text("📷 Отправьте скриншот оплаты (фото или документ).")

dispatcher.add_handler(CallbackQueryHandler(callback_handler))

# Обработка фото/документа
def handle_file(update: Update, context):
    user_id = update.message.from_user.id
    state = user_states.get(user_id)
    if state == "waiting_screenshot":
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"approve_{user_id}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")]
        ]
        if update.message.photo:
            bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id,
                           caption=f"💰 Заявка от {get_user_link(update.message.from_user)}",
                           reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        elif update.message.document:
            bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id,
                              caption=f"💰 Заявка от {get_user_link(update.message.from_user)}",
                              reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        user_states[user_id] = None

dispatcher.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_file))

# Vercel handler
def handler(request):
    import json
    if request.method == "POST":
        data = json.loads(request.data)
        update = Update.de_json(data, bot)
        dispatcher.process_update(update)
        return {"status": 200}
    return {"status": 200, "body": "Bot is running!"}
