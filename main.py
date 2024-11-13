import sys
print(sys.path)
import telebot
import json
from config import API_TOKEN, CHANNEL_ID, ADMIN_ID
from apscheduler.triggers.cron import CronTrigger
from admin import (
    scheduler, send_good_morning, send_reminder_1min, send_reminder_30min,
    send_reminder_50min, reset_reminders, handle_admin_commands
)

bot = telebot.TeleBot(API_TOKEN)
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
        bot.send_message(user_id, "Ваше ім’я: 🍅")
        save_data()
    else:
        bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")
    
    # Проверка на права администратора
    if user_id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton("Администратор"))
        bot.send_message(user_id, "Панель администратора активирована.", reply_markup=markup)

# Обработка нажатия на кнопку "Администратор"
@bot.message_handler(func=lambda message: message.text == "Администратор" and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    bot.send_message(message.chat.id, "Введите /admin для загрузки видео.")

# Обработка команды /admin для загрузки видео
@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id == ADMIN_ID:
        handle_admin_commands(bot, message, CHANNEL_ID)

# Установка имени пользователя
@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['name'] == '')
def set_name(message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text
    save_data()
    bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")

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
        photo_buffer[user_id].append(message.photo[-1].file_id)
    else:
        bot.send_message(user_id, "Нажмите '/start' для регистрации.")

scheduler.add_job(lambda: send_good_morning(bot, CHANNEL_ID), CronTrigger(minute=0, hour='*'))
scheduler.start()

bot.polling()

