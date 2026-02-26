import telebot

# Твой проверенный токен
TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    # Тут магия: parse_mode='Markdown' заставляет звезды исчезнуть и превратиться в жирный шрифт
    text = "_🐑 *Мее*! У тебя уже есть *овечка*. 🥺_"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# Запуск 24/7
if __name__ == "__main__":
    bot.polling(none_stop=True)
