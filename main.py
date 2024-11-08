import telebot
import json
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
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

# Создаем клавиатуру с кнопками
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Почнемо"))
    keyboard.add(KeyboardButton("Відправити фото"))
    return keyboard

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
        bot.send_message(user_id, "Ваше ім’я: 🍅", reply_markup=get_main_keyboard())
        print(f"Старт: Инициализация пользователя {user_id}")
        save_data()
    else:
        print(f"Старт: Пользователь {user_id} уже инициализирован")

@bot.message_handler(func=lambda message: message.text == "Почнемо")
def register_user(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'name': message.from_user.first_name, 'counter': 0, 'total_strikes': 0, 'has_sent_photo': False}
        bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.", reply_markup=get_main_keyboard())
        save_data()

@bot.message_handler(func=lambda message: message.text == "Відправити фото")
def prompt_photo(message):
    user_id = message.from_user.id
    if user_id in user_data:
        bot.send_message(user_id, "Відправте своє фото сюди 📸")
    else:
        bot.send_message(user_id, "Введи /start, щоб розпочати.")

@bot.message_handler(content_types=['photo'])
def receive_photo(message):
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]['counter'] += 1
        user_data[user_id]['total_strikes'] += 1
        user_data[user_id]['has_sent_photo'] = True
        save_data()

        if user_id not in photo_buffer:
            photo_buffer[user_id] = []
        photo_buffer[user_id].append({
            'file_id': message.photo[-1].file_id,
            'caption': f"{user_data[user_id]['name']} - страйк {user_data[user_id]['counter']} из 100"
        })

        current_count = user_data[user_id]['counter']
        total_strikes = user_data[user_id]['total_strikes']
        bot.send_message(user_id, f"Супер 👍 молодець 😎! +1\n"
                                  f"Кількість страйків зараз: {current_count} из 100\n"
                                  f"Загальна кількість страйків: {total_strikes}")
    else:
        bot.send_message(user_id, "Введи /start, щоб розпочати.")

def send_hourly_statistics():
    stats_message = "Страйки усіх учасників:\n"
    for user_id, data in user_data.items():
        name = data['name'] if data['name'] else "Невідомий користувач"
        stats_message += f"{name} - страйк {data['counter']} из 100\n"

    bot.send_message(CHANNEL_ID, stats_message)

    for user_id, photos in photo_buffer.items():
        for photo in photos:
            bot.send_photo(CHANNEL_ID, photo['file_id'], caption=photo['caption'])

    photo_buffer.clear()

scheduler.add_job(send_hourly_statistics, CronTrigger(minute=0, hour='*'))

def check_and_reset_counters():
    for user_id, data in user_data.items():
        if data['counter'] == 0:
            reset_counter(user_id)
        else:
            data['counter'] = 0
            data['has_sent_photo'] = False
    save_data()

scheduler.add_job(check_and_reset_counters, CronTrigger(minute=0, hour='*'))

scheduler.start()
bot.polling()
