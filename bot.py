import asyncio
import re
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

TOKEN = "7847443343:AAGGEHCZCNFJSokQGZy8Vtc87zBa1KeMys4"

# Хранение напоминаний для всех пользователей
reminders = {}  # {user_id: [(datetime, message), ...]}

async def start(update: Update, context: CallbackContext) -> None:
    """Обрабатывает команду /start"""
    await update.message.reply_text("Привет! Просто напиши время и текст, например: '14:30 Купить хлеб', и я напомню!")

async def help_command(update: Update, context: CallbackContext) -> None:
    """Обрабатывает команду /help"""
    await update.message.reply_text("Просто напиши сообщение в формате 'HH:MM Текст' — я напомню!\n\n/list — список напоминаний")

async def list_reminders(update: Update, context: CallbackContext) -> None:
    """Выводит список напоминаний для текущего пользователя"""
    user_id = update.message.chat_id
    if user_id not in reminders or not reminders[user_id]:
        await update.message.reply_text("У тебя пока нет напоминаний.")
        return

    text = "\n".join([f"{t.strftime('%H:%M')} - {m}" for t, m in reminders[user_id]])
    await update.message.reply_text(f"Твои напоминания:\n{text}")

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обрабатывает входящие сообщения и ищет в них время"""
    user_id = update.message.chat_id
    text = update.message.text

    # Ищем время в формате HH:MM
    match = re.match(r"(\d{1,2}:\d{2})\s+(.+)", text)
    if not match:
        return  # Если не найдено время, игнорируем сообщение

    time_str, message_text = match.groups()

    try:
        remind_time = datetime.datetime.strptime(time_str, "%H:%M").time()
        now = datetime.datetime.now()
        remind_datetime = datetime.datetime.combine(now.date(), remind_time)

        # Если время уже прошло сегодня, то переносим на следующий день
        if remind_datetime < now:
            remind_datetime += datetime.timedelta(days=1)

    except ValueError:
        return  # Если время некорректное, игнорируем

    if user_id not in reminders:
        reminders[user_id] = []

    reminders[user_id].append((remind_datetime, message_text))
    await update.message.reply_text(f"✅ Напоминание установлено на {time_str}: {message_text}")

async def reminder_checker():
    """Фоновая задача, отправляющая напоминания в нужное время"""
    while True:
        now = datetime.datetime.now()
        for user_id in list(reminders.keys()):
            for remind_datetime, message in reminders[user_id][:]:
                if now >= remind_datetime:
                    app = Application.builder().token(TOKEN).build()
                    await app.bot.send_message(user_id, f"🔔 Напоминание: {message}")
                    reminders[user_id].remove((remind_datetime, message))

            # Удаляем пользователя, если у него больше нет напоминаний
            if not reminders[user_id]:
                del reminders[user_id]

        await asyncio.sleep(60)  # Проверяем каждую минуту

def main():
    """Запускает бота"""
    global app
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list", list_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем фоновую задачу с проверкой напоминаний
    loop = asyncio.get_event_loop()
    loop.create_task(reminder_checker())

    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
