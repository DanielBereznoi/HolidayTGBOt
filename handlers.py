from time import sleep
import telebot
from telebot import types
import time
from datetime import datetime, timedelta
import event_service
import threading
import re
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import secret_parser
import json

logs = 'logs'
os.makedirs(logs, exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'level': record.levelname,
            'message': record.getMessage(),
            'timestamp': datetime.utcnow().isoformat()
        }
        return json.dumps(log_entry)

handler = TimedRotatingFileHandler(
    os.path.join(logs, "bot.log"), when="midnight", interval=1, backupCount=30
)
handler.setFormatter(JsonFormatter())
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def log_event(level, message):
    logger.log(level, message)

secret_parser.parse_secret()
event_service.update_date()

bot = telebot.TeleBot(token=secret_parser.bot_token)

special_char_pattern = re.compile(r'[@_!#$%^&*()<>?/|}{~:]')
time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
date_format = "%d.%m.%Y"
current_transactions = {}

def handle_some_event():
    log_event(logging.WARNING, "Some event occurred that may need attention.")

def check_transaction_timeout():
    while True:
        logger.info("Checking transaction timeout...")
        # Directly remove timed-out transactions
        keys_to_remove = [key for key, value in current_transactions.items() if value[0] + 1 * 60 <= time.time()]
        delete_transactions(keys_to_remove)
        time.sleep(10)


def delete_transactions(keys):
    for key in keys:
        if key in current_transactions:
            logger.info("Deleting transactions...")
            bot.send_message(key, "Transaction timed out")
            current_transactions.pop(key, None)  # Use pop with default to avoid errors


def check_date():
    while True:
        logger.info("Checking date...")
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
    print("Validating date...")
    try:
        inserted_date = str_date_to_date(date_string)
        if inserted_date >= str_date_to_date(datetime.today().strftime(date_format)):
            return True
        else:
            return False
    except ValueError:
        return False

def str_date_to_date(date_str):
    return datetime.strptime(date_str, date_format)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Hello {message.chat.username}!")
    log_event(logging.INFO, f"User {message.chat.username} started the bot.")


@bot.message_handler(commands=['addevent'])
def add_new_occasion(message):
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
    if message.chat.id in current_transactions:
        current_transactions.pop(message.chat.id)
        bot.reply_to(message, "Transaction cancelled")
        logger.info(f"Transaction cancelled by {message.chat.id}.")
    else:
        handle_replies(message)


@bot.message_handler(commands=['stop'])
def stop(message):
    log_event(logging.CRITICAL, "Stop command received. Stopping the bot.")
    #notify_admin("Critical event: Stop command received.")

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
            update_transaction_timeout(chat_id)
            process_multistep_transaction(message, message_text, chat_id, transaction)
        elif transaction[1] is False:
            update_transaction_timeout(chat_id)
            process_inline_transaction(message, message_text, chat_id)
    else:
        if message_text == "cancel":
            bot.reply_to(message, "No transaction to cancel")
        bot.reply_to(message, "Please insert a valid command. To get a list of possible commands insert '/help'")


def process_inline_transaction(message, message_text, chat_id):  # Format: []
    elements = message_text.split(" - ")
    if len(elements) != 4:
        bot.reply_to(message, "Invalid inserted message. Please use format: DD.MM.YYYY - HH:mm - "
                              "Event name - Repeating(y/n)")
    else:
        is_valid_date = validate_date(elements[0])
        time_str = elements[1]
        is_valid_time = is_time_valid(time_str, elements[0])
        repeating_flag_valid = elements[3].lower() in ["yes", "y", "no", "n", "true", "false"]
        name_valid = is_valid_event_name(elements[2])
        if name_valid and is_valid_date and is_valid_time and repeating_flag_valid:
            repeating = elements[3].lower() in ["yes", "y", "true"]
            hour, minute = time_str.split(":")
            saved = event_service.add_data_to_db(chat_id, elements[0], hour, minute, elements[2], repeating)
            if saved:
                bot.send_message(chat_id, f"Event added - {elements[0]} {hour}:{minute} {elements[2]}, "
                                          f"repeating: {repeating}")
            else:
                bot.send_message(chat_id, "Event not saved. Please try again later.")

            current_transactions.pop(chat_id)
        else:
            bot.reply_to(message, "Invalid inserted message. Please use format: DD.MM.YYYY - HH:mm - "
                                  "Event name - Repeating(y/n). Make sure not to specify a passed time.")

def update_transaction_timeout(chat_id):
    transaction = current_transactions[chat_id]
    transaction[0] = time.time()
    current_transactions[chat_id] = transaction



def process_multistep_transaction(message, message_text, chat_id, transaction):
    transaction_phase = len(transaction)
    if transaction_phase == 2:  # Adding date
        print("Need to validate date")
        if validate_date(message_text):
            transaction.append(message_text)
            bot.send_message(chat_id, "Next, please insert the time (24h format) when the event would happen.")
        else:
            react_to_invalid_transaction_reply(message, transaction_phase)

    elif transaction_phase == 3:  # Adding time
        try:
            if is_time_valid(message_text, transaction[2]):
                transaction.append(message_text)
                bot.send_message(chat_id, "Next, please insert the event name.")
            else:
                raise ValueError("Invalid time range")
        except ValueError:
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
            _, _, date, time_str, name = transaction
            hour, minute = time_str.split(":")
            repeating = repeating_flag == "true"
            saved = event_service.add_data_to_db(chat_id, date, hour, minute, name, repeating)
            if saved:
                bot.send_message(chat_id, f"Event added - {date} {hour}:{minute} {name}, repeating: {repeating}")
            else:
                bot.send_message(chat_id, "Event not saved. Please try again later.")
            current_transactions.pop(chat_id)
        else:
            react_to_invalid_transaction_reply(message, transaction_phase)


def is_time_valid(time_str, date_string):
    inserted_date = datetime.strptime(date_string, date_format)
    if time_pattern.search(time_str) is not None:
        hour, minute = time_str.split(":")
        if hour.isdigit() and 0 <= int(hour) < 24 and minute.isdigit() and 0 <= int(minute) < 60 and not is_past_datetime(inserted_date, hour, minute):
            return True
    return False

def is_past_datetime(inserted_date, hour, minute):
    event_datetime = datetime.combine(inserted_date, datetime.min.time()) + timedelta(hours=int(hour), minutes=int(minute))
    if event_datetime > datetime.now():
        return False
    else:
        return True

def is_valid_event_name(name):
    return len(name) <= 100 and special_char_pattern.search(name) is None


def react_to_invalid_transaction_reply(message, phase):
    switcher = {
        2: "Invalid date. Please use the format DD.MM.YYYY.",
        3: "Invalid value inserted. Pleas use format HH:MM, where HH is in range of 0-23 and MM in range of 0-59. Make sure that you didn't insert past time.",
        4: "Please make sure that name is under 100 characters and that no special characters are used.",
        5: "Please insert values 'true' or 'false'"
    }
    bot.reply_to(message, switcher[phase])
        
bot.polling(non_stop=True)
