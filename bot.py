import telebot

# Твой рабочий токен
TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    # Просто текст, никакой лишней разметки
    bot.send_message(message.chat.id, "🐑 Мее! У тебя уже есть овечка. 🥺")

# Бесконечный цикл, чтобы не вырубался
if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
