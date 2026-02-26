import telebot

# Сюда вставь свой токен от @BotFather (в кавычках)
TOKEN = 'ТВОЙ_ТОКЕН_ТУТ'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    # _ — это курсив, * — это жирный. Сочетаем их: _*текст*_
    text = "_🐑 *Мее*! У тебя уже есть *овечка*. 🥺_"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# Запуск бота
bot.polling(none_stop=True)
