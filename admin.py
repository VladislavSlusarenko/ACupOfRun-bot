import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import os

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Замените на ваш токен
CHANNEL_ID = '-1002302094356'  # Замените на ваш канал
ADMIN_ID = 378578202 # Замените на ID вашего администратора

bot = telebot.TeleBot(API_TOKEN)

VIDEO_FOLDER = 'videos/'  # Папка для хранения видео

# Создаем папку для видео, если её нет
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

# Храним видео для каждого дня
videos = {i: None for i in range(1, 8)}  # Дни от 1 до 7

# Стартовая команда /start
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        # Если пользователь администратор, отправляем сообщение и кнопку для панели администратора
        bot.send_message(message.chat.id, "Привіт, Адміністратор! Тепер ви можете керувати завантаженням відео.")
        bot.send_message(message.chat.id, "Натисніть '/admin', щоб увійти в панель адміністратора.")
    else:
        # Если пользователь не администратор
        bot.send_message(message.chat.id, f"Привіт, {message.from_user.first_name}! Напишіть '/admin', щоб стати адміністратором.")

# Обработчик команды /admin для администратора
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        # Если пользователь администратор, выводим панель
        bot.send_message(message.chat.id, "Ви є адміністратором. Ось панель управління.")
        
        # Показываем количество загруженных видео
        uploaded_videos = sum(1 for v in videos.values() if v is not None)
        bot.send_message(message.chat.id, f"Зараз завантажено відео: {uploaded_videos}/7")
        
        bot.send_message(message.chat.id, "Виберіть номер дня для завантаження відео (від 1 до 7).")
    else:
        bot.send_message(message.chat.id, "У вас немає доступу до цієї команди.")

# Обработка ввода номера дня
@bot.message_handler(func=lambda message: message.text.isdigit() and 1 <= int(message.text) <= 7)
def choose_day(message):
    day = int(message.text)
    bot.send_message(message.chat.id, f"Чекаю відео для дня #{day}. Надішліть відео.")
    bot.register_next_step_handler(message, handle_video_upload, day)

# Обработка загрузки видео
@bot.message_handler(content_types=['video'])
def handle_video_upload(message, day):
    if message.from_user.id == ADMIN_ID:
        # Сохраняем видео
        video_file_id = message.video.file_id
        video_file = bot.get_file(video_file_id)
        downloaded_video = bot.download_file(video_file.file_path)
        
        # Сохраняем видео на диск
        video_path = os.path.join(VIDEO_FOLDER, f"day_{day}.mp4")
        with open(video_path, 'wb') as new_video:
            new_video.write(downloaded_video)
        
        # Сохраняем информацию о видео
        videos[day] = video_path
        bot.send_message(message.chat.id, f"Відео для дня #{day} завантажено. Відправляю в канал...")
        
        # Отправляем видео в канал с "Доброго ранку!"
        bot.send_video(CHANNEL_ID, open(video_path, 'rb'), caption="Доброго ранку!")
        
        # Подтверждаем администратору
        bot.send_message(message.chat.id, f"Відео для дня #{day} успішно завантажено і відправлено в канал.")
    else:
        bot.send_message(message.chat.id, "У вас немає доступу до цієї команди.")

# Запуск бота
bot.polling()

