import telebot
import sqlite3
import random
import time
from telebot import types
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# --- НАСТРОЙКА FLASK ДЛЯ 24/7 ---
app = Flask('')
@app.route('/')
def home(): return "MeewoolBot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- ТОКЕН И ИНИЦИАЛИЗАЦИЯ ---
# Замени TOKEN на свой, если он изменился
TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 1864104580  # Твой ID

# --- БАЗА ДАННЫХ ---
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
    u = cursor.fetchone()
    conn.close()
    return u

def update_user(user_id, **kwargs):
    conn = sqlite3.connect('meewool.db')
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

init_db()

# --- КОМАНДЫ ИГРОКА ---
@bot.message_handler(commands=['start'])
def start(message):
    if not get_user(message.from_user.id):
        conn = sqlite3.connect('meewool.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, last_action) VALUES (?, ?)", 
                       (message.from_user.id, (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    bot.send_message(message.chat.id, "🐑 **Мее! Скорее закупайся яйцами.**", parse_mode='Markdown')

@bot.message_handler(commands=['sheep'])
def sheep_profile(message):
    u = get_user(message.from_user.id)
    if not u: return

    now = datetime.now()
    last_t = datetime.strptime(u[6], '%Y-%m-%d %H:%M:%S')
    diff = now - last_t
    
    status_text = ""
    if u[7] == 0:
        if diff >= timedelta(hours=12):
            update_user(message.from_user.id, status=1)
            status_text = "✅ Шерсть готова к сбору."
        else:
            rem = timedelta(hours=12) - diff
            status_text = f"⏳ Шерсть будет готова через: {str(rem).split('.')[0]}"
    elif u[7] == 1:
        status_text = "✅ Шерсть готова к сбору."
    elif u[7] == 2:
        if diff >= timedelta(minutes=5):
            status_text = "✅ Процесс стрижки завершен!"
        else:
            rem = timedelta(minutes=5) - diff
            status_text = f"✂️ Стрижка... осталось: {str(rem).split('.')[0]}"

    text = (f"{u[4]} **{u[3]}**\n"
            f"🔴 Статус: {u[5]}\n"
            f"🐾 Копытца: {u[1]}\n"
            f"⏳ {status_text}")

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✂️ Стрижка", callback_data='shear'),
        types.InlineKeyboardButton("💰 Продажа шерсти", callback_data='market'),
        types.InlineKeyboardButton("🥚 Покупка яиц", callback_data='buy_eggs')
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

# --- УМНАЯ АДМИН-ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        text = (f"👑 **Панель Пастуха**\n\n"
                f"`/give_paws ID кол-во` — выдать копытца\n"
                f"`/give_wool ID кол-во` — выдать шерсть\n"
                f"`/set_rare ID` — выдать Мифическую\n"
                f"`/db_size` — кол-во игроков\n\n"
                f"Твой ID: `{message.from_user.id}`")
        bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['give_paws'])
def admin_give_paws(message):
    if message.from_user.id == ADMIN_ID:
        parts = message.text.split()
        if len(parts) == 3:
            try:
                target_id = int(parts[1])
                amount = int(parts[2])
                u = get_user(target_id)
                if u:
                    update_user(target_id, paws=u[1] + amount)
                    bot.send_message(message.chat.id, f"✅ Выдано {amount} 🐾 игроку {target_id}")
                else: bot.send_message(message.chat.id, "❌ Игрок не найден.")
            except: bot.send_message(message.chat.id, "Ошибка в числах!")
        else: bot.send_message(message.chat.id, "Формат: `/give_paws ID кол-во`")

@bot.message_handler(commands=['give_wool'])
def admin_give_wool(message):
    if message.from_user.id == ADMIN_ID:
        parts = message.text.split()
        if len(parts) == 3:
            try:
                target_id = int(parts[1])
                amount = int(parts[2])
                u = get_user(target_id)
                if u:
                    update_user(target_id, wool=u[2] + amount)
                    bot.send_message(message.chat.id, f"✅ Выдано {amount} 🧶 игроку {target_id}")
            except: bot.send_message(message.chat.id, "Ошибка!")

@bot.message_handler(commands=['db_size'])
def admin_db_size(message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('meewool.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        bot.send_message(message.chat.id, f"📊 Всего игроков: {count}")

# --- CALLBACK LOGIC ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    u = get_user(call.from_user.id)
    if not u: return
    now = datetime.now()
    last_t = datetime.strptime(u[6], '%Y-%m-%d %H:%M:%S')

    if call.data == 'shear':
        if u[7] == 0:
            bot.answer_callback_query(call.id, "❌ Овечка еще не готова к стрижке!", show_alert=True)
        elif u[7] == 1:
            update_user(call.from_user.id, status=2, last_action=now.strftime('%Y-%m-%d %H:%M:%S'))
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⌛️ Проверить время", callback_data='check_shear'))
            bot.edit_message_text("✂️ Стрижём твою овечку. ⏳ Процесс займет: 5 мин.", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'check_shear':
        if (now - last_t) >= timedelta(minutes=5):
            gain = random.randint(5, 15)
            update_user(call.from_user.id, status=0, wool=u[2] + gain, last_action=now.strftime('%Y-%m-%d %H:%M:%S'))
            bot.edit_message_text(f"🐑 Овечка успешно пострижена! Получено: {gain} 🧶", call.message.chat.id, call.message.message_id, 
                                  reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data='back')))
        else: bot.answer_callback_query(call.id, "Еще не закончили!")

    elif call.data == 'market':
        text = f"🐑 Овечий рынок.\n💰 Курс: 1 🧶 = 10 🐾\nУ тебя: {u[2]} 🧶"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("💰 Продать", callback_data='sell'), types.InlineKeyboardButton("⬅️ Назад", callback_data='back'))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'sell':
        if u[2] <= 0: bot.answer_callback_query(call.id, "🐑 Мее! Сначала постриги овечку.", show_alert=True)
        else:
            money = u[2] * 10
            update_user(call.from_user.id, paws=u[1] + money, wool=0)
            bot.edit_message_text(f"💰 Продано! Получено: {money} 🐾", call.message.chat.id, call.message.message_id, 
                                  reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data='back')))

    elif call.data == 'buy_eggs':
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🥚 Открыть", callback_data='open_egg'), types.InlineKeyboardButton("⬅️ Назад", callback_data='back'))
        bot.edit_message_text(f"🥚 Яичный рынок.\n💰 Цена: 200 🐾\nБаланс: {u[1]} 🐾", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'open_egg':
        if u[1] < 200: bot.answer_callback_query(call.id, "❌ Мало копытц!", show_alert=True)
        else:
            res = random.random() * 100
            if res <= 2: n, e, r = random.choice([("Радиоактивная овечка", "☢️"), ("Пустотная овечка", "👁️‍🗨️")]), "Космическая ⚫️"
            elif res <= 10: n, e, r = random.choice([("Священная овечка", "👼"), ("Призрачная овечка", "👻")]), "Мифическая 🔴"
            elif res <= 25: n, e, r = random.choice([("Магмовая овечка", "🔥"), ("Бриллиантовая овечка", "💎")]), "Легендарная 🟡"
            elif res <= 50: n, e, r = random.choice([("Шизанутая овечка", "💥"), ("Милая овечка", "🎀")]), "Эпическая 🟣"
            else: n, e, r = random.choice([("Деревенская овечка", "🏡"), ("Пляжная овечка", "🏖️")]), "Редкая 🔵"
            update_user(call.from_user.id, paws=u[1]-200, mut_name=n, mut_emoji=e, rarity=r)
            bot.edit_message_text(f"🥚 Тебе выпала:\n{r} {n}", call.message.chat.id, call.message.message_id, 
                                  reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data='back')))

    elif call.data == 'back':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        sheep_profile(call.message)

if __name__ == "__main__":
    init_db()
    keep_alive()
    bot.infinity_polling()
