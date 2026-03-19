import asyncio, random, time, threading, sqlite3, os
from flask import Flask
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = '8339481234:AAGd1Odibul01mCKjqRjtQME4ddyQnTL8As' 
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

RARITIES = {
    "🔵 Редкая": {"items": ["🏡 Деревенская овечка", "🏖️ Пляжная овечка"], "w": 50},
    "🟣 Эпическая": {"items": ["💥 Шизанутая овечка", "🎀 Милая овечка"], "w": 25},
    "🟡 Легендарная": {"items": ["🔥 Магмовая овечка", "💎 Бриллиантовая овечка"], "w": 15},
    "🔴 Мифическая": {"items": ["👼 Священная овечка", "👻 Призрачная овечка"], "w": 9},
    "⚫️ Космическая": {"items": ["☢️ Радиоактивная овечка", "👁️‍🗨️ Пустотная овечка"], "w": 1}
}

def init_db():
    with sqlite3.connect('farm.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, skin TEXT, balance INTEGER, wool INTEGER, harvest REAL, shearing INTEGER, s_finish REAL)')

def get_u(uid):
    with sqlite3.connect('farm.db') as conn:
        cur = conn.cursor(); cur.execute("SELECT * FROM users WHERE id=?", (uid,))
        r = cur.fetchone()
        if not r:
            u = {"id": uid, "skin": "🐑 Обычная овечка", "balance": 0, "wool": 0, "harvest": time.time(), "shearing": 0, "s_finish": 0}
            save_u(u); return u
        return {"id": r[0], "skin": r[1], "balance": r[2], "wool": r[3], "harvest": r[4], "shearing": r[5], "s_finish": r[6]}

def save_u(u):
    with sqlite3.connect('farm.db') as conn:
        conn.execute('REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?)', (u['id'], u['skin'], u['balance'], u['wool'], u['harvest'], u['shearing'], u['s_finish']))

app = Flask(__name__)
@app.route('/')
def h(): return "OK"

def main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="✂️ Стрижка", callback_data="shear"))
    kb.row(types.InlineKeyboardButton(text="💰 Продажа шерсти", callback_data="market"))
    kb.row(types.InlineKeyboardButton(text="🥚 Покупка яиц", callback_data="eggs"))
    return kb.as_markup()

@dp.message(Command("start"))
async def st(m: types.Message):
    await m.answer("🐑 Мее! скорее закупайся яйцами.")

@dp.message(Command("sheep"))
async def sh(m: types.Message):
    u = get_u(m.from_user.id); now = time.time()
    t = "✅ Шерсть готова к сбору." if now >= u['harvest'] else f"⏳ Шерсть будет готова к сбору через: {time.strftime('%H:%M:%S', time.gmtime(int(u['harvest']-now)))}"
    # Убрал /sheep в начале
    await m.answer(f"{u['skin']}\n🐾 Копытца: {u['balance']}\n{t}", reply_markup=main_kb())

@dp.callback_query(F.data == "shear")
async def shear(cb: types.CallbackQuery):
    u = get_u(cb.from_user.id); now = time.time()
    
    if u['shearing']:
        if now >= u['s_finish']:
            gain = random.randint(5, 15); u['wool'] += gain; u['shearing'] = 0; u['harvest'] = now + 43200; save_u(u)
            await cb.message.edit_text(f"🐑 Овечка успешно пострижена! Получено: {gain} 🧶", reply_markup=main_kb())
        else:
            rem = int(u['s_finish'] - now)
            m, s = divmod(rem, 60)
            kb = InlineKeyboardBuilder()
            kb.row(types.InlineKeyboardButton(text="⌛️ Проверить время", callback_data="shear"))
            kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
            # Пытаемся обновить текст, если время реально изменилось
            try:
                await cb.message.edit_text(f"✂️ Стрижём твою овечку. ⏳ Процесс займет: {m} мин. {s} сек.", reply_markup=kb.as_markup())
            except:
                await cb.answer(f"⏳ Осталось: {m} мин. {s} сек.")
                
    elif now < u['harvest']:
        await cb.answer("❌ Овечка еще не готова к стрижке!", show_alert=True)
    else:
        u['shearing'] = 1; u['s_finish'] = now + 300; save_u(u)
        kb = InlineKeyboardBuilder()
        kb.row(types.InlineKeyboardButton(text="⌛️ Проверить время", callback_data="shear"))
        kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await cb.message.edit_text("✂️ Стрижём твою овечку. ⏳ Процесс займет: 5 мин.", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "market")
async def market(cb: types.CallbackQuery):
    kb = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="💰 Продать шерсть", callback_data="sell")).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")).as_markup()
    await cb.message.edit_text("🐑 Овечий рынок.\n💰Курс: 1 🧶 = 10 🐾", reply_markup=kb)

@dp.callback_query(F.data == "sell")
async def sell(cb: types.CallbackQuery):
    u = get_u(cb.from_user.id)
    if u['wool'] <= 0:
        await cb.answer("🐑 Мее! Дружок, постриги сначала свою овечку.", show_alert=True)
    else:
        m_val = u['wool'] * 10; u['balance'] += m_val; u['wool'] = 0; save_u(u)
        kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")).as_markup()
        await cb.message.edit_text(f"💰 Ты успешно продал всю шерсть! \nПолучено: {m_val} 🐾", reply_markup=kb)

@dp.callback_query(F.data == "eggs")
async def eggs(cb: types.CallbackQuery):
    kb = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🥚 Открыть яйцо", callback_data="open")).row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")).as_markup()
    await cb.message.edit_text("🥚 Яичный рынок.\n💰 Курс: 1 🥚 = 200 🐾", reply_markup=kb)

@dp.callback_query(F.data == "open")
async def open_e(cb: types.CallbackQuery):
    u = get_u(cb.from_user.id)
    if u['balance'] < 200:
        await cb.answer("❌ Недостаточно копытц!", show_alert=True)
    else:
        u['balance'] -= 200; r_l = list(RARITIES.keys()); rarity = random.choices(r_l, weights=[RARITIES[k]["w"] for k in r_l])[0]
        u['skin'] = f"{rarity}: {random.choice(RARITIES[rarity]['items'])}"; save_u(u)
        kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back")).as_markup()
        await cb.message.edit_text(f"🥚 Ты открыл яйцо! Тебе выпала: {u['skin']}", reply_markup=kb)

@dp.callback_query(F.data == "back")
async def back(cb: types.CallbackQuery):
    u = get_u(cb.from_user.id); now = time.time()
    t = "✅ Шерсть готова к сбору." if now >= u['harvest'] else f"⏳ Шерсть будет готова к сбору через: {time.strftime('%H:%M:%S', time.gmtime(int(u['harvest']-now)))}"
    await cb.message.edit_text(f"{u['skin']}\n🐾 Копытца: {u['balance']}\n{t}", reply_markup=main_kb())

async def main():
    init_db()
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
