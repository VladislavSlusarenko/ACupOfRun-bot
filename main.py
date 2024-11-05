import asyncio
import schedule
import time
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
import pytz
from datetime import datetime

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Замените на ваш токен
user_data = {}  # Словарь для хранения данных пользователей

async def main():
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    @dp.message(Command("start"))
    async def start_command(message: types.Message):
        await message.answer("Привіт! Введи своє ім'я для реєстрації:")
        dp.message.register(get_name)

    @dp.message()
    async def get_name(message: types.Message):
        user_data[message.from_user.id] = {
            "name": message.text,
            "strike_count": 0,
            "last_photo_date": None
        }
        await message.answer(f"Ваше ім’я: {message.text} 🍅\nЯ буду нагадувати тобі про фото.")
        schedule_tasks()  # Запускаем задачи после получения имени

    # Функция для планирования задач
    def schedule_tasks():
        # Устанавливаем время для отправки сообщений каждую первую, 30-ю и 50-ю минуту каждого часа
        schedule.every().hour.at(":01").do(lambda: asyncio.create_task(send_hourly_message("Чекаю на твоє фото 😊")))
        schedule.every().hour.at(":30").do(lambda: asyncio.create_task(send_hourly_message("Не забудь 😏")))
        schedule.every().hour.at(":50").do(lambda: asyncio.create_task(send_hourly_message("Останній шанс 😢")))

    async def send_hourly_message(message_text):
        # Получаем текущее время в Торонто
        tz = pytz.timezone('America/Toronto')
        current_time = datetime.now(tz).strftime("%H:%M")
        print(f"Текущее время в Торонто: {current_time}")  # Вывод текущего времени на консоль

        # Отправляем сообщения пользователям
        for user_id, data in user_data.items():
            await bot.send_message(user_id, message_text)

            # Проверка, если последнее фото не отправлено в этот день
            if data["last_photo_date"] != datetime.now(tz).date():
                # Сбрасываем счетчик страйков
                data["strike_count"] = 0
                data["last_photo_date"] = None  # Сбрасываем дату

    @dp.message(lambda message: message.content_type == 'photo')
    async def handle_photo(message: types.Message):
        user_id = message.from_user.id
        if user_id not in user_data:
            await message.answer("Спочатку надішліть команду /start.")
            return

        # Увеличиваем счетчик страйков
        user_data[user_id]["strike_count"] += 1
        user_data[user_id]["last_photo_date"] = datetime.now(pytz.timezone('America/Toronto')).date()  # Обновляем дату
        await message.answer("Супер 👍 молодець 😎")

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(30)  # Проверяем раз в 30 секунд

    # Запуск расписания в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    # Запуск polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
