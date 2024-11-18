import telebot
from apscheduler.schedulers.background import BackgroundScheduler

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'  # Токен бота
CHANNEL_ID = '-1002302094356'  # ID канала
ADMINS = "922094773"

class Config:
    VIDEO_FOLDER = "/path/to/your/video/folder"

# Инициализация бота и планировщика
bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=4)
scheduler = BackgroundScheduler()

# Инициализация планировщика
scheduler = BackgroundScheduler()

class AdminPanel:
    def __init__(self):
        self.panel_name = "Admin Panel"
        self.admins = []
        self.settings = {
            'theme': 'dark',
            'language': 'en'
        }
    
    def add_admin(self, admin_id):
        self.admins.append(admin_id)
    
    def remove_admin(self, admin_id):
        if admin_id in self.admins:
            self.admins.remove(admin_id)
    
    def update_setting(self, key, value):
        if key in self.settings:
            self.settings[key] = value
    
    def get_info(self):
        return {
            'panel_name': self.panel_name,
            'admins': self.admins,
            'settings': self.settings
        }



# Создание экземпляра admin_panel
admin_panel = AdminPanel()
