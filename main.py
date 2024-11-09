import telebot
import json
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Замените на свой токен
CHANNEL_ID = '-1002302094356'  # Замените на ID вашего канала
bot = telebot.TeleBot(API_TOKEN)
scheduler = BackgroundScheduler()

DATA_FILE = 'user_data.json'  # Имя файла для хранения данных
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

# Создаем клавиатуру с кнопкой "Відправити фото"
def get_photo_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Відправити фото"))
    return keyboard

# Начальная команда /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Проверяем, зарегистрирован ли уже пользователь
    if user_id not in user_data:
        user_data[user_id] = {'name': '', 'counter': 0, 'total_strikes': 0, 'has_sent_photo': False}
        bot.send_message(user_id, "Ваше ім’я: 🍅", reply_markup=ReplyKeyboardRemove())
        print(f"Старт: Инициализация пользователя {user_id}")
        save_data()
    else:
        # Если пользователь уже зарегистрирован, показываем кнопку "Відправити фото"
        bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.", reply_markup=get_photo_keyboard())

# Установка имени пользователя
@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['name'] == '')
def set_name(message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text
    save_data()

    # Убираем строку ввода и показываем только кнопку "Відправити фото"
    bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}🍅! Тепер я буду чекати на твоє фото.", reply_markup=ReplyKeyboardRemove())  # Убираем клавиатуру
# Обработка нажатия кнопки "Відправити фото"
@bot.message_handler(func=lambda message: message.text == "Відправити фото")
def prompt_photo(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]['name']:
        bot.send_message(user_id, "Відправте своє фото сюди 📸")
    else:
        bot.send_message(user_id, "Нажмите 'Почнемо' для регистрации.")

# Обработка отправки фото
@bot.message_handler(content_types=['photo'])
def receive_photo(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]['name']:
        user_data[user_id]['counter'] += 1
        user_data[user_id]['total_strikes'] += 1
        user_data[user_id]['has_sent_photo'] = True
        save_data()

        # Сохранение фото в буфер
        if user_id not in photo_buffer:
            photo_buffer[user_id] = []
        photo_buffer[user_id].append({
            'file_id': message.photo[-1].file_id,
            'caption': f"{user_data[user_id]['name']} - страйк {user_data[user_id]['counter']} из 100"
        })

        # Сообщение о текущем количестве страйков
        current_count = user_data[user_id]['counter']
        total_strikes = user_data[user_id]['total_strikes']
        bot.send_message(user_id, f"Супер 👍 молодець 😎! +1\n"
                                  f"Кількість страйків зараз: {current_count} из 100\n"
                                  f"Загальна кількість страйків: {total_strikes}")
    else:
        bot.send_message(user_id, "Нажмите 'Почнемо' для регистрации.")

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

# Планируем отправку статистики каждый час
scheduler.add_job(send_hourly_statistics, CronTrigger(minute=0, hour='*'))

# Функция сброса счетчика для пользователей, не отправивших фото
def reset_counter(user_id):
    name = user_data[user_id]['name']
    user_data[user_id]['counter'] = 0
    user_data[user_id]['has_sent_photo'] = False
    bot.send_message(user_id, f"Ну ти і помідорка, {name} 🍅")

    # Возвращаем кнопку "Відправити фото" после сброса
    bot.send_message(user_id, "Тепер відправляй своє фото знову 📸", reply_markup=get_photo_keyboard())

# Проверка и сброс счетчиков каждый час
def check_and_reset_counters():
    for user_id, data in user_data.items():
        if not data['has_sent_photo']:  # Если пользователь не отправил фото
            reset_counter(user_id)
        else:
            data['counter'] = 0  # Сбрасываем счетчик для следующего часа
            data['has_sent_photo'] = False
            # Возвращаем кнопку "Відправити фото" после сброса
            bot.send_message(user_id, "Тепер відправляй своє фото знову 📸", reply_markup=get_photo_keyboard())
    save_data()

scheduler.add_job(check_and_reset_counters, CronTrigger(minute=0, hour='*'))

# Запуск планировщика и бота
scheduler.start()
bot.polling()
