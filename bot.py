import telebot
import sqlite3
import random
import time
from telebot import types
from flask import Flask
from threading import Thread

# 1. Мини-сервер для "оживления" на Render
app = Flask('')

@app.route('/')
def home():
    return "Овечка бодрствует! 🐑"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)

# 2. Настройка базы данных
def init_db():
    conn = sqlite3.connect('farm.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, wool INTEGER, last_click INTEGER)''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id, username):
    conn = sqlite3.connect('farm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT wool, last_click FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    if not data:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, username, 0, 0))
        conn.commit()
        data = (0, 0)
    conn.close()
    return data

@bot.message_handler(commands=['start', 'sheep'])
def start(message):
    bot.send_message(message.chat.id, "_🐑 *Мее*! Твоя овечка ждет стрижки. Используй /click_", parse_mode='Markdown')

@bot.message_handler(commands=['click'])
def click(message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Аноним"
    wool, last_click = get_user(user_id, username)
    
    now = int(time.time())
    wait_time = 300 
    
    if now - last_click < wait_time:
        remaining = wait_time - (now - last_click)
        bot.reply_to(message, f"⏳ Овечка еще не обросла! Подожди еще {remaining} сек.")
    else:
        gain = random.randint(5, 15)
        new_wool = wool + gain
        conn = sqlite3.connect('farm.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET wool = ?, last_click = ?, username = ? WHERE user_id = ?", 
                       (new_wool, now, username, user_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✂️ ТРРР! Ты состриг {gain} шерсти! \n🧶 Всего в мешке: {new_wool}")

@bot.message_handler(commands=['top'])
def top(message):
    conn = sqlite3.connect('farm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, wool FROM users ORDER BY wool DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    text = "🏆 *ТОП ЛУЧШИХ СТРИГАЛЕЙ:* \n\n"
    for i, row in enumerate(rows, 1):
        # Убрали тире, теперь просто Имя и Число
        text += f"{i}. {row[0]} {row[1]} 🧶\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    wool, _ = get_user(user_id, message.from_user.first_name)
    bot.reply_to(message, f"📊 Твоя статистика:\n🧶 Собрано шерсти {wool}")

# Запуск сервера и бота
if __name__ == "__main__":
    keep_alive() # Запускаем "будильник" для Render
    bot.infinity_polling()
