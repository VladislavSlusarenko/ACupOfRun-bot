import telebot
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import ADMINS 
from admin import admin_panel
from admin import admin_session
from admin import types 
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

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {'name': '', 'counter': 0, 'has_sent_photo': False}
        bot.send_message(user_id, "Ваше ім’я: 🍅")  # Просимо ім'я
        save_data()
    else:
        if user_id in ADMINS:  # Перевіряємо, чи є користувач адміністратором
            bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Ти в адмін-панелі.")
            bot.loop.create_task(admin_panel(bot, user_id))  # Виклик асинхронної функції
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

# Напоминания
def send_reminder_1min():
    for user_id in user_data:
        if user_data[user_id]['name'] and not user_data[user_id]['has_sent_photo']:  # Проверяем, отправил ли пользователь фото
            bot.send_message(user_id, "Чекаю на твоє фото 😊")

def send_reminder_30min():
    for user_id in user_data:
        if user_data[user_id]['name'] and not user_data[user_id]['has_sent_photo']:  # Проверяем, отправил ли пользователь фото
            bot.send_message(user_id, "Не забудь 😏")

def send_reminder_50min():
    for user_id in user_data:
        if user_data[user_id]['name'] and not user_data[user_id]['has_sent_photo']:  # Проверяем, отправил ли пользователь фото
            bot.send_message(user_id, "Останній шанс 😢")

# Обработка фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]['name']:
        user_data[user_id]['counter'] += 1
        user_data[user_id]['has_sent_photo'] = True  # Устанавливаем, что пользователь отправил фото
        save_data()
        bot.send_message(user_id, f"Супер 👍 молодець 😎\nСтрайк {user_data[user_id]['counter']} з 100")
        if user_id not in photo_buffer:
            photo_buffer[user_id] = []
        # Сохранение фотографии в буфер
        photo_buffer[user_id].append(message.photo[-1].file_id)
    else:
        bot.send_message(user_id, "Нажмите '/start' для регистрации.")

@bot.message_handler(func=lambda message: message.text == "Повернутись до бота")
def back_to_bot(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        # Повертаємо адміністратора до звичайного бота
        admin_session[user_id] = 'user'
        
        # Видаляємо клавіатуру
        markup = types.ReplyKeyboardRemove()  # Прибираємо клавіатуру
        bot.send_message(user_id, "Тепер ти в режимі бота. Можеш працювати як звичайний користувач!", reply_markup=markup)
        
        # Запускаємо нагадування або інші функції бота:
        send_reminder_1min()  # Нагадування через 1 хвилину
        send_reminder_30min()  # Нагадування через 30 хвилин
        send_reminder_50min()  # Нагадування через 50 хвилин

# Запланированные задачи
scheduler.add_job(send_good_morning, CronTrigger(minute=0, hour='*'))  # Каждую ночь отправляем "Доброго ранку!"

# Стартуем планировщик для регулярных уведомлений
scheduler.add_job(send_reminder_1min, CronTrigger(minute=1))   # 1-я минута каждого часа
scheduler.add_job(send_reminder_30min, CronTrigger(minute=30)) # 30-я минута каждого часа
scheduler.add_job(send_reminder_50min, CronTrigger(minute=50)) # 50-я минута каждого часа

# Функция для сброса напоминаний
def reset_reminders():
    for user_id in user_data:
        user_data[user_id]['has_sent_photo'] = False  # Сбрасываем флаг, чтобы напоминания начали отправляться заново
    save_data()      # Запланировать сброс флагов напоминаний каждый день
scheduler.add_job(reset_reminders, CronTrigger(hour=0, minute=0))  # Каждый день в 00:00 сбрасываем флаги

# Функция для отправки статистики и фотографий с подписями в конце каждого часа
def send_grouped_stats_and_photos_hourly():
    # Формируем статистику
    stats_message = "Статистика страйков: \n"
    for user_id, data in user_data.items():
        name = data['name'] if data['name'] else "Невідомий користувач"
        stats_message += f"{name} - страйк {data['counter']} з 100\n"
        if data['counter'] == 0:
            stats_message += f"{name} -  помідорка 🍅\n"

    # Отправляем статистику в канал
    bot.send_message(CHANNEL_ID, stats_message)

    # Формируем список сообщений с фотографиями
    for user_id, photos in photo_buffer.items():
        for photo in photos:
            user_name = user_data[user_id]['name'] if user_id in user_data else "Невідомий користувач"
            # Отправляем каждую фотографию с подписью
            photo_caption = f"Фотографія від {user_name} - страйк {user_data[user_id]['counter']} з 100"
            bot.send_photo(CHANNEL_ID, photo, caption=photo_caption)

    # Очищаем буфер фотографий после отправки
    photo_buffer.clear()

# Запланировать задачи для сброса и отправки статистики каждый час
scheduler.add_job(send_grouped_stats_and_photos_hourly, CronTrigger(minute=59))  # В 59-ю минуту каждого часа

# Запуск планировщика
scheduler.start()

# Запуск бота
bot.polling()
