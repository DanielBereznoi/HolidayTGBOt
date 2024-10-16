from contextlib import suppress
from time import sleep

import telebot
from six import print_
from telebot import types
import time
import datetime
import event_service
import saved_token
import threading

bot = telebot.TeleBot(token=saved_token.token)

current_transactions = {}


def check_transaction_timeout():
    while True:
        print("Checking transaction timeout...")
        # Directly remove timed-out transactions
        keys_to_remove = [key for key, value in current_transactions.items() if value[0] + 2 * 60 <= time.time()]
        delete_transactions(keys_to_remove)
        time.sleep(10)


def delete_transactions(keys):
    for key in keys:
        print('Deleting transactions...')
        bot.send_message(key, "Transaction timed out")
        current_transactions.pop(key, None)  # Use pop with default to avoid errors


def check_date():
    while True:
        print("Checking date...")
        is_eventful_day = event_service.check_dates()
        print(is_eventful_day)
        if is_eventful_day:
            events_for_today = event_service.get_events_by_today()
            for event in events_for_today:
                bot.send_message(event[0], f'Don\'t forget about {event[2]}!')
            event_service.update_events(events_for_today)
        else:
            sleep(3600)


transaction_check_thread = threading.Thread(target=check_transaction_timeout)
date_check_thread = threading.Thread(target=check_date)

transaction_check_thread.start()
date_check_thread.start()


def validate_date(date_string):
    date_format = "%d.%m.%Y"
    try:
        date = datetime.datetime.strptime(date_string, date_format)
        if date > datetime.date.today():
            return True
        else:
            return False
    except ValueError:
        return False


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Hello {message.chat.username}!")
    print(message)


@bot.message_handler(commands=['addrepeatingevent'])
def add_new_occasion(message):
    bot.send_message(message.chat.id, "Insert event name")
    current_transactions[message.chat.id] = [time.time(), True]
    print("Added the new event")


@bot.message_handler(commands=['addevent'])
def add_new_occasion(message):
    bot.send_message(message.chat.id, "Insert your event name")
    print("added the new event)")
    current_transactions[message.chat.id] = [time.time(), False]


@bot.message_handler(commands=['deleteevent'])
def delete_holiday(message):
    chat_events = event_service.get_events_by_chat_id(message.chat.id)
    markup = types.InlineKeyboardMarkup()
    for event in chat_events:
        markup.add(types.InlineKeyboardButton(text=f'{str(event[1])} - {str(event[2])}',
                                              callback_data=str(event[3])))
    bot.reply_to(message, reply_markup=markup, text="Select event what you want to delete")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(callback):
    event_service.delete_data_from_db(callback.data)
    bot.send_message(callback.message.chat.id, "Event deleted")


@bot.message_handler(commands=['allevents'])
def all_holidays(message):
    events = event_service.get_events_by_chat_id(message.chat.id)
    reply = ""
    for event in events:
        reply += f'{event[1].strftime("%d.%m.%Y")} - {event[2]}\n'
    bot.reply_to(message, reply)


@bot.message_handler(commands=['cancel'])
def cancel(message):
    current_transactions.pop(message.chat.id)
    print("cancel")


@bot.message_handler(commands=['stop'])
def stop(message):
    print("stop")


@bot.message_handler()
def handle_replies(message):
    message_text = message.text
    if message_text not in ["/start", "/help", "/addevent", "/addrepeatingevent",
                            "/deleteevent", "/allevents", "/cancel", "/stop"]:
        chat_id = message.chat.id
        if chat_id in current_transactions:
            halves = message_text.split(" - ")
            if len(halves) == 2:
                valid_date = validate_date(halves[0])
                event_name = halves[1]
                if valid_date and len(event_name) <= 100:
                    succeeded = event_service.add_data_to_db(chat_id, halves[0], event_name,
                                                             current_transactions[chat_id][1])
                    if not succeeded:
                        bot.reply_to(message, "Something wrong")
                    else:
                        bot.reply_to(message, "Event added")
                    cancel(message)
                else:
                    error_message = "Invalid input."
                    if not valid_date:
                        error_message = "Invalid date. Please use the format dd.MM.yyyy."
                    if len(event_name) > 100:
                        error_message = "Event name must be under 100 characters."
                    bot.send_message(chat_id, error_message)
            else:
                bot.send_message(chat_id, "Invalid input format. Use 'dd.MM.yyyy - event name'.")

    print(message.text)


bot.polling(non_stop=True)
