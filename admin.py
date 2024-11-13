import telebot
import os
from telebot import types

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Замените на ваш API токен
CHANNEL_ID = '-1002302094356'  # Замените на ваш канал
bot = telebot.TeleBot(API_TOKEN)

# Список администраторов
ADMIN_IDS = [922094773,  1166978466]  # Замените на реальные ID администраторов

# Словарь для хранения информации о видео
videos = {
    "Понеділок": None,
    "Вівторок": None,
    "Середа": None,
    "Четвер": None,
    "П’ятниця": None,
    "Субота": None,
    "Неділя": None
}

# Стартовая команда /start
@bot.message_handler(commands=['admin'])
def start(message):
    user_id = message.from_user.id
    
    if user_id in ADMIN_IDS:  # Проверка, является ли пользователь администратором
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Бот', 'Адмін')  # Админ видит две кнопки: "Бот" и "Адмін"
        bot.send_message(user_id, "Привет, выбери: Бот или Адмін", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Бот')  # Обычный пользователь видит только кнопку "Бот"
        bot.send_message(user_id, "Привет, выбери: Бот", reply_markup=markup)

# Обработка кнопки "Адмін"
@bot.message_handler(func=lambda message: message.text == "Адмін")
def admin_menu(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        bot.send_message(user_id, "У вас нет прав доступа к админ-меню.")
        return
    
    # Если пользователь администратор, показываем меню админа
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П’ятниця', 'Субота', 'Неділя')
    bot.send_message(user_id, "Выберите день недели для загрузки видео", reply_markup=markup)

# Обработка выбора дня недели
@bot.message_handler(func=lambda message: message.text in ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця", "Субота", "Неділя"])
def select_day(message):
    user_id = message.from_user.id
    day = message.text
    
    if user_id not in ADMIN_IDS:
        bot.send_message(user_id, "У вас нет прав доступа.")
        return

    # Проверяем, есть ли уже видео для выбранного дня
    if videos[day] is not None:
        bot.send_message(user_id, f"Видео для дня {day} уже загружено. Хотите заменить?", reply_markup=create_yes_no_markup(day))
    else:
        bot.send_message(user_id, f"Чекаю відео для дня {day}. Отправьте видео.")

# Создаем клавиатуру для замены видео
def create_yes_no_markup(day):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Да', 'Нет')
    return markup

# Обработка кнопок "Да" или "Нет"
@bot.message_handler(func=lambda message: message.text in ["Да", "Нет"])
def replace_video(message):
    user_id = message.from_user.id
    day = message.text  # День для замены видео
    if message.text == "Да":
        bot.send_message(user_id, f"Отправьте новое видео для дня {day}")
    else:
        # Возвращаем к выбору дня
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П’ятниця', 'Субота', 'Неділя')
        bot.send_message(user_id, "Выберите день недели для загрузки видео", reply_markup=markup)

# Обработка видео от админа
@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    day = None
    
    # Проверяем, для какого дня видео отправляется
    for selected_day in ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця", "Субота", "Неділя"]:
        if selected_day in message.caption:
            day = selected_day
            break
    
    if day is None:
        bot.send_message(user_id, "Видео не связано с днем недели. Пожалуйста, укажите день.")
        return

    if user_id not in ADMIN_IDS:
        bot.send_message(user_id, "У вас нет прав доступа.")
        return

    # Сохранение видео на сервере или файловой системе
    file_info = bot.get_file(message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    video_path = f'./videos/{day}.mp4'
    with open(video_path, 'wb') as new_video:
        new_video.write(downloaded_file)

    # Сохраняем информацию о видео
    videos[day] = video_path

    # Отправляем видео в канал
    bot.send_video(chat_id=CHANNEL_ID, video=open(video_path, 'rb'), caption=f"Доброго ранку! Відео для {day}")

    # Очищаем клавиатуру
    markup = types.ReplyKeyboardRemove()
    bot.send_message(user_id, f"Видео для дня {day} успешно загружено.", reply_markup=markup)

# Запуск бота
bot.polling()