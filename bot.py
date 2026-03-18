import telebot
import sqlite3
import random
from telebot import types
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# --- FLASK 24/7 ---
app = Flask('')
@app.route('/')
def home(): return "MeewoolBot Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- НАСТРОЙКИ ---
TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 1864104580 

def init_db():
    conn = sqlite3.connect('meewool.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, 
                       paws INTEGER DEFAULT 0, 
                       wool INTEGER DEFAULT 0, 
                       mut_name TEXT DEFAULT 'Обычная овечка',
                       mut_emoji TEXT DEFAULT '🐑',
                       rarity TEXT DEFAULT 'Базовая',
                       last_action TEXT,
                       status INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('meewool.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def update_user(user_id, **kwargs):
    conn = sqlite3.connect('meewool.db')
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

init_db()

def get_rarity_circle(rarity):
    circles = {"Базовая": "🟢", "Редкая": "🔵", "Эпическая": "🟣", "Легендарная": "🟡", "Мифическая": "🔴", "Космическая": "⚫️"}
    return circles.get(rarity, "🟢")

def get_profile_text(u):
    now = datetime.now()
    last_t = datetime.strptime(u[6], '%Y-%m-%d %H:%M:%S')
    diff = now - last_t
    circle = get_rarity_circle(u[5])
    
    status_msg = ""
    if u[7] == 0:
        if diff >= timedelta(hours=12):
            update_user(u[0], status=1)
            status_msg = "✅ Шерсть готова к сбору."
        else:
            rem = timedelta(hours=12) - diff
            status_msg = f"⏳ Шерсть будет готова к сбору через: {str(rem).split('.')[0]}"
    elif u[7] == 1: status_msg = "✅ Шерсть готова к сбору."
    elif u[7] == 2: status_msg = "✂️ Овечка в процессе стрижки..."

    return (f"{u[4]} **{u[3]}**\n"
            f"{circle} **Статус:** {u[5]}\n"
            f"🐾 **Копытца:** {u[1]}\n"
            f"🧶 **Шерсть:** {u[2]}\n\n"
            f"{status_msg}")

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    if not get_user(message.from_user.id):
        update_user(message.from_user.id, last_action=(datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S'))
    bot.send_message(message.chat.id, "🐑 **Мее! Скорее закупайся яйцами.**", parse_mode='Markdown')

@bot.message_handler(commands=['sheep'])
def sheep_profile(message):
    u = get_user(message.from_user.id)
    if not u: return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✂️ Стрижка", callback_data='shear'),
               types.InlineKeyboardButton("💰 Продажа шерсти", callback_data='market_wool'),
               types.InlineKeyboardButton("🥚 Покупка яиц", callback_data='market_eggs'))
    bot.send_message(message.chat.id, get_profile_text(u), parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['give_paws'])
def admin_give(message):
    if message.from_user.id == ADMIN_ID:
        parts = message.text.split()
        if len(parts) == 3:
            uid = int(parts[1])
            amt = int(parts[2])
            curr = get_user(uid)
            update_user(uid, paws=curr[1] + amt)
            bot.send_message(message.chat.id, f"✅ Баланс игрока {uid} пополнен на {amt} 🐾")

# --- ЛОГИКА ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    u = get_user(call.from_user.id)
    now = datetime.now()
    last_t = datetime.strptime(u[6], '%Y-%m-%d %H:%M:%S')

    if call.data == 'shear':
        if u[7] == 0: bot.answer_callback_query(call.id, "❌ Овечка еще не готова к стрижке!", show_alert=True)
        elif u[7] == 1:
            update_user(call.from_user.id, status=2, last_action=now.strftime('%Y-%m-%d %H:%M:%S'))
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⌛️ Проверить время", callback_data='check_time'))
            bot.edit_message_text("✂️ Стрижём твою овечку. ⏳ Процесс займет: 5 мин.", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'check_time':
        diff = now - last_t
        if diff >= timedelta(minutes=5):
            gain = random.randint(5, 15)
            update_user(call.from_user.id, status=0, wool=u[2] + gain, last_action=now.strftime('%Y-%m-%d %H:%M:%S'))
            bot.edit_message_text(f"🐑 Овечка успешно пострижена! Получено: {gain} 🧶", call.message.chat.id, call.message.message_id, 
                                  reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data='back_to_profile')))
        else:
            rem = timedelta(minutes=5) - diff
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⌛️ Проверить время", callback_data='check_time'))
            bot.edit_message_text(f"✂️ Стрижём твою овечку. ⏳ Осталось ждать: {str(rem).split('.')[0]}", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'market_eggs':
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🥚 Открыть яйцо", callback_data='open_egg'),
                   types.InlineKeyboardButton("⬅️ Назад", callback_data='back_to_profile'))
        bot.edit_message_text(f"🥚 Яичный рынок.\n💰 Курс: 1 🥚 = 200 🐾", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'open_egg':
        if u[1] < 200:
            bot.answer_callback_query(call.id, "🐑 Дружок, у тебя тут не хватает!", show_alert=True)
        else:
            res = random.random() * 100
            if res <= 2: n, e, r = random.choice([("Радиоактивная овечка", "☢️"), ("Пустотная овечка", "👁️‍🗨️")]), "Космическая"
            elif res <= 10: n, e, r = random.choice([("Священная овечка", "👼"), ("Призрачная овечка", "👻")]), "Мифическая"
            elif res <= 25: n, e, r = random.choice([("Магмовая овечка", "🔥"), ("Бриллиантовая овечка", "💎")]), "Легендарная"
            elif res <= 50: n, e, r = random.choice([("Шизанутая овечка", "💥"), ("Милая овечка", "🎀")]), "Эпическая"
            else: n, e, r = random.choice([("Деревенская овечка", "🏡"), ("Пляжная овечка", "🏖️")]), "Редкая"
            update_user(call.from_user.id, paws=u[1]-200, mut_name=n, mut_emoji=e, rarity=r)
            bot.edit_message_text(f"🥚 Ты успешно открыл яйцо! Тебе выпала: {e} {n}", call.message.chat.id, call.message.message_id, 
                                  reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data='market_eggs')))

    elif call.data == 'market_wool':
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💰 Продать шерсть", callback_data='sell_wool'),
                   types.InlineKeyboardButton("⬅️ Назад", callback_data='back_to_profile'))
        bot.edit_message_text(f"🐑 Овечий рынок.\n💰 Курс: 1 🧶 = 10 🐾", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'sell_wool':
        if u[2] <= 0:
            bot.answer_callback_query(call.id, "🐑 Дружок, ты сначало овечку постриги!", show_alert=True)
        else:
            gain = u[2] * 10
            update_user(call.from_user.id, paws=u[1] + gain, wool=0)
            bot.edit_message_text(f"💰 Ты успешно продал шерсть! Получено: {gain} 🐾", call.message.chat.id, call.message.message_id, 
                                  reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data='market_wool')))

    elif call.data == 'back_to_profile':
        bot.edit_message_text(get_profile_text(u), call.message.chat.id, call.message.message_id, parse_mode='Markdown', 
                              reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
                                  types.InlineKeyboardButton("✂️ Стрижка", callback_data='shear'),
                                  types.InlineKeyboardButton("💰 Продажа шерсти", callback_data='market_wool'),
                                  types.InlineKeyboardButton("🥚 Покупка яиц", callback_data='market_eggs')))

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
