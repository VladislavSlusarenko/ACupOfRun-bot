import telebot
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Замените на ваш токен
CHANNEL_ID = '-1002302094356'  # Замените на ваш канал
ADMIN_ID = 1166978466  # ID администратора

bot = telebot.TeleBot(API_TOKEN)
scheduler = BackgroundScheduler()

DATA_FILE = 'user_data.json'  # Файл для хранения данных
VIDEO_DIR = 'videos'  # Директория для хранения видео
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
    if user_id not in user_data or not user_data[user_id]['name']:
        # Если пользователя нет в данных или у него нет имени, просим ввести имя
        user_data[user_id] = {'name': '', 'counter': 0, 'has_sent_photo': False}
        bot.send_message(user_id, "Ваше ім’я: 🍅")  # Просим ввести имя
        bot.register_next_step_handler(message, set_name)  # Ожидаем, что пользователь введет имя
    else:
        # Если пользователь уже зарегистрирован и имеет имя, говорим, что ожидаем фото
        bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")
        
    # Кнопка администратора (если это администратор)
    markup = InlineKeyboardMarkup()
    if user_id == ADMIN_ID and user_data[user_id]['name']:  # Только если имя задано
        markup.add(InlineKeyboardButton("Адміністратор", callback_data="admin"))
        bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']} 🍅 ви адміністратор!", reply_markup=markup)

# Установка имени пользователя
def set_name(message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text.strip()  # Сохраняем имя
    save_data()

    # Приветственное сообщение после ввода имени
    bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")

    # Если это администратор, показываем кнопку "Адміністратор"
    if user_id == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Адміністратор", callback_data="admin"))
        bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']} 🍅 ви адміністратор!", reply_markup=markup)

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
    save_data()

# Запланировать сброс флагов напоминаний каждый день
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

# Кнопки для администратора
def admin_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Понеділок", callback_data="Понеділок"),
        InlineKeyboardButton("Вівторок", callback_data="Вівторок"),
        InlineKeyboardButton("Середа", callback_data="Середа"),
        InlineKeyboardButton("Четвер", callback_data="Четвер"),
        InlineKeyboardButton("П'ятниця", callback_data="П'ятниця"),
        InlineKeyboardButton("Субота", callback_data="Субота"),
        InlineKeyboardButton("Неділя", callback_data="Неділя")
    )
    return markup

# Обработка команды /admin
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Ласкаво просимо до адмін-панелі.", reply_markup=admin_keyboard())
    else:
        bot.send_message(message.chat.id, "У вас немає доступу до адмін-панелі.")

# Обработка кнопки "Адміністратор"
@bot.callback_query_handler(func=lambda call: call.data == "admin")
def admin_panel(call):
    if call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, "Ласкаво просимо до адмін-панелі.", reply_markup=admin_keyboard())

# Обработка выбора дня недели
@bot.callback_query_handler(func=lambda call: call.data in ['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'Пятниця', 'Субота', 'Неділя'])
def day_selected(call):
    day = call.data
    user_id = call.from_user.id
    if not os.path.exists(VIDEO_DIR):
        os.mkdir(VIDEO_DIR)

    video_path = os.path.join(VIDEO_DIR, f"{day}_video.mp4")
    if os.path.exists(video_path):
        bot.send_message(call.message.chat.id, f"Текущє відео для {day} вже є. Ви можете замінити його або залишити поточне.")
        bot.send_video(call.message.chat.id, open(video_path, 'rb'), caption=f"Відео для {day}")
        bot.send_message(call.message.chat.id, "Натисніть кнопку, щоб замінити відео.", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Заміна відео", callback_data=f"replace_{day}")))
    else:
        bot.send_message(call.message.chat.id, f"Для {day} ще немає відео. Завантажте нове відео.")
        bot.register_next_step_handler(call.message, handle_video_upload, day)

# Обработка загрузки видео
@bot.message_handler(content_types=['video'])
def handle_video_upload(message, day):
    user_id = message.from_user.id
    video_path = os.path.join(VIDEO_DIR, f"{day}_video.mp4")
    video_file = bot.get_file(message.video.file_id)
    file = bot.download_file(video_file.file_path)
    with open(video_path, 'wb') as new_video:
        new_video.write(file)
    bot.send_message(message.chat.id, f"Відео для {day} успішно завантажено!")
    bot.send_video(message.chat.id, open(video_path, 'rb'))

# Обработка замены видео
@bot.callback_query_handler(func=lambda call: call.data.startswith('replace_'))
def replace_video(call):
    day = call.data.split('_')[1]
    bot.send_message(call.message.chat.id, f"Завантажте нове відео для {day}.")
    bot.register_next_step_handler(call.message, handle_video_upload, day)

# Запуск планировщика
scheduler.start()

# Запуск бота
bot.polling()

