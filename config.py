# core.py
import telebot
from apscheduler.schedulers.background import BackgroundScheduler

API_TOKEN = '7338566190:AAGtOOMI8StYiU5HZ2vrkWY12QtIR6iL1n4'
bot = telebot.TeleBot(API_TOKEN)
scheduler = BackgroundScheduler()


