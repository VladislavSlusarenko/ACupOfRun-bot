import telebot
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Замените на ваш токен
CHANNEL_ID = '-1002302094356'  # Замените на ваш канал

bot = telebot.TeleBot(API_TOKEN)
scheduler = BackgroundScheduler()

DATA_FILE = 'user_data.json'  # Файл для хранения данных
user_data = {}
photo_buffer = {}  # Буфер для фотографий

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

# Автоматическое сохранение данных после каждого действия
load_data()

# Стартовая команда /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'name': '', 'counter': 0, 'has_sent_photo': False}
        bot.send_message(user_id, "Ваше ім’я: 🍅")  # Убираем клавиатуру и просим имя
        save_data()
    else:
        bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")

# Установка имени пользователя
@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['name'] == '')
def set_name(message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text
    save_data()
    bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")

# Функция для отправки "Доброго ранку!" в канал
def send_good_morning():
    bot.send_message(CHANNEL_ID , "Доброго ранку!")

def send_reminder_1min():
    for user_id in user_data:
        if user_data[user_id]['name']:  # Проверяем, зарегистрирован ли пользователь
            bot.send_message(user_id, "Чекаю на твоє фото 😊")


def send_reminder_30min():
    for user_id in user_data:
        if user_data[user_id]['name']:
            bot.send_message(user_id, "Не забудь 😏")

def send_reminder_50min():
    for user_id in user_data:
        if user_data[user_id]['name']:
            bot.send_message(user_id, "Останній шанс 😢")

scheduler.add_job(send_good_morning, CronTrigger(minute=0, hour='*'))

# Стартуем планировщик для регулярных уведомлений
scheduler.add_job(send_reminder_1min, CronTrigger(minute=1))   # 1-я минута каждого часа
scheduler.add_job(send_reminder_30min, CronTrigger(minute=30)) # 30-я минута каждого часа
scheduler.add_job(send_reminder_50min, CronTrigger(minute=50)) # 50-я минута каждого часа

# Обработка фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]['name']:
        user_data[user_id]['counter'] += 1
        user_data[user_id]['has_sent_photo'] = True
        save_data()
        bot.send_message(user_id, f"Супер 👍 молодець 😎\nСтрайк {user_data[user_id]['counter']} з 100")
        if user_id not in photo_buffer:
            photo_buffer[user_id] = []
        # Сохранение фотографии в буфер
        photo_buffer[user_id].append(message.photo[-1].file_id)
    else:
        bot.send_message(user_id, "Нажмите '/start' для регистрации.")

# Функция для сброса счетчика, если пользователь не отправил фото в течение дня
def reset_counter(user_id):
    user_data[user_id]['counter'] = 0
    user_data[user_id]['has_sent_photo'] = False
    save_data()
    bot.send_message(user_id, f"Ну ти і помідорка, {user_data[user_id]['name']} 🍅")

# Ежечасная отправка статистики
def send_hourly_stats():
    registered_count = sum(1 for data in user_data.values() if data['name'])
    stats_message = f"Статистика:\nЗарегистрированных участников: {registered_count}\n"
    for user_id, data in user_data.items():
        name = data['name'] if data['name'] else "Невідомий користувач"
        stats_message += f"{name} - страйк {data['counter']} з 100\n"
        if data['counter'] == 0:
            stats_message += f"{name} -  помідорка 🍅\n"

    # Отправляем статистику в закрытый канал
    bot.send_message(CHANNEL_ID , stats_message)

    # Отправляем все фотографии в закрытый канал
    for user_id, photos in photo_buffer.items():
        for photo in photos:
            user_name = user_data[user_id]['name'] if user_id in user_data else "Невідомий користувач"
            bot.send_message(CHANNEL_ID , f"{user_name} - страйк {user_data[user_id]['counter']} з 100")
            bot.send_photo(CHANNEL_ID , photo)

    # Очищаем буфер фотографий после отправки
    photo_buffer.clear()

# Запланировать задачи для сброса и отправки статистики каждый час
scheduler.add_job(send_hourly_stats, CronTrigger(hour='*', minute=59))  # Отправляем статистику в конце часа

# Запуск планировщика
scheduler.start()

# Запуск бота
bot.polling()

