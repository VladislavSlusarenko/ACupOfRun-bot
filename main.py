import telebot
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Замените на свой токен
CHANNEL_ID = '-1002302094356'  # Замените на ID вашего канала
bot = telebot.TeleBot(API_TOKEN)
scheduler = BackgroundScheduler()

# Имя файла для хранения данных
DATA_FILE = 'user_data.json'

# Словарь для хранения данных пользователей
user_data = {}
photo_buffer = {}  # Буфер для сохранения фотографий до конца часа

# Загрузка данных из файла
def load_data():
    global user_data
    try:
        with open(DATA_FILE, 'r') as file:
            user_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}

# Сохранение данных в файл
def save_data():
    with open(DATA_FILE, 'w') as file:
        json.dump(user_data, file)

# Загружаем данные при запуске
load_data()

def send_first_reminder(user_id):
    if not user_data[user_id]['has_sent_photo']:
        bot.send_message(user_id, "Чекаю на твоє фото 😊")

def send_second_reminder(user_id):
    if not user_data[user_id]['has_sent_photo']:
        bot.send_message(user_id, "Не забудь 😏")

def send_final_reminder(user_id):
    if not user_data[user_id]['has_sent_photo']:
        bot.send_message(user_id, "Останній шанс 😢")

def reset_counter(user_id):
    name = user_data[user_id]['name']
    user_data[user_id]['counter'] = 0
    user_data[user_id]['has_sent_photo'] = False
    bot.send_message(user_id, f"Ну ти і помідорка, {name} 🍅")
    save_data()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'name': '', 'counter': 0, 'total_strikes': 0, 'has_sent_photo': False}
        bot.send_message(user_id, "Ваше ім’я: 🍅")
        print(f"Старт: Инициализация пользователя {user_id}")
        save_data()
    else:
        print(f"Старт: Пользователь {user_id} уже инициализирован")

@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['name'] == '')
def set_name(message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text
    bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")

    # Запускаем три напоминания каждый час
    scheduler.add_job(send_first_reminder, CronTrigger(minute=1), args=[user_id], id=f"{user_id}_reminder_1")
    scheduler.add_job(send_second_reminder, CronTrigger(minute=30), args=[user_id], id=f"{user_id}_reminder_2")
    scheduler.add_job(send_final_reminder, CronTrigger(minute=50), args=[user_id], id=f"{user_id}_reminder_3")

@bot.message_handler(content_types=['photo'])
def receive_photo(message):
    user_id = message.from_user.id
    if user_id in user_data:
        # Обновление счетчиков
        user_data[user_id]['counter'] += 1
        user_data[user_id]['total_strikes'] += 1
        user_data[user_id]['has_sent_photo'] = True
        save_data()

        # Добавляем фото в буфер
        if user_id not in photo_buffer:
            photo_buffer[user_id] = []
        photo_buffer[user_id].append({
            'file_id': message.photo[-1].file_id,
            'caption': f"{user_data[user_id]['name']} отправил(а) фото"
        })

        # Сообщение пользователю о страйках
        current_count = user_data[user_id]['counter']
        total_strikes = user_data[user_id]['total_strikes']
        bot.send_message(user_id, f"Супер 👍 молодець 😎! +1\n"
                                  f"Кількість страйків зараз: {current_count}\n"
                                  f"Загальна кількість страйків: {total_strikes}")
    else:
        bot.send_message(user_id, "Введи /start, щоб розпочати.")

def send_hourly_statistics():
    # Формируем статистику страйков
    stats_message = "Страйки усіх учасників:\n"
    for user_id, data in user_data.items():
        name = data['name'] if data['name'] else "Невідомий користувач"
        strikes = data['counter']
        stats_message += f"{name} - страйк {strikes}\n"

    # Отправляем статистику в канал
    bot.send_message(CHANNEL_ID, stats_message)

    # Отправляем фотографии из буфера
    for user_id, photos in photo_buffer.items():
        for photo in photos:
            bot.send_photo(CHANNEL_ID, photo['file_id'], caption=photo['caption'])

    # Очищаем буфер фотографий после отправки
    photo_buffer.clear()

# Планируем отправку статистики и фото в канал каждый час
scheduler.add_job(send_hourly_statistics, CronTrigger(minute=0, hour='*'))

def check_and_reset_counters():
    for user_id, data in user_data.items():
        if data['counter'] == 0:
            reset_counter(user_id)
        else:
            data['counter'] = 0
            data['has_sent_photo'] = False
    save_data()

# Планируем обнуление счетчика каждый час
scheduler.add_job(check_and_reset_counters, CronTrigger(minute=0, hour='*'))

# Запуск бота и планировщика
scheduler.start()
bot.polling()
