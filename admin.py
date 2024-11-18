import os
from telebot import TeleBot
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from config import ADMINS
from config import bot 
from config import admin_panel 
VIDEO_FOLDER = "./videos"  # Путь внутри вашего проекта
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# Папка для хранения видео
os.makedirs(VIDEO_FOLDER, exist_ok=True)
# Временное хранилище для состояния администратора
admin_state = {}

admin_panel.add_admin(922094773)
print(admin_panel.get_info())

# Планировщик для задач
scheduler = BackgroundScheduler()

# Команда /admin для доступа к админ панели
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        bot.send_message(
            user_id, 
            "Ласкаво просимо в панель адміністратора!\n"
            "Ви можете:\n"
            "1️⃣ Завантажити відео для публікації (введіть номер дня: 1-7).\n"
            "2️⃣ Перевірити поточні відео.\n\n"
            "Просто введіть номер дня, щоб почати! 🎥"
        )
        bot.send_message(user_id, f"Зараз завантажено відео: {count_uploaded_videos()} з 7.")
        admin_state[user_id] = {'awaiting_day': True, 'day': None}  # Стан очікування номера дня
    else:
        bot.send_message(user_id, "У вас немає прав для входу в панель адміністратора.")

# Проверка количества загруженных видео
def count_uploaded_videos():
    return len([f for f in os.listdir(VIDEO_FOLDER) if f.endswith(".mp4")])

# Обработка введения дня
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_state and admin_state[msg.from_user.id].get('awaiting_day'))
def set_day_for_video(message):
    user_id = message.from_user.id
    try:
        day = int(message.text)
        if 1 <= day <= 7:
            admin_state[user_id]['day'] = day
            admin_state[user_id]['awaiting_day'] = False
            admin_state[user_id]['awaiting_video'] = True
            bot.send_message(user_id, f"Чекаю відео для дня #{day} 📹")
        else:
            bot.send_message(user_id, "Введіть число від 1 до 7.")
    except ValueError:
        bot.send_message(user_id, "Будь ласка, введіть коректний номер дня (1-7).")

# Обработка загрузки видео
@bot.message_handler(content_types=['video'])
def handle_video_upload(message):
    user_id = message.from_user.id
    if user_id in admin_state and admin_state[user_id].get('awaiting_video'):
        day = admin_state[user_id]['day']
        video_file_id = message.video.file_id
        video_file = bot.get_file(video_file_id)
        try:
            downloaded_file = bot.download_file(video_file.file_path)
            
            # Сохраняем видео
            video_path = os.path.join(VIDEO_FOLDER, f"day_{day}.mp4")
            with open(video_path, 'wb') as f:
                f.write(downloaded_file)
            
            bot.send_message(user_id, f"Відео для дня #{day} успішно збережено! ✅")
            schedule_video_post(day, video_path)
            admin_state.pop(user_id)  # Сброс состояния администратора
        except Exception as e:
            bot.send_message(user_id, f"Помилка при завантаженні відео: {e}")
    else:
        bot.send_message(user_id, "Будь ласка, спершу виберіть день через /admin.")

# Планирование публикации видео
def schedule_video_post(day, video_path):
    # Устанавливаем время публикации на начало следующего часа
    publish_time = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    # Добавляем задачу в планировщик
    scheduler.add_job(
        lambda: publish_video(video_path), 
        'date',  # Используем 'date' для выполнения задачи в одно время
        run_date=publish_time,
        id=f"video_post_day_{day}"
    )
    bot.send_message(
        'CHANNEL_ID',  # Замените на ваш канал
        f"Відео для дня #{day} заплановано на публікацію в {publish_time.strftime('%Y-%m-%d %H:%M')}! 🚀"
    )
    print(f"Відео заплановано на {publish_time.strftime('%Y-%m-%d %H:%M')}")

# Публикация видео
def publish_video(video_path):
    if os.path.exists(video_path):
        with open(video_path, 'rb') as video_file:
            bot.send_video('CHANNEL_ID', video_file, caption="Доброго ранку! ☀️")
    else:
        bot.send_message('CHANNEL_ID', "Помилка: відео не знайдено для публікації. 🚨")

# Запуск бота
if __name__ == "__main__":
    scheduler.start()

