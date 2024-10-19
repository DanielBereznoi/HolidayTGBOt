from contextlib import suppress
from time import sleep
from collections import defaultdict
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telebot
from six import print_
from telebot import types
import time
from datetime import date, datetime
import event_service
import saved_token
import threading
import re

bot = telebot.TeleBot(token=saved_token.token)

special_char_pattern = re.compile(r'[@_!#$%^&*()<>?/\|}{~:]')
current_transactions = {}


def check_transaction_timeout():
    while True:
        print("Checking transaction timeout...")
        # Directly remove timed-out transactions
        keys_to_remove = [key for key, value in current_transactions.items() if value[0] + 4 * 60 <= time.time()]
        delete_transactions(keys_to_remove)
        time.sleep(10)


def delete_transactions(keys):
    for key in keys:
        if key in current_transactions:
            print('Deleting transactions...')
            bot.send_message(key, "Transaction timed out")
            current_transactions.pop(key, None)  # Use pop with default to avoid errors


def check_date():
    while True:
        print("Checking date...")
        is_eventful_day = event_service.check_dates()
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
        inserted_date = datetime.strptime(date_string, date_format)
        if inserted_date > inserted_date.today():
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
    bot.send_message(message.chat.id, "Insert the date of the event. Please use the format DD.MM.YYYY.")
    current_transactions[message.chat.id] = [time.time()]


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


@bot.message_handler(commands=['list'])
def all_holidays(message):
    events = event_service.get_events_by_chat_id(message.chat.id)
    reply = ""
    for event in events:
        repeating_str = "Non-repeating"
        if event[4]:
            repeating_str = "Repeating"
        reply += f'{event[1].strftime("%d.%m.%Y")} - {event[2]} - {repeating_str}\n'
    if len(reply) == 0:
        reply = "You have no saved events"
    bot.reply_to(message, reply)


@bot.message_handler(commands=['cancel'])
def cancel(message):
    current_transactions.pop(message.chat.id)
    bot.reply_to(message, "Cancelled")
    print("cancel")


@bot.message_handler(commands=['stop'])
def stop(message):
    print("stop")


# @bot.message_handler()
# def handle_replies(message):
#    if message.chat.id in current_transactions:
#        message_text = message.text
#        if message_text not in ["/start", "/help", "/addevent", "/addrepeatingevent",
#                                "/deleteevent", "/allevents", "/cancel", "/stop"]:
#            chat_id = message.chat.id
#            if chat_id in current_transactions:
#                halves = message_text.split(" - ")
#                if len(halves) == 2:
#                    valid_date = validate_date(halves[0])
#                    event_name = halves[1]
#                    if valid_date and len(event_name) <= 100:
#                        succeeded = event_service.add_data_to_db(chat_id, halves[0], event_name,
#                                                                 current_transactions[chat_id][1])
#                        if not succeeded:
#                            bot.reply_to(message, "Something wrong")
#                        else:
#                            bot.reply_to(message, "Event added")
#                        current_transactions.pop(message.chat.id)
#                    else:
#                        error_message = "Invalid input."
#                        if not valid_date:
#                            error_message = "Invalid date. Please use the format dd.MM.yyyy."
#                        if len(event_name) > 100:
#                            error_message = "Event name must be under 100 characters."
#                        bot.send_message(chat_id, error_message)
#                else:
#                    bot.send_message(chat_id, "Invalid input format. Use 'dd.MM.yyyy - event name'.")
#
#        print(message.text)
#    else:
#        bot.reply_to(message, "Please insert a valid command.")


# transaction format {
# chat_id: [date, hour, minutes, name, repeating]
# }

@bot.message_handler()
def handle_replies(message):
    command_list = ["start", "stop", "addevent", "deleteevent", "addholiday", "allevents", "help", "menu"]
    message_text = message.text
    chat_id = message.chat.id

    # If it's a command, return early
    if message_text in command_list:
        return

    if chat_id in current_transactions:
        transaction = current_transactions[chat_id]
        transaction_phase = len(transaction)

        if transaction_phase == 1:  # Adding date
            if validate_date(message_text):
                transaction.append(message_text)
                bot.send_message(chat_id, "Next, please insert the hour (24h format) when the event would happen.")
            else:
                react_to_invalid_transaction_reply(message, transaction_phase)

        elif transaction_phase == 2:  # Adding hour
            if is_valid_time_range(message_text, 0, 24):
                transaction.append(message_text)
                bot.send_message(chat_id, "Next, please insert the minute when the event would happen.")
            else:
                react_to_invalid_transaction_reply(message, transaction_phase)

        elif transaction_phase == 3:  # Adding minute
            if is_valid_time_range(message_text, 0, 60):
                transaction.append(message_text)
                bot.send_message(chat_id, "Next, please insert the event name.")
            else:
                react_to_invalid_transaction_reply(message, transaction_phase)

        elif transaction_phase == 4:  # Adding event name
            if is_valid_event_name(message_text):
                transaction.append(message_text)
                bot.send_message(chat_id, "Next, specify if the event would be repeating yearly (true/false).")
            else:
                react_to_invalid_transaction_reply(message, transaction_phase)

        elif transaction_phase == 5:  # Adding repeating flag
            repeating_flag = message_text.lower()
            if repeating_flag in ["true", "false"]:
                start, date, hour, minute, name = transaction
                repeating = repeating_flag == "true"
                saved = event_service.add_data_to_db(chat_id, date, hour, minute, name, repeating)
                if saved:
                    bot.send_message(chat_id, f"Event added - {date} {hour}:{minute} {name}, repeating: {repeating}")
                else:
                    bot.send_message(chat_id, "Event not saved. Please try again later.")
                current_transactions.pop(chat_id)
            else:
                react_to_invalid_transaction_reply(message, transaction_phase)
    else:
        bot.reply_to(message, "Please insert a valid command. To get a list of possible commands insert '/help'")


def is_valid_time_range(value, min_val, max_val):
    return value.isdigit() and min_val <= int(value) < max_val


def is_valid_event_name(name):
    return len(name) <= 100 and special_char_pattern.search(name) is None


def react_to_invalid_transaction_reply(message, phase):
    switcher = {
        1: "Invalid date. Please use the format DD.MM.YYYY.",
        2: "Invalid value inserted. Please insert numberical value from 0-23.",
        3: "Invalid value inserted. Please insert numberical value from 0-59.",
        4: "Please make sure that name is under 100 characters and that no special characters are used.",
        5: "Please insert values 'true' or 'false'"
    }
    bot.reply_to(message, switcher[phase])


bot.polling(non_stop=True)
