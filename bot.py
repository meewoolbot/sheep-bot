import asyncio
import random
import time
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = 'ТВОЙ_ТОКЕН'
users_data = {} 

# --- РЕДКОСТИ И ШАНСЫ ---
SHEEP_RARITIES = {
    "🔵 Редкая": {"items": [("Деревенская овечка", "🏡"), ("Пляжная овечка", "🏖️")], "weight": 50},
    "🟣 Эпическая": {"items": [("Шизанутая овечка", "💥"), ("Милая овечка", "🎀")], "weight": 25},
    "🟡 Легендарная": {"items": [("Магмовая овечка", "🔥"), ("Бриллиантовая овечка", "💎")], "weight": 15},
    "🔴 Мифическая": {"items": [("Священная овечка", "👼"), ("Призрачная овечка", "👻")], "weight": 9},
    "⚫️ Космическая": {"items": [("Радиоактивная овечка", "☢️"), ("Пустотная овечка", "👁️‍🗨️")], "weight": 1}
}

# --- FLASK (Порт 8080) ---
app = Flask(__name__)
@app.route('/')
def index():
    return f"Бот запущен. Игроков: {len(users_data)}"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- ЛОГИКА БОТА ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def get_user(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "skin_name": "Обычная овечка", "skin_emoji": "🐑",
            "balance": 0, "wool": 0, 
            "next_harvest": time.time(), # Сразу готова при первом старте
            "is_shearing": False, "shear_finish": 0
        }
    return users_data[user_id]

def get_main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="✂️ Стрижка", callback_data="shear"))
    kb.row(types.InlineKeyboardButton(text="💰 Продажа шерсти", callback_data="market"))
    kb.row(types.InlineKeyboardButton(text="🥚 Покупка яиц", callback_data="eggs"))
    return kb.as_markup()

# --- КОМАНДА /SHEEP (ПРОФИЛЬ) ---
@dp.message(Command("start", "sheep"))
async def cmd_sheep(message: types.Message):
    user = get_user(message.from_user.id)
    now = time.time()
    
    if now >= user["next_harvest"]:
        timer_text = "✅ Шерсть готова к сбору."
    else:
        rem = int(user["next_harvest"] - now)
        timer_text = f"⏳ Шерсть будет готова к сбору через: {time.strftime('%H:%M:%S', time.gmtime(rem))}"

    text = (f"🐑 {user['skin_name']}.\n"
            f"🐾 Копытца: {user['balance']}\n"
            f"🧶 Шерсть: {user['wool']}\n"
            f"{timer_text}")
    
    await message.answer(text, reply_markup=get_main_kb())

# --- ОБРАБОТКА КНОПОК ---
@dp.callback_query(F.data == "shear")
async def process_shear(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    now = time.time()

    if user["is_shearing"]:
        if now >= user["shear_finish"]:
            gain = random.randint(5, 15)
            user["wool"] += gain
            user["is_shearing"] = False
            user["next_harvest"] = now + 43200 # 12 часов до след. раза
            await callback.message.edit_text(f"🐑 Овечка успешно пострижена! Получено: {gain} 🧶", reply_markup=get_main_kb())
        else:
            # Обновление времени в процессе стрижки
            rem = int(user["shear_finish"] - now)
            kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⌛️ Проверить время", callback_data="shear"))
            try: # Чтобы не падало, если текст не изменился
                await callback.message.edit_text(f"✂️ Стрижём твою овечку.\n⏳ Осталось: {rem} сек.", reply_markup=kb.as_markup())
            except:
                await callback.answer(f"Осталось: {rem} сек.")
            
    elif now < user["next_harvest"]:
        await callback.answer("❌ Овечка еще не готова к стрижке!", show_alert=True)
    else:
        user["is_shearing"] = True
        user["shear_finish"] = now + 300 # 5 минут
        kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⌛️ Проверить время", callback_data="shear"))
        await callback.message.edit_text("✂️ Стрижём твою овечку. ⏳ Процесс займет: 5 мин.", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "market")
async def market(callback: types.CallbackQuery):
    text = "🐑 Овечий рынок.\n💰 Курс: 1 🧶 = 10 🐾"
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="💰 Продать шерсть", callback_data="sell_all"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "sell_all")
async def sell_wool(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    if user["wool"] <= 0:
        await callback.answer("🐑 Мее! Дружок, постриги сначало свою овечку.", show_alert=True)
    else:
        money = user["wool"] * 10
        user["balance"] += money
        user["wool"] = 0
        kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
        await callback.message.edit_text(f"💰 Ты успешно продал всю шерсть!\nПолучено: {money} 🐾", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "eggs")
async def eggs_market(callback: types.CallbackQuery):
    text = "🥚 Яичный рынок.\n💰 Курс: 1 🥚 = 200 🐾"
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🥚 Открыть яйцо", callback_data="open_egg"))
    kb.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    await callback.message.edit_text(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "open_egg")
async def open_egg(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    if user["balance"] < 200:
        await callback.answer("❌ Недостаточно копытц!", show_alert=True)
        return

    user["balance"] -= 200
    rarity_list = list(SHEEP_RARITIES.keys())
    weights = [SHEEP_RARITIES[r]["weight"] for r in rarity_list]
    rarity = random.choices(rarity_list, weights=weights, k=1)[0]
    name, emoji = random.choice(SHEEP_RARITIES[rarity]["items"])
    
    user["skin_name"] = f"{rarity}: {name}"
    user["skin_emoji"] = emoji
    
    kb = InlineKeyboardBuilder().add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    await callback.message.edit_text(f"🥚 Ты открыл яйцо! Тебе выпала:\n{user['skin_name']} {user['skin_emoji']}", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "back")
async def back_to_profile(callback: types.CallbackQuery):
    # Вместо удаления просто вызываем логику обновления сообщения как в /sheep
    user = get_user(callback.from_user.id)
    now = time.time()
    timer_text = "✅ Шерсть готова к сбору." if now >= user["next_harvest"] else f"⏳ Готова через: {time.strftime('%H:%M:%S', time.gmtime(int(user['next_harvest']-now)))}"
    text = (f"🐑 {user['skin_name']}.\n🐾 Копытца: {user['balance']}\n🧶 Шерсть: {user['wool']}\n{timer_text}")
    await callback.message.edit_text(text, reply_markup=get_main_kb())

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
