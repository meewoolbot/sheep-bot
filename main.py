import asyncio
import random
import time
import threading
import sqlite3
from flask import Flask
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
API_TOKEN = '7788801153:AAHpRztr5HWc4qD8upJy-2Q72Iq6Xs361pg'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

SHEEP_RARITIES = {
    "🔵 Редкая": {"items": [("Деревенская овечка", "🏡"), ("Пляжная овечка", "🏖️")], "weight": 50},
    "🟣 Эпическая": {"items": [("Шизанутая овечка", "💥"), ("Милая овечка", "🎀")], "weight": 25},
    "🟡 Легендарная": {"items": [("Магмовая овечка", "🔥"), ("Бриллиантовая овечка", "💎")], "weight": 15},
    "🔴 Мифическая": {"items": [("Священная овечка", "👼"), ("Призрачная овечка", "👻")], "weight": 9},
    "⚫️ Космическая": {"items": [("Радиоактивная овечка", "☢️"), ("Пустотная овечка", "👁️‍🗨️")], "weight": 1}
}

# --- БД ---
def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY, skin_name TEXT, skin_emoji TEXT, 
                         balance INTEGER, wool INTEGER, next_harvest REAL, 
                         is_shearing INTEGER, shear_finish REAL)''')

def get_user(user_id):
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        r = cur.fetchone()
        if not r:
            u = {"id": user_id, "skin_name": "Обычная овечка", "skin_emoji": "🐑", "balance": 0, "wool": 0, "next_harvest": time.time(), "is_shearing": 0, "shear_finish": 0}
            save_user(u)
            return u
        return {"id": r[0], "skin_name": r[1], "skin_emoji": r[2], "balance": r[3], "wool": r[4], "next_harvest": r[5], "is_shearing": r[6], "shear_finish": r[7]}

def save_user(u):
    with sqlite3.connect('database.db') as conn:
        conn.execute('REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                    (u['id'], u['skin_name'], u['skin_emoji'], u['balance'], u['wool'], u['next_harvest'], u['is_shearing'], u['shear_finish']))

# --- FLASK ---
app = Flask(__name__)
@app.route('/')
def home(): return "Sheep Farm is Alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- ЛОГИКА ---
def main_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✂️ Стрижка", callback_data="shear"))
    builder.row(types.InlineKeyboardButton(text="💰 Продажа шерсти", callback_data="market"))
    builder.row(types.InlineKeyboardButton(text="🥚 Покупка яиц", callback_data="eggs"))
    return builder.as_markup()

@dp.message(Command("start", "sheep"))
async def cmd_sheep(message: types.Message):
    u = get_user(message.from_user.id)
    now = time.time()
    timer = "✅ Шерсть готова к сбору." if now >= u['next_harvest'] else f"⏳ Готова через: {time.strftime('%H:%M:%S', time.gmtime(int(u['next_harvest']-now)))}"
    await message.answer(f"🐑 {u['skin_name']} {u['skin_emoji']}.\n🐾 Копытца: {u['balance']}\n🧶 Шерсть: {u['wool']}\n{timer}", reply_markup=main_kb())

@dp.callback_query(F.data == "shear")
async def process_shear(cb: types.CallbackQuery):
    u = get_user(cb.from_user.id); now = time.time()
    if u['is_shearing']:
        if now >= u['shear_finish']:
            gain = random.randint(5, 15)
            u['wool'] += gain; u['is_shearing'] = 0; u['next_harvest'] = now + 43200; save_user(u)
            await cb.message.edit_text(f"🐑 Овечка успешно пострижена! Получено: {gain} 🧶", reply_markup=main_kb())
        else:
            rem = int(u['shear_finish'] - now)
            kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⌛️ Проверить время", callback_data="shear")).as_markup()
            try: await cb.message.edit_text(f"✂️ Стрижём овечку. Осталось: {rem} сек.", reply_markup=kb)
            except: await cb.answer(f"Осталось: {rem} сек.")
    elif now < u['next_harvest']:
        await cb.answer("❌ Овечка еще не готова!", show_alert=True)
    else:
        u['is_shearing'] = 1; u['shear_finish'] = now + 300; save_user(u)
        kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⌛️ Проверить время", callback_data="shear")).as_markup()
        await cb.message.edit_text("✂️ Стрижём твою овечку. ⏳ Процесс займет: 5 мин.", reply_markup=kb)

@dp.callback_query(F.data == "market")
async def market(cb: types.CallbackQuery):
    kb = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="💰 Продать шерсть", callback_data="sell")).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")).as_markup()
    await cb.message.edit_text("🐑 Овечий рынок.\n💰 Курс: 1 🧶 = 10 🐾", reply_markup=kb)

@dp.callback_query(F.data == "sell")
async def sell(cb: types.CallbackQuery):
    u = get_user(cb.from_user.id)
    if u['wool'] <= 0: await cb.answer("🐑 Мее! Сначала постриги овечку.", show_alert=True)
    else:
        money = u['wool'] * 10; u['balance'] += money; u['wool'] = 0; save_user(u)
        await cb.message.edit_text(f"💰 Продано! Получено: {money} 🐾", reply_markup=InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")).as_markup())

@dp.callback_query(F.data == "eggs")
async def eggs(cb: types.CallbackQuery):
    kb = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🥚 Открыть яйцо", callback_data="open")).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")).as_markup()
    await cb.message.edit_text("🥚 Яичный рынок.\n💰 Курс: 1 🥚 = 200 🐾", reply_markup=kb)

@dp.callback_query(F.data == "open")
async def open_egg(cb: types.CallbackQuery):
    u = get_user(cb.from_user.id)
    if u['balance'] < 200: await cb.answer("❌ Мало копытц!", show_alert=True)
    else:
        u['balance'] -= 200
        r_list = list(SHEEP_RARITIES.keys())
        rarity = random.choices(r_list, weights=[SHEEP_RARITIES[k]["weight"] for k in r_list])[0]
        name, emo = random.choice(SHEEP_RARITIES[rarity]["items"])
        u['skin_name'], u['skin_emoji'] = f"{rarity}: {name}", emo; save_user(u)
        await cb.message.edit_text(f"🥚 Выпала:\n{u['skin_name']} {u['skin_emoji']}", reply_markup=InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")).as_markup())

@dp.callback_query(F.data == "back")
async def back(cb: types.CallbackQuery):
    u = get_user(cb.from_user.id); now = time.time()
    t = "✅ Шерсть готова к сбору." if now >= u['next_harvest'] else f"⏳ Готова через: {time.strftime('%H:%M:%S', time.gmtime(int(u['next_harvest']-now)))}"
    await cb.message.edit_text(f"🐑 {u['skin_name']} {u['skin_emoji']}.\n🐾 Копытца: {u['balance']}\n🧶 Шерсть: {u['wool']}\n{t}", reply_markup=main_kb())

async def main():
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
