import os
from dotenv import load_dotenv

from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, CommandHandler

from gpt import *
from util import *

async def hello(update, context):
    if dialog.mode == "gpt":
        await gpt_dialog(update, context)
    else:
        await send_text(update, context, "Привет!")
        await send_text(update, context, "Как дела, *дружище*?")
        await send_text(update, context, "Ты написал " + update.message.text)
    await show_main_menu(update, context, {
        "start": "главное меню бота",
        "profile": "генерация Tinder-профиля 😎",
        "opener": "сообщение для знакомства 🥰",
        "message": "переписка от вашего имени 😈",
        "date": "переписка со звездами 🔥",
        "gpt": "задать вопрос ChatGPT  🧠",
    })

async def start(update, context):
    dialog.mode = "main"
    text = load_message("main")
    await send_photo(update, context, "main")
    await send_text(update, context, text)



async def hello_button(update, context):
    dialog.mode = "main"
    query = update.callback_query.data   #код кнопки
    await update.callback_query.answer() #помечаем что обработали нажатие на кнопку
    await send_text(update, context, "Вы нажали на кнопку " + query)

async def gpt(update, context):
    dialog.mode = "gpt"
    await send_photo(update, context, "gpt")
    await send_text(update, context, "Напишите сообщение *ChatGPT*:")


async def gpt_dialog(update, context):
    prompt = load_prompt("gpt")
    text = update.message.text
    answer = await chatgpt.send_question(prompt,  text)
    await send_text(update, context, answer)

load_dotenv()

OPEN_API_TOKEN = os.getenv("OPEN_API_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

dialog = Dialog()
dialog.mode = "main"

chatgpt = ChatGptService(token=OPEN_API_TOKEN)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, hello)) # отключаем команды
app.add_handler(CommandHandler("gpt", gpt))
app.add_handler(CallbackQueryHandler(hello_button))
app.run_polling()
