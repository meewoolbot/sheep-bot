import telebot

TOKEN = '8339481234:AAGurTvdvnjPcdzlULjr-qkmnumAbpaFMWU'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    # Разметка: _ - курсив, * - жирный
    text = "_🐑 *Мее*! У тебя уже есть *овечка*. 🥺_"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

if __name__ == "__main__":
    bot.polling(none_stop=True)
