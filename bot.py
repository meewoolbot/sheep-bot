import telebot
import sqlite3
import threading
from telebot import types
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# Настройка Flask для поддержания жизни на хостинге
app = Flask('')
@app.route('/')
def home(): return "Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# ТОКЕН БОТА
TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('pet.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, lvl INTEGER DEFAULT 0, 
                       fatigue INTEGER DEFAULT 0, grass INTEGER DEFAULT 0, 
                       sticks INTEGER DEFAULT 0, wool INTEGER DEFAULT 0,
                       last_forest TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect('pet.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# Функция выдачи лута через час
def forest_finish(user_id, chat_id):
    conn = sqlite3.connect('pet.db')
    cursor = conn.cursor()
    cursor.execute("""UPDATE users SET grass = grass + 3, lvl = lvl + 1, 
                      sticks = sticks + 2, fatigue = fatigue + 30 
                      WHERE user_id = ?""", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "_🌲 Твоя овечка вернулась из леса! Принесла: 3 травы, 2 ветки и +1 Ур._", parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id)
    if not user:
        conn = sqlite3.connect('pet.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (message.from_user.id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "_🐑 Мее! Теперь у тебя есть овечка._", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "_🐑 Мее! У тебя уже есть овечка. 🥺_", parse_mode='Markdown')

@bot.message_handler(commands=['sheep'])
def sheep_info(message):
    u = get_user(message.from_user.id)
    if not u: return
    text = f"_🐑 Твоя овечка. ( Ур. {u[1]} )\n💤 Усталость: {u[2]}_"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("✂️ Стрижка", callback_data='shear'),
               types.InlineKeyboardButton("💤 Уложить спать", callback_data='sleep'))
    markup.add(types.InlineKeyboardButton("📦 Склад", callback_data='storage'))
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    u = get_user(call.from_user.id)
    if not u: return

    if call.data == 'shear':
        if u[1] < 1:
            bot.answer_callback_query(call.id, "Овечка еще не обросла!")
        else:
            # С 19 лвл получает 19 шерсти (шерсть = уровню)
            new_wool = u[5] + u[1]
            conn = sqlite3.connect('pet.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET wool = ?, lvl = 0 WHERE user_id = ?", (new_wool, call.from_user.id))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, f"Стрижка завершена! Получено {u[1]} шерсти.", show_alert=True)
            sheep_info(call.message)

    elif call.data == 'sleep':
        if u[2] <= 0:
            bot.answer_callback_query(call.id, "Она полна сил!", show_alert=True)
        else:
            # Сон 30 мин (имитация через мгновенное вычитание или можно добавить таймер как в лесу)
            new_f = max(0, u[2] - 20)
            conn = sqlite3.connect('pet.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET fatigue = ? WHERE user_id = ?", (new_f, call.from_user.id))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, "Овечка поспала (-20 усталости)")
            sheep_info(call.message)

    elif call.data == 'storage':
        text = f"_📦 Склад:\n🌿 Трава: {u[3]}\n🪵 Веточки: {u[4]}\n🧶 Шерсть: {u[5]}_"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data='back'))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)

    elif call.data == 'back':
        text = f"_🐑 Твоя овечка. ( Ур. {u[1]} )\n💤 Усталость: {u[2]}_"
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("✂️ Стрижка", callback_data='shear'),
                   types.InlineKeyboardButton("💤 Уложить спать", callback_data='sleep'))
        markup.add(types.InlineKeyboardButton("📦 Склад", callback_data='storage'))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['forest'])
def forest(message):
    u = get_user(message.from_user.id)
    if not u: return
    
    now = datetime.now()
    if u[6]: # Проверка КД
        last_time = datetime.strptime(u[6], '%Y-%m-%d %H:%M:%S')
        if now < last_time + timedelta(hours=1):
            rem = int((last_time + timedelta(hours=1) - now).total_seconds() // 60)
            bot.send_message(message.chat.id, f"_Овечка еще в лесу. Вернется через {rem} мин._", parse_mode='Markdown')
            return

    if u[2] >= 80:
        bot.send_message(message.chat.id, "_Овечка слишком устала для гуляний!_", parse_mode='Markdown')
        return

    conn = sqlite3.connect('pet.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_forest = ? WHERE user_id = ?", (now.strftime('%Y-%m-%d %H:%M:%S'), message.from_user.id))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "_🌲 Овечка ушла в лес на час..._", parse_mode='Markdown')
    # Таймер на 1 час (3600 секунд)
    threading.Timer(3600, forest_finish, args=[message.from_user.id, message.chat.id]).start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
