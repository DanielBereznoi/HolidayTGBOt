from contextlib import suppress
from idlelib.configdialog import tracers
from itertools import chain

from time import sleep
from collections import defaultdict
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
        keys_to_remove = [key for key, value in current_transactions.items() if value[0] + 1 * 60 <= time.time()]
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


@bot.message_handler(commands=['addevent'])
def add_new_occasion(message):
    print(message)
    print(message.chat.id)
    bot.send_message(message.chat.id, "Insert the date of the event. Please use the format DD.MM.YYYY.")
    current_transactions[message.chat.id] = [time.time(), True]


@bot.message_handler(commands=['addeventinline'])
def add_new_inline_event(message):  # Message format: DD.MM.YYYY - HH:mm - Event name - repeating
    # list = "11.12.2024 - 12:20 - vaike valge vene Pede posi - Y".split(" - ")
    current_transactions[message.chat.id] = [time.time(), False]
    bot.send_message(message.chat.id, "Please insert the event description in one line. \n"
                                      "Please use format: DD.MM.YYYY - HH:mm - Event name - Repeating(y/n).\n"
                                      "Repeating means that event would repeat yearly.")


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
        if transaction[1] is True:  # Is multi-step transaction
            proccess_multistep_transaction(message, message_text, chat_id, transaction)
        elif transaction[1] is False:
            process_inline_transaction(message, message_text, chat_id)
    else:
        bot.reply_to(message, "Please insert a valid command. To get a list of possible commands insert '/help'")


def process_inline_transaction(message, message_text, chat_id):  # Format: []
    elements = message_text.split(" - ")
    if len(elements) != 4:
        bot.reply_to(message, "Invalid inserted message. Please use format: DD.MM.YYYY - HH:mm - "
                              "Event name - Repeating(y/n)")
    is_valid_date = validate_date(elements[0])
    hour = elements[1].split(":")[0]
    is_hour_valid = is_valid_time_range(hour, 0, 24)
    minute = elements[1].split(":")[1]
    is_minute_valid = is_valid_time_range(hour, 0, 60)
    repeating_flag_valid = elements[3].lower() in ["yes", "y", "no", "n", "true", "false"]
    name_valid = is_valid_event_name(elements[2])
    if name_valid and is_valid_date and is_hour_valid and is_minute_valid:
        repeating = elements[3].lower() in ["yes", "y", "true"]
        saved = event_service.add_data_to_db(chat_id, elements[0], hour, minute, elements[2], repeating)
        if saved:
            bot.send_message(chat_id, f"Event added - {elements[0]} {hour}:{minute} {elements[2]}, "
                                      f"repeating: {repeating}")
        else:
            bot.send_message(chat_id, "Event not saved. Please try again later.")

        current_transactions.pop(chat_id)
    else:
        bot.reply_to(message, "Invalid inserted message. Please use format: DD.MM.YYYY - HH:mm - "
                              "Event name - Repeating(y/n)")


def proccess_multistep_transaction(message, message_text, chat_id, transaction):
    transaction = current_transactions[chat_id]
    transaction_phase = len(transaction)
    if transaction_phase == 2:  # Adding date
        if validate_date(message_text):
            transaction.append(message_text)
            bot.send_message(chat_id, "Next, please insert the time (24h format) when the event would happen.")
        else:
            react_to_invalid_transaction_reply(message, transaction_phase)

    elif transaction_phase == 3:  # Adding time
        hour, min = message_text.split(":")
        if is_valid_time_range(hour, 0, 24) and is_valid_time_range(min, 0, 60):
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
            _, _, date, time, name = transaction
            hour, minute = time.split(":")
            repeating = repeating_flag == "true"
            saved = event_service.add_data_to_db(chat_id, date, hour, minute, name, repeating)
            if saved:
                bot.send_message(chat_id, f"Event added - {date} {hour}:{minute} {name}, repeating: {repeating}")
            else:
                bot.send_message(chat_id, "Event not saved. Please try again later.")
            current_transactions.pop(chat_id)
        else:
            react_to_invalid_transaction_reply(message, transaction_phase)


def is_valid_time_range(value, min_val, max_val):
    return value.isdigit() and min_val <= int(value) < max_val


def is_valid_event_name(name):
    return len(name) <= 100 and special_char_pattern.search(name) is None


def react_to_invalid_transaction_reply(message, phase):
    switcher = {
        2: "Invalid date. Please use the format DD.MM.YYYY.",
        3: "Invalid value inserted. Pleas use format HH:MM, where HH is in range of 0-23 and MM in range of 0-59.",
        4: "Please make sure that name is under 100 characters and that no special characters are used.",
        5: "Please insert values 'true' or 'false'"
    }
    bot.reply_to(message, switcher[phase])


bot.polling(non_stop=True)
