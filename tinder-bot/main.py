import os
from dotenv import load_dotenv

from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, CommandHandler

from classes.gpt import *
from classes.util import *


class TelegramBot:
    def __init__(self):
        self.dialog = Dialog()
        self.gpt_property = GPTProperty(dialog=self.dialog)
        self.date_property = DateProperty(dialog=self.dialog)
        self.messages_property = MessageProperty(dialog=self.dialog)
        self.profile_property = ProfileProperty(dialog=self.dialog)
        self.opener_property = OpenerProperty(dialog=self.dialog)

    async def hello(self, update, context):
        if self.dialog.mode == "gpt":
            await self.gpt_property.gpt_dialog(update, context)
        elif self.dialog.mode == "profile":
            await self.profile_property.profile_dialog(update, context)
        elif self.dialog.mode == "date":
            await self.date_property.date_dialog(update, context)
        elif self.dialog.mode == "opener":
            await self.opener_property.opener_dialog(update, context)
        elif self.dialog.mode == "message":
            await self.messages_property.message_dialog(update, context)
        else:
            await send_text(update, context, "Привет!")
            await send_text(update, context, "Как дела, *дружище*?")
            await send_text(update, context, "Ты написал " + update.message.text)
            await send_photo(update, context, "avatar_main")
            await send_text_buttons(update, context, "Запустить процесс?", {
                "start": "Запустить",
                "stop": "Остановить"
            })

    @staticmethod
    async def hello_button(update, context):
        query = update.callback_query.data
        await update.callback_query.answer()

        if query == "start":
            await send_text(update, context, "Процесс запущен")
        else:
            await send_text(update, context, "Процесс остановлен")

    async def start(self, update, context):
        self.dialog.mode = "main"
        text = load_message("main")
        await send_photo(update, context, "main")
        await send_text(update, context, text)
        await show_main_menu(update, context, {
            "start": "главное меню бота",
            "profile": "генерация Tinder-профиля 😎",
            "opener": "сообщение для знакомства 🥰",
            "message": "переписка от вашего имени 😈",
            "date": "переписка со звездами 🔥",
            "gpt": "задать вопрос ChatGPT  🧠",
        })

    def add_handlers(self, app):
        """Handlers for telegram."""

        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("gpt", self.gpt_property.gpt))
        app.add_handler(CommandHandler("profile", self.profile_property.profile))
        app.add_handler(CommandHandler("opener", self.opener_property.opener))
        app.add_handler(CommandHandler("date", self.date_property.date))
        app.add_handler(CommandHandler("message", self.messages_property.message))

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.hello))  # отключаем команды

        app.add_handler(CallbackQueryHandler(self.date_property.date_button, pattern="^date_.*"))
        app.add_handler(CallbackQueryHandler(self.messages_property.message_button, pattern="^message_.*"))

        app.add_handler(CallbackQueryHandler(self.hello_button))


class Property:
    def __init__(self, dialog):
        self.dialog = dialog


class MessageProperty(Property):
    """Message property"""

    async def message(self, update, context):
        self.dialog.mode = "message"
        text = load_message("message")
        await send_photo(update, context, "message")
        await send_text(update, context, text)
        await send_text_buttons(update, context, text, {
            "message_next": "Следующее сообщение",
            "message_date": "Пригласить на свидание",
        })
        self.dialog.list.clear()

    async def message_dialog(self, update, context):
        text = update.message.text
        self.dialog.list.append(text)

    async def message_button(self, update, context):
        query = update.callback_query.data
        await update.callback_query.answer()

        prompt = load_prompt(query)
        user_chat_history = "\n\n".join(self.dialog.list)
        my_message = await send_text(update, context, "ChatGPT думает над вариантами ответа...")
        answer = await chatgpt.send_question(prompt, user_chat_history)
        await my_message.edit_text(answer)


class DateProperty(Property):
    """Date property of the bot."""

    async def date(self, update, context):
        self.dialog.mode = "date"
        await send_text(update, context, "date")
        text = load_message("date")
        await send_text_buttons(update, context, text, {
            "date_grande": "Ариана Гранде",
            "date_robbie": "Марго Робби",
            "date_zendaya": "Зендея",
            "date_gosling": "Райан Гослинг",
            "date_hardy": "Том Харди",
        })
        await send_photo(update, context, "date")

    @staticmethod
    async def date_button(update, context):
        # Обработчик
        query = update.callback_query.data
        await update.callback_query.answer()

        await send_photo(update, context, query)
        await send_text(update, context, " Отличный выбор! Пригласите девушку (парня) на свидание за 5 сообщений")

        prompt = load_prompt(query)
        chatgpt.set_prompt(prompt)

        # await send_html(update, context, query)

    @staticmethod
    async def date_dialog(update, context):
        # Диалог
        text = update.message.text
        my_message = await send_text(update, context, "Девушка набирает текст...")
        answer = await chatgpt.add_message(text)
        await my_message.edit_text(answer)


class GPTProperty(Property):
    """GPT Property"""

    async def gpt(self, update, context):
        self.dialog.mode = "gpt"
        await send_photo(update, context, "gpt")
        await send_text(update, context, "Напишите сообщение *ChatGPT*:")

    @staticmethod
    async def gpt_dialog(update, context):
        my_message = await send_text(update, context, "ChatGPT думает. Ожидайте...")
        prompt = load_prompt("gpt")
        text = update.message.text
        answer = await chatgpt.send_question(prompt, text)
        await my_message.edit_text(answer)


class ProfileProperty(Property):
    """Profile property"""

    async def profile(self, update, context):
        self.dialog.mode = "profile"
        text = load_message("profile")
        await send_photo(update, context, "profile")
        await send_text(update, context, text)

        self.dialog.user.clear()
        self.dialog.count = 0
        await send_text(update, context, "Сколько вам лет?")

    async def profile_dialog(self, update, context):
        text = update.message.text
        self.dialog.count += 1

        if self.dialog.count == 1:
            self.dialog.user["age"] = text
            await send_text(update, context, "Кем вы работаете?")
        elif self.dialog.count == 2:
            self.dialog.user["occupation"] = text
            await send_text(update, context, "У вас есть хобби?")
        elif self.dialog.count == 3:
            self.dialog.user["hobby"] = text
            await send_text(update, context, "Что вам НЕ нравится в людях?")
        elif self.dialog.count == 4:
            self.dialog.user["annoys"] = text
            await send_text(update, context, "Цель знакомства?")
        elif self.dialog.count == 5:
            self.dialog.user["goals"] = text

        prompt = load_prompt("profile")
        user_info = dialog_user_info_to_str(self.dialog.user)
        answer = await chatgpt.send_question(prompt, user_info)
        await send_text(update, context, answer)


class OpenerProperty(Property):
    """Opener profile."""

    async def opener(self, update, context):
        self.dialog.mode = "opener"
        text = load_message("opener")
        await send_photo(update, context, "opener")
        await send_text(update, context, text)

        self.dialog.user.clear()
        self.dialog.count = 0
        await send_text(update, context, "Как тебя зовут?")

    async def opener_dialog(self, update, context):
        text = update.message.text
        self.dialog.count += 1

        if self.dialog.count == 1:
            self.dialog.user["name"] = text
            await send_text(update, context, "Сколько лет?")
        elif self.dialog.count == 2:
            self.dialog.user["occupation"] = text
            await send_text(update, context, "Внешность 1-10 баллов?")
        elif self.dialog.count == 3:
            self.dialog.user["hobby"] = text
            await send_text(update, context, "Кем работаешь?")
        elif self.dialog.count == 4:
            self.dialog.user["annoys"] = text
            await send_text(update, context, "Цель знакомства?")
        elif self.dialog.count == 5:
            self.dialog.user["goals"] = text

        prompt = load_prompt("opener")
        user_info = dialog_user_info_to_str(self.dialog.user)
        answer = await chatgpt.send_question(prompt, user_info)
        await send_text(update, context, answer)


load_dotenv()

OPEN_API_TOKEN = os.getenv("OPEN_API_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
chatgpt = ChatGptService(token=OPEN_API_TOKEN)
bot = TelegramBot()

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
bot.add_handlers(app)
app.run_polling()
