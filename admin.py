import telebot
import os
import datetime
from telebot import types
from config import API_TOKEN, CHANNEL_ID, ADMINS  # Импортируем данные из config.py
import schedule
import time
import threading
from main import set_name, user_data
from main import send_reminder_1min, send_reminder_30min, send_reminder_50min
from main import send_grouped_stats_and_photos_hourly
VIDEO_DIR = 'uploaded_videos'  # Папка для хранения видео
bot = telebot.TeleBot(API_TOKEN)

# Переконаємося, що папка для відео існує
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

# Словник для зберігання відео за днями
video_data = {}


# Словарь для отслеживания, находится ли пользователь в админ-панели
admin_session = {}

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        item_admin = types.KeyboardButton("Адмін")
        item_bot = types.KeyboardButton("Бот")
        markup.add(item_admin, item_bot)
        bot.send_message(user_id, "Привіт, вибери, що хочеш зробити:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Привіт! Я готовий до роботи!")


# Обработка нажатия кнопки "Адмін"
@bot.message_handler(func=lambda message: message.text == "Адмін")
def admin_panel(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        # Помечаем, что пользователь в админ-панели
        admin_session[user_id] = 'admin'
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        item_upload_video = types.KeyboardButton("Загрузить видео для нового часа")
        item_back_to_bot = types.KeyboardButton("Повернутись до бота")  # Кнопка возврата
        markup.add(item_upload_video, item_back_to_bot)
        bot.send_message(user_id, "Вітаємо в адмін панелі!", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Повернутись до бота")
def back_to_bot(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        # Повертаємо адміністратора до режиму звичайного бота
        admin_session[user_id] = 'user'
        
        # Видаляємо клавіатуру
        markup = types.ReplyKeyboardRemove()
        bot.send_message(user_id, "Тепер ти в режимі бота. Можеш працювати як звичайний користувач!", reply_markup=markup)
        
        # Повертаємо адміна до основного коду бота з нагадуваннями
        send_reminder_1min()  # Це може бути, наприклад, нагадування через 1 хвилину
        send_reminder_30min()  # Так само для інших нагадувань
        send_reminder_50min()  # І для 50 хвилини

        # Інші дії, які відбуваються після повернення адміністратора до бота:
        # Відправка статистики та фотографій
        send_grouped_stats_and_photos_hourly()

# Відправка відео в канал
def send_video_to_channel(day):
    if day in video_data:
        video_file_path = os.path.join(VIDEO_DIR, video_data[day])
        if os.path.exists(video_file_path):
            with open(video_file_path, 'rb') as video_file:
                bot.send_video(CHANNEL_ID, video_file, caption="Доброго ранку!")
            bot.send_message(ADMINS[0], f"Відео для дня #{day} успішно відправлено в канал.")
        else:
            bot.send_message(ADMINS[0], f"Файл відео для дня #{day} не знайдено.")
    else:
        bot.send_message(ADMINS[0], f"Відео для дня #{day} не знайдено в словнику video_data!")

# Завдання для `schedule`
def schedule_send_video():
    # Отримати поточний день у році
    current_day = datetime.datetime.now().timetuple().tm_yday
    send_video_to_channel(current_day)

# Налаштування щогодинного відправлення
schedule.every().hour.at(":00").do(schedule_send_video)

# Запуск планувальника у фоновому потоці
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Завантаження відео (адмін-функція)
@bot.message_handler(func=lambda message: message.from_user.id in ADMINS and message.text == "Завантажити відео")
def upload_video(message):
    bot.send_message(message.chat.id, "Введіть номер дня, для якого завантажуєте відео:")
    bot.register_next_step_handler(message, ask_for_day)

# Отримання номера дня
def ask_for_day(message):
    try:
        day = int(message.text)
        if day < 1 or day > 365:
            raise ValueError("Номер дня має бути між 1 і 365.")
        bot.send_message(message.chat.id, f"Надішліть відео для дня #{day}.")
        bot.register_next_step_handler(message, handle_video, day)
    except ValueError as e:
        bot.send_message(message.chat.id, str(e))
        bot.register_next_step_handler(message, ask_for_day)

# Обробка відео
def handle_video(message, day):
    if message.content_type == 'video':
        video = message.video
        file_info = bot.get_file(video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Збереження відео
        video_path = os.path.join(VIDEO_DIR, f"day_{day}.mp4")
        with open(video_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        video_data[day] = f"day_{day}.mp4"
        bot.send_message(message.chat.id, f"Відео для дня #{day} успішно збережено!")
    else:
        bot.send_message(message.chat.id, "Будь ласка, надішліть відео.")
        bot.register_next_step_handler(message, handle_video, day)

# Запуск планувальника в окремому потоці
import threading
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Запуск бота
bot.polling()
