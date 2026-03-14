import telebot
import sqlite3
import random
import threading
from telebot import types
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

app = Flask('')
@app.route('/')
def home(): return "Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('office.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS slaves 
                      (user_id INTEGER PRIMARY KEY, lvl INTEGER DEFAULT 0, 
                       stress INTEGER DEFAULT 0, money INTEGER DEFAULT 0, 
                       coffee_lvl INTEGER DEFAULT 0, last_work TEXT, last_seen TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect('office.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM slaves WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# Пассивное снижение стресса при просмотре профиля
def refresh_stress(user_id):
    u = get_user(user_id)
    if not u or not u[6]: return
    last_seen = datetime.strptime(u[6], '%Y-%m-%d %H:%M:%S')
    minutes_passed = int((datetime.now() - last_seen).total_seconds() // 60)
    if minutes_passed > 0:
        new_stress = max(0, u[2] - minutes_passed)
        conn = sqlite3.connect('office.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE slaves SET stress = ?, last_seen = ? WHERE user_id = ?", 
                       (new_stress, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
        conn.commit()
        conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    if not get_user(message.from_user.id):
        conn = sqlite3.connect('office.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO slaves (user_id, last_seen) VALUES (?, ?)", 
                       (message.from_user.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    bot.send_message(message.chat.id, "_🐑 Твоя овечка устроилась в офис. Приготовься к дедлайнам._", parse_mode='Markdown')

@bot.message_handler(commands=['office'])
def office_info(message):
    refresh_stress(message.from_user.id)
    u = get_user(message.from_user.id)
    if not u: return
    text = (f"_💼 **Офисный раб №{message.from_user.id}**\n\n"
            f"🎓 Квалификация: {u[1]}\n"
            f"🤯 Стресс: {u[2]}%\n"
            f"☕ Кофеин: {u[4]}/5\n"
            f"💰 Бюджет: {u[3]}$_")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("☕ Кофе", callback_data='drink_coffee'),
               types.InlineKeyboardButton("📈 Бонус", callback_data='get_bonus'))
    markup.add(types.InlineKeyboardButton("📦 Хлам", callback_data='storage'))
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['snitch'])
def snitch(message):
    if not message.reply_to_message:
        bot.reply_to_message(message, "_Чтобы настучать, ответь этой командой на сообщение коллеги!_")
        return
    
    snitcher_id = message.from_user.id
    victim_id = message.reply_to_message.from_user.id
    
    if snitcher_id == victim_id:
        bot.send_message(message.chat.id, "_Ты пытался настучать на самого себя? Это уже клиника._")
        return

    victim = get_user(victim_id)
    if not victim:
        bot.send_message(message.chat.id, "_Этот человек еще не работает в нашем офисе._")
        return

    conn = sqlite3.connect('office.db')
    cursor = conn.cursor()
    # Настучавшему +20$, Жертве +40% стресса
    cursor.execute("UPDATE slaves SET money = money + 20 WHERE user_id = ?", (snitcher_id,))
    cursor.execute("UPDATE slaves SET stress = min(100, stress + 40) WHERE user_id = ?", (victim_id,))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, f"_🤫 Овечка нашептала боссу о косяках коллеги!\n➕ Тебе: **+20$**\n💥 Жертве: **+40% стресса**_", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_office_cb(call):
    u = get_user(call.from_user.id)
    if not u: return

    if call.data == 'drink_coffee':
        if u[4] >= 5:
            conn = sqlite3.connect('office.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM slaves WHERE user_id = ?", (call.from_user.id,))
            conn.commit()
            conn.close()
            bot.edit_message_text("_💀 Передозировка! Овечка увидела розовых слонов и уволилась из жизни._", 
                                  call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        else:
            conn = sqlite3.connect('office.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE slaves SET coffee_lvl = coffee_lvl + 1, stress = max(0, stress - 30) WHERE user_id = ?", (call.from_user.id,))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, "Эспрессо зашел! Стресс -30%")
            office_info(call.message)

    elif call.data == 'get_bonus':
        bonus = u[1] * 25
        conn = sqlite3.connect('office.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE slaves SET money = money + ?, lvl = 0 WHERE user_id = ?", (bonus, call.from_user.id))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"Премия {bonus}$ получена!", show_alert=True)
        office_info(call.message)

    elif call.data == 'storage':
        bot.edit_message_text(f"_📦 Склад:\n📎 Скрепки: {u[1]*3}\n💵 Деньги: {u[3]}$_", 
                              call.message.chat.id, call.message.message_id, parse_mode='Markdown', 
                              reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Назад", callback_data='back')))

    elif call.data == 'back':
        office_info(call.message)

@bot.message_handler(commands=['work'])
def work(message):
    u = get_user(message.from_user.id)
    if u[2] >= 90:
        bot.send_message(message.chat.id, "_🤯 У овечки нервный тик! Она не может работать со стрессом 90%._")
        return
    
    now = datetime.now()
    if u[5]: 
        last_time = datetime.strptime(u[5], '%Y-%m-%d %H:%M:%S')
        if now < last_time + timedelta(hours=1):
            bot.send_message(message.chat.id, "_⌨️ Овечка усиленно имитирует бурную деятельность..._")
            return

    conn = sqlite3.connect('office.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE slaves SET last_work = ?, coffee_lvl = 0 WHERE user_id = ?", (now.strftime('%Y-%m-%d %H:%M:%S'), message.from_user.id))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "_⌨️ Овечка открыла Excel. Час страданий начался._")
    threading.Timer(3600, work_done, args=[message.from_user.id, message.chat.id]).start()

def work_done(user_id, chat_id):
    conn = sqlite3.connect('office.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE slaves SET money = money + 60, lvl = lvl + 1, stress = stress + 35 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "_📊 Дедлайн закрыт! +60$ и +1 квалификация. Но глаз дергается сильнее._")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
