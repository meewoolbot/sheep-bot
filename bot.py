import telebot
import sqlite3
import random
import time
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Овечка под дождем... 🌧"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('farm.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, wool INTEGER, last_click INTEGER, penalty INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

def update_user(user_id, username, wool_gain=0, set_last_click=False, set_penalty=0):
    conn = sqlite3.connect('farm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT wool, last_click, penalty FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    
    if not data:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (user_id, username, wool_gain, int(time.time()) if set_last_click else 0, set_penalty))
        res = (wool_gain, int(time.time()) if set_last_click else 0, set_penalty)
    else:
        new_wool = data[0] + wool_gain
        new_click = int(time.time()) if set_last_click else data[1]
        cursor.execute("UPDATE users SET wool = ?, last_click = ?, penalty = ?, username = ? WHERE user_id = ?", 
                       (new_wool, new_click, set_penalty, username, user_id))
        res = (new_wool, new_click, set_penalty)
        
    conn.commit()
    conn.close()
    return res

@bot.message_handler(commands=['start'])
def start(message):
    # Бот молчит, как ты и просил
    pass

@bot.message_handler(commands=['click'])
def click(message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Стригаль"
    
    # Получаем текущие данные без начисления
    wool, last_click, penalty = update_user(user_id, username)
    
    now = int(time.time())
    wait_time = 600 if penalty == 1 else 300
    
    if now - last_click < wait_time:
        remaining = wait_time - (now - last_click)
        bot.reply_to(message, f"⏳ Овечка восстанавливается. Подожди {remaining} сек.")
    else:
        rand = random.random() * 100
        new_penalty = 0
        gain = 0
        
        if rand <= 25: # Ливень (25%)
            res_text = "🌧 *ЛИВЕНЬ!* Овечка промокла до нитки. \n❌ Шерсти: 0. \n⏰ Следующая стрижка через 10 минут!"
            new_penalty = 1
        elif rand <= 40: # Крит (15%)
            gain = random.randint(50, 100)
            res_text = f"⚡️ *КРИТИЧЕСКИЙ УСПЕХ!* \n✂️ Ты состриг целых {gain} шерсти!"
        else: # Обычный (60%)
            gain = random.randint(5, 15)
            res_text = f"✂️ Обычная стрижка: +{gain} шерсти."
            
        update_user(user_id, username, gain, True, new_penalty)
        bot.send_message(message.chat.id, res_text, parse_mode='Markdown')

@bot.message_handler(commands=['top'])
def top(message):
    conn = sqlite3.connect('farm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, wool FROM users ORDER BY wool DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    text = "🏆 *Топ шерстяных магнатов* \n\n"
    for i, row in enumerate(rows, 1):
        # row[0] - имя, row[1] - шерсть. Тире убраны.
        text += f"{i}. {row[0]} {row[1]} 🧶\n"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Стригаль"
    wool, _, _ = update_user(user_id, username)
    bot.reply_to(message, f"📊 Мой мешок\n🧶 Шерсти в запасе {wool}")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
