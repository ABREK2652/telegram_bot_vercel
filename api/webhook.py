import os
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from telegram.ext import MessageHandler, filters

TOKEN = os.environ["TOKEN"]
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# /start команда
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Бот работает через Vercel 🚀")

dispatcher.add_handler(CommandHandler("start", start))

# Обработка всех текстовых сообщений
def echo(update: Update, context: CallbackContext):
    update.message.reply_text(f"Вы написали: {update.message.text}")

dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Точка входа для Vercel
def handler(request):
    from telegram import Update
    import json

    if request.method == "POST":
        data = json.loads(request.data)
        update = Update.de_json(data, bot)
        dispatcher.process_update(update)
        return {"status": 200}
    return {"status": 200, "body": "Hello, this is Telegram bot!"}
