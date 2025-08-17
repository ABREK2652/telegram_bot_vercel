from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import datetime

TOKEN = "8425955011:AAHeowquUceZtWHCW7iB7RfQhwnWlH4vWv0"
CHAT_ID = -1002863526087
ADMIN_ID = 634560479

user_states = {}  # {user_id: state}

def get_user_link(user):
    if user.username:
        return f"@{user.username}"
    else:
        return f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 1000 ₽ — 1 месяц", callback_data="plan_1000_1")],
        [InlineKeyboardButton("💳 2500 ₽ — 3 месяца", callback_data="plan_2900_3")],
        [InlineKeyboardButton("💳 5000 ₽ — 6 месяцев", callback_data="plan_5500_6")],
        [InlineKeyboardButton("💳 10 000 ₽ — 12 месяцев", callback_data="plan_10000_12")],
        [InlineKeyboardButton("📩 Помощь", url="https://t.me/Russian_2652")]
    ]
    await update.message.reply_text(
        "💳 Выберите тариф и переведите указанную сумму на карту:\n"
        "📌 2204 3101 7224 7291 Получатель Татьяна Д. Банк получателя Яндекс\n\n"
        "После перевода отправьте скриншот чека.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# выбор тарифа
async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")  # ["plan", "1000", "1"]
    price = parts[1]
    months = parts[2]

    user_id = query.from_user.id
    user_states[user_id] = {"state": "waiting_screenshot", "plan": f"{price}₽ / {months} мес."}

    await query.message.reply_text(  # ✅ заменили update.message на query.message
        f"📷 Отправьте скриншот оплаты тарифа {price}₽ за {months} мес.\n"
        "📌 2204 3101 7224 7291"
    )
    # выбор тарифа
async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")  # ["plan", "1000", "1"]
    price = parts[1]
    months = parts[2]

    user_id = query.from_user.id
    user_states[user_id] = {"state": "waiting_screenshot", "plan": f"{price}₽ / {months} мес."}

    keyboard = [
        [InlineKeyboardButton("✅ Я оплатил", callback_data="paid")],
        [InlineKeyboardButton("📩 Помощь", url="https://t.me/Russian_2652")]
    ]

    await query.message.reply_text(
        f"📷 Отправьте скриншот оплаты тарифа {price}₽ за {months} мес.\n"
        "📌 2204 3101 7224 7291 Получатель Татьяна Д. Банк Яндекс\n\n"
        "После оплаты нажмите «Я оплатил».",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# "Я оплатил"
async def paid_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_states[user_id] = "waiting_screenshot"
    await query.message.reply_text("📷 Отправьте скриншот оплаты (фото или документ).")

# Обработка фото/документа
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = user_states.get(user_id)

    if state == "waiting_screenshot":
        kb = [
            [InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"approve_{user_id}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")]
        ]

        if update.message.photo:
            msg = await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=update.message.photo[-1].file_id,
                caption=f"💰 Заявка от {get_user_link(update.message.from_user)}",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="HTML"
            )
        elif update.message.document:
            msg = await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=update.message.document.file_id,
                caption=f"💰 Заявка от {get_user_link(update.message.from_user)}",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="HTML"
            )
        else:
            return

        user_states[user_id] = None
        user_states[f"admin_msg_{user_id}"] = msg.message_id

# Подтверждение оплаты
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[1])

    expire_time = datetime.datetime.now() + datetime.timedelta(days=30)
    invite_link = await context.bot.create_chat_invite_link(
        chat_id=CHAT_ID,
        expire_date=expire_time,
        member_limit=1
    )
    await context.bot.send_message(chat_id=user_id, text=f"🎉 Ваша ссылка для доступа: {invite_link.invite_link}")

    # Удаляем заявку у админа
    admin_msg_id = user_states.pop(f"admin_msg_{user_id}", None)
    if admin_msg_id:
        await context.bot.delete_message(chat_id=ADMIN_ID, message_id=admin_msg_id)

# Отклонение
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[1])
    await context.bot.send_message(chat_id=user_id, text="❌ Доступ отклонён. Причина: нет оплаты")

    # Удаляем заявку у админа
    admin_msg_id = user_states.pop(f"admin_msg_{user_id}", None)
    if admin_msg_id:
        await context.bot.delete_message(chat_id=ADMIN_ID, message_id=admin_msg_id)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(paid_pressed, pattern="^paid$"))
app.add_handler(CallbackQueryHandler(approve, pattern="^approve_"))
app.add_handler(CallbackQueryHandler(reject, pattern="^reject_"))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_file))
app.add_handler(CallbackQueryHandler(select_plan, pattern="^plan_"))

app.run_polling()