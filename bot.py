import telebot
import sqlite3
import random
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('pet.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, trait TEXT, trait_desc TEXT)''')
    conn.commit()
    conn.close()
init_db()

@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('pet.db')
    cursor = conn.cursor()
    cursor.execute("SELECT trait FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🐑 Завести овечку", callback_data='create_pet'))
        bot.send_message(message.chat.id, "_У тебя еще нет друга... Надо завести! 🥺_", 
                         parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "_Твоя овечка уже ждет тебя! 🐑_", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'create_pet')
def create_pet(call):
    # Настраиваем характеры
    traits = [
        ('Обжора 🍎', 'будет хотеть кушать постоянно'),
        ('Соня 💤', 'любит поспать подольше'),
        ('Исследователь 🧭', 'обожает долгие прогулки')
    ]
    my_trait, my_desc = random.choice(traits)
    
    conn = sqlite3.connect('pet.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (call.from_user.id, my_trait, my_desc))
        conn.commit()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"✨ *Поздравляем!*\n\nТвоя овечка родилась!\nХарактер: *{my_trait}*\nОна *{my_desc}*.", 
                              parse_mode='Markdown')
    except:
        bot.answer_callback_query(call.id, "У тебя уже есть овечка!")
    conn.close()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
