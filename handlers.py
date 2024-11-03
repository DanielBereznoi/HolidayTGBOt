import bot_message_text
import transaction
from bot_utils import command_list
from transaction import chat_id_in_transaction, process_transaction, check_transaction_timeout, \
    get_timed_out_transactions
# from logger import log_event, handle_some_event
from time import sleep
import telebot
from telebot import types
from datetime import datetime, timezone
import event_service
import threading
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import secret_parser
import subprocess
import json
from metrics import increment_message_count, add_unique_user, track_command_time, start_metrics_server

secret_parser.parse_secret()
event_service.update_date()

bot = telebot.TeleBot(token=secret_parser.bot_token)

def handle_some_event():
    log_event(logging.WARNING, "Some event occurred that may need attention.")


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


def send_transaction_timeout_message():
    deleted = get_timed_out_transactions
    if isinstance(deleted, list):
        for chat_id in deleted:
            bot.send_message(chat_id, bot_message_text.transaction_messages_eng.get('transaction_timed_out'))
    sleep(5)

transaction_check_thread = threading.Thread(target=check_transaction_timeout)
transaction_timeout_message_thread = threading.Thread(target=send_transaction_timeout_message)
date_check_thread = threading.Thread(target=check_date)

transaction_check_thread.start()
date_check_thread.start()


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Hello {message.chat.username}!")
    log_event(logging.INFO, f"User {message.chat.username} started the bot.")


@bot.message_handler(commands=['addevent'])
def add_new_occasion(message):
    bot.send_message(message.chat.id, "Insert the date of the event. Please use the format DD.MM.YYYY.")
    transaction.add_transaction(message.chat.id, False)


@bot.message_handler(commands=['addeventinline'])
def add_new_inline_event(message):  # Message format: DD.MM.YYYY - HH:mm - Event name - repeating
    transaction.add_transaction(message.chat.id, True)
    bot.send_message(message.chat.id, bot_message_text.transaction_messages_eng.get('inline_event_info'))


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
    if transaction.chat_id_in_transaction(message.chat.id):
        transaction.delete_transactions([message.chat.id])
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
    if  message.text in command_list:
        pass

    if chat_id_in_transaction(message.chat.id):
        is_reply, return_message = process_transaction(message)
        if is_reply:
            bot.reply_to(message, return_message)
        else:
            bot.send_message(message.chat.id, return_message)
    else:
         bot.reply_to(message, "Please insert a valid command. To get a list of possible commands insert '/help'")


@bot.message_handler(commands=['restart'])
def restart_bot(message):
    admin_id = 466698059
    
    if message.chat.id == admin_id:
        bot.reply_to(message, "Restarting bot and pulling latest updates...")
        log_event(logging.INFO, f"Bot restart triggered by {message.chat.username}")
        # os.exit(0)  # Terminate the bot, systemd or supervisor will restart it
    else:
        bot.reply_to(message, "Unauthorized command.")

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    quit()

start_metrics_server()
bot.polling(non_stop=True)
