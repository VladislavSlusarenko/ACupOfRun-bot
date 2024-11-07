import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Замените на свой токен
CHANNEL_ID = '-1002302094356'  # Замените на ID закрытого канала
bot = telebot.TeleBot(API_TOKEN)
scheduler = BackgroundScheduler()

user_data = {}  # Словарь для хранения данных пользователей (имя, счетчик и состояние)

def send_first_reminder(user_id):
    if not user_data[user_id]['has_sent_photo']:
        bot.send_message(user_id, "Чекаю на твоє фото 😊")

def send_second_reminder(user_id):
    if not user_data[user_id]['has_sent_photo']:
        bot.send_message(user_id, "Не забудь 😏")

def send_final_reminder(user_id):
    if not user_data[user_id]['has_sent_photo']:
        bot.send_message(user_id, "Останній шанс 😢")

def reset_counter(user_id):
    name = user_data[user_id]['name']
    user_data[user_id]['counter'] = 0
    user_data[user_id]['has_sent_photo'] = False  # Сброс состояния отправки фото
    bot.send_message(user_id, f"Ну ти і помідорка, {name} 🍅")

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in user_data:  # Проверяем, если пользователь уже существует
        user_data[user_id] = {'name': '', 'counter': 0, 'total_strikes': 0, 'has_sent_photo': False}  # Инициализация данных пользователя
        bot.send_message(user_id, "Ваше ім’я: 🍅")
        print(f"Старт: Инициализация пользователя {user_id}")  # Отладочное сообщение
    else:
        print(f"Старт: Пользователь {user_id} уже инициализирован")  # Отладочное сообщение

@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['name'] == '')
def set_name(message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text  # Сохранение имени
    bot.send_message(user_id, f"Привіт, {user_data[user_id]['name']}! Тепер я буду чекати на твоє фото.")

    # Запускаем три напоминания каждый час
    scheduler.add_job(send_first_reminder, CronTrigger(minute=1), args=[user_id], id=f"{user_id}_reminder_1")
    scheduler.add_job(send_second_reminder, CronTrigger(minute=30), args=[user_id], id=f"{user_id}_reminder_2")
    scheduler.add_job(send_final_reminder, CronTrigger(minute=50), args=[user_id], id=f"{user_id}_reminder_3")

@bot.message_handler(content_types=['photo'])
def receive_photo(message):
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]['counter'] += 1  # Увеличиваем счетчик страйков
        user_data[user_id]['total_strikes'] += 1  # Увеличиваем общий счет страйков
        user_data[user_id]['has_sent_photo'] = True  # Устанавливаем флаг, что фото было отправлено

        current_count = user_data[user_id]['counter']  # Текущий счетчик для пользователя
        total_strikes = user_data[user_id]['total_strikes']  # Общее количество страйков

        # Формируем сообщение с дополнительной информацией
        bot.send_message(user_id, f"Супер 👍 молодець 😎! +1\n"
                                  f"Кількість страйків зараз: {current_count}\n"
                                  f"Загальна кількість страйків: {total_strikes}")

        # Репост фото в закрытый канал с подписью бота
        bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption="ACupOfRun_bot")
    else:
        bot.send_message(user_id, "Введи /start, щоб розпочати.")

def send_morning_message():
    bot.send_message(CHANNEL_ID, "Доброго ранку!")

def send_daily_statistics():
    total_users = len(user_data)
    stats_message = f"Статистика дня:\nЗареєстровані учасники: {total_users}\n"

    for user_id, data in user_data.items():
        name = data['name']
        strikes = data['counter']
        if strikes == 0:
            stats_message += f"{name} - помідорка 🍅\n"
        else:
            stats_message += f"{name} - страйк: {strikes}\n"

    bot.send_message(CHANNEL_ID, stats_message)

def check_and_reset_counters():
    for user_id, data in user_data.items():
        if data['counter'] == 0:
            reset_counter(user_id)  # Сбрасываем счетчик если пользователь не отправил фото
        else:
            data['counter'] = 0  # Сброс счетчика для следующего часа
            data['has_sent_photo'] = False  # Сбрасываем флаг отправки фото

# Планируем обнуление счетчика каждый час
scheduler.add_job(check_and_reset_counters, CronTrigger(hour='*'))

# Планируем утреннее сообщение в закрытый канал
scheduler.add_job(send_morning_message, CronTrigger(hour=7))  # Отправляем в 7 утра

# Планируем отправку статистики в закрытый канал в конце дня
scheduler.add_job(send_daily_statistics, CronTrigger(hour=23, minute=59))  # Отправляем в 23:59

# Запуск бота и планировщика
scheduler.start()
bot.polling()
 