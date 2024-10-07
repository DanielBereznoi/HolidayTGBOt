import telebot

bot = telebot.TeleBot(token='7966855356:AAGZ-GyRAY20OI-QQDM6bWFbh98S4vW4OVU')

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Hello {message.chat.username}!")


@bot.message_handler(commands=['addNewOccasion'])
def add_new_occasion(message):
    print(message.chat.id)

@bot.message_handler(content_types=['deleteHoliday'])
def delete_holiday(message):
    print()

@bot.message_handler()
def info(message):
    if message.text.lower() == "hola":
        bot.send_message(message.chat.id, "Hola, Combrero")
    elif message.text.lower() == "tere":
        bot.send_message(message.chat.id, "Tere, tere vanakere")

bot.polling(non_stop=True)