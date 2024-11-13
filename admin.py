from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
from telebot import types
from config import API_TOKEN, CHANNEL_ID, ADMIN_ID
print(API_TOKEN)  # Проверяем правильность импорта
print(CHANNEL_ID)
print(ADMIN_ID)
scheduler = BackgroundScheduler()

video_storage_path = "videos/"  # Папка для хранения видео
if not os.path.exists(video_storage_path):
    os.makedirs(video_storage_path)

video_schedule = {}  # Словарь для хранения привязок видео к дням

# Функция для отправки "Доброго ранку!" и видео в канал
def send_good_morning(bot, channel_id):
    current_day = get_current_day()
    if current_day in video_schedule:
        try:
            bot.send_video(channel_id, video=open(video_schedule[current_day], 'rb'))
        except Exception as e:
            bot.send_message(channel_id, f"Ошибка при отправке видео: {e}")
    bot.send_message(channel_id, "Доброго ранку!")

# Уведомления
def send_reminder_1min(bot, user_data):
    for user_id in user_data:
        if user_data[user_id]['name'] and not user_data[user_id]['has_sent_photo']:
            bot.send_message(user_id, "Чекаю на твоє фото 😊")

def send_reminder_30min(bot, user_data):
    for user_id in user_data:
        if user_data[user_id]['name'] and not user_data[user_id]['has_sent_photo']:
            bot.send_message(user_id, "Не забудь 😏")

def send_reminder_50min(bot, user_data):
    for user_id in user_data:
        if user_data[user_id]['name'] and not user_data[user_id]['has_sent_photo']:
            bot.send_message(user_id, "Останній шанс 😢")

# Сброс напоминаний
def reset_reminders(user_data):
    for user_id in user_data:
        user_data[user_id]['has_sent_photo'] = False

# Команда админа для загрузки видео
def handle_admin_commands(bot, message, channel_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for i in range(1, 8):
        markup.add(types.KeyboardButton(f"Загрузить видео для дня {i}"))
    bot.send_message(message.chat.id, "Выберите номер дня для загрузки видео", reply_markup=markup)

    @bot.message_handler(content_types=['video'])
    def receive_video(video_message):
        try:
            day_number = int(video_message.text.split()[-1])  # Парсим номер дня
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат видео. Попробуйте снова.")
            return
        
        file_path = os.path.join(video_storage_path, f"day_{day_number}.mp4")
        
        # Сохранение видео на файловую систему
        file_info = bot.get_file(video_message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        try:
            with open(file_path, "wb") as f:
                f.write(downloaded_file)
            video_schedule[day_number] = file_path  # Добавляем в расписание
            bot.send_message(video_message.chat.id, f"Видео для дня {day_number} сохранено.")
            bot.send_message(video_message.chat.id, f"Сейчас выгружено {len(video_schedule)} видео из 7.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при сохранении видео: {e}")

def get_current_day():
    from datetime import datetime
    return datetime.now().weekday() + 1
