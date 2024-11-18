import telebot
import json
import logging
#import os 
from config import ADMINS  
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import admin_panel

#import sys
#sys.path.append('/Users/admin/Downloads/ACupOfRun-bot')  
# Используем объект admin_panel
print(admin_panel.get_info())  # Выведет информацию о панели

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'
CHANNEL_ID = '-1002302094356'
DATA_FILE = 'user_data.json'  # Файл для хранения данных
ADMINS = [ 922094773] 
# Проверим обновления
print(admin_panel.get_info())

# Инициализация бота, планировщика и логирования
bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=4)
scheduler = BackgroundScheduler()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Глобальные переменные
user_data = {}
photo_buffer = {}

# Загрузка данных из файла
def load_data():
    global user_data
    try:
        with open(DATA_FILE, 'r') as file:
            user_data = json.load(file)
            logging.info("Данные загружены успешно.")
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}
        logging.warning("Файл данных отсутствует или поврежден. Создан новый словарь данных.")

# Сохранение данных в файл
def save_data():
    try:
        with open(DATA_FILE, 'w') as file:
            json.dump(user_data, file, indent=4)
            logging.info("Данные сохранены успешно.")
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

# Загрузка данных при запуске
load_data()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    # Проверка и отладка
    print(f"ADMINS: {ADMINS}, type: {type(ADMINS)}")
    print(f"user_id: {user_id}, type: {type(user_id)}")

    if user_id not in user_data:
        user_data[user_id] = {'name': '', 'counter': 0, 'has_sent_photo': False}
        bot.send_message(user_id, "Ваше ім’я: 🍅")
        save_data()
    else:
        bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")

    if user_id in ADMINS:
        bot.send_message(user_id, "Ви зареєстровані як адміністратор.")
        admin_panel(message)

# Установка имени пользователя
@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['name'] == '')
def set_name(message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text.strip()
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

# Напоминания пользователям
def send_reminders():
    for user_id, data in user_data.items():
        if data['name'] and not data['has_sent_photo']:
            reminder_message = "Чекаю на твоє фото 😊" if data['counter'] < 3 else "Останній шанс 😢"
            bot.send_message(user_id, reminder_message)

# Функция для отправки "Доброго ранку!"
def send_good_morning():
    try:
        bot.send_message(CHANNEL_ID, "Доброго ранку!")
        logging.info("Сообщение 'Доброго ранку!' отправлено успешно.")
    except Exception as e:
        logging.error(f"Ошибка отправки 'Доброго ранку!': {e}")

# Сброс статусов has_sent_photo
def reset_reminders():
    for user_id in user_data:
        user_data[user_id]['has_sent_photo'] = False
    save_data()
    logging.info("Флаги отправки фото сброшены.")

# Отправка статистики и фотографий
def send_grouped_stats_and_photos_hourly():
    stats_message = "Статистика страйков:\n"
    for user_id, data in user_data.items():
        name = data['name'] or "Невідомий користувач"
        stats_message += f"{name} - страйк {data['counter']} з 100\n"
        if data['counter'] == 0:
            stats_message += f"{name} - помідорка 🍅\n"
    bot.send_message(CHANNEL_ID, stats_message)

    for user_id, photos in photo_buffer.items():
        for photo_id in photos:
            caption = f"Фото від {user_data[user_id]['name']} - страйк {user_data[user_id]['counter']} з 100"
            bot.send_photo(CHANNEL_ID, photo_id, caption=caption)
    photo_buffer.clear()

# Планировщик задач
scheduler.add_job(send_good_morning, CronTrigger(hour=8, minute=0))  # Утреннее сообщение
scheduler.add_job(send_reminders, CronTrigger(minute="1,30,50"))  # Напоминания в 1, 30 и 50 минут каждого часа
scheduler.add_job(reset_reminders, CronTrigger(hour=0, minute=0))  # Сброс флагов
scheduler.add_job(send_grouped_stats_and_photos_hourly, CronTrigger(minute=59))  # Ежечасная статистика

# Запуск планировщика и бота
scheduler.start()
try:
    logging.info("Бот запущен!")
    bot.polling()
except Exception as e:
    logging.critical(f"Критическая ошибка: {e}")

