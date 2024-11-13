from datetime import datetime
import bot_message_text
import holidays
import logger
import transaction
from bot_utils import command_list
from transaction import chat_id_in_transaction, process_transaction, check_transaction_timeout, \
    get_timed_out_transactions
from time import sleep
import telebot
from telebot import types
import event_service
import threading
from logger import log_event
import secret_parser

# from metrics import increment_message_count, track_command_time, start_metrics_server

secret_parser.parse_secret()
event_service.update_date()
admins = [466698059, 5167789151]
bot = telebot.TeleBot(token=secret_parser.bot_token)


def handle_some_event():
    log_event("WARNING", "Some event occurred that may need attention.")
    pass


def check_date():
    while True:
        log_event("INFO", "Checking date...")
        is_eventful_day = event_service.check_dates()
        if is_eventful_day:
            events = event_service.get_events_by_datetime()

            for event in events:
                bot.send_message(event[0], f'Don\'t forget about {event[2]}!')

            event_service.update_events(events)
            event_service.update_date()
        else:
            sleep(30)


def send_transaction_timeout_message():
    deleted = get_timed_out_transactions()
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
    # increment_message_count()  # Увеличиваем счётчик сообщений
    # increment_total_users()     # Увеличиваем общее количество пользователей
    bot.send_message(message.chat.id, f"Hello {message.chat.username}!")
    log_event("INFO", f"User {message.chat.username} started the bot.")


@bot.message_handler(commands=['add'])
def add_new_occasion(message):
    # increment_message_count()  # Увеличиваем счётчик сообщений
    # increment_total_users()     # Увеличиваем общее количество пользователей
    bot.send_message(message.chat.id, "Insert the date of the event. Please use the format DD.MM.YYYY.")
    transaction.add_transaction(message.chat.id, False)


@bot.message_handler(commands=['addinline'])
def add_new_inline_event(message):  # Message format: DD.MM.YYYY - HH:mm - Event name - repeating
    # increment_message_count()  # Увеличиваем счётчик сообщений
    # increment_total_users()     # Увеличиваем общее количество пользователей
    transaction.add_transaction(message.chat.id, True)
    bot.send_message(message.chat.id, bot_message_text.transaction_messages_eng.get('inline_event_info'))


@bot.message_handler(commands=['delete'])
def delete_holiday(message):
    # increment_message_count()  # Увеличиваем счётчик сообщений
    chat_events = event_service.get_events_by_chat_id(message.chat.id)
    markup = types.InlineKeyboardMarkup()
    for event in chat_events:
        f'delete,{str(event[3])}'
        markup.add(types.InlineKeyboardButton(text=f'{str(event[1])} - {str(event[2])}',
                                              callback_data=f'delete,{message.chat.id},{str(event[3])}'))
    bot.reply_to(message, reply_markup=markup, text="Select event what you want to delete")


@bot.message_handler(commands=['special'])
def add_special_event(message):
    markup = types.InlineKeyboardMarkup()
    chat_id = message.chat.id
    markup.add(types.InlineKeyboardButton(text="Estonian national holidays", callback_data=f'est_special,{chat_id},{None}'))
    markup.add(types.InlineKeyboardButton(text="Russian national holidays", callback_data=f'rus_special,{chat_id},{None}'))
    markup.add(types.InlineKeyboardButton(text="Dynamic national holidays", callback_data=f'dynamic_special,{chat_id},{None}'))
    bot.send_message(chat_id, reply_markup=markup, text="Select what type of special event you want to add")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(callback):
    btn_type,chat_id, value = callback.data.split(',')


    markup = types.InlineKeyboardMarkup()
    cur_year = datetime.now().year
    next_year = datetime.now().year + 1
    if btn_type == 'delete':
        event_service.delete_data_from_db(callback.data)
        bot.send_message(callback.message.chat.id, "Event deleted")
    elif btn_type == 'est_special':
        est_holidays = holidays.estonian_fixed_holidays
        for holiday in est_holidays.keys():
            # dm = est_holidays[holiday]['date']
            # holiday_date = datetime.strptime(f'{dm}.{cur_year}', '%d.%m.%Y')
            # if holiday_date < datetime.now():
            #    holiday_date = datetime.strptime(f'{dm}.{next_year}', '%d.%m.%Y')
            markup.add(types.InlineKeyboardButton(text=est_holidays[holiday]['name_eng'],
                                                  callback_data=f'special_holiday,{chat_id},{holiday}'))
        bot.send_message(chat_id, reply_markup=markup, text="Select the event you want to add")

    elif btn_type == 'rus_special':
        rus_holidays = holidays.russian_fixed_holidays
        for holiday in rus_holidays.keys():
            markup.add(types.InlineKeyboardButton(text=rus_holidays[holiday]['name_eng'],
                                                  callback_data=f'special_holiday,{chat_id},{holiday}'))
        bot.send_message(chat_id, reply_markup=markup, text="Select the event you want to add")
    elif btn_type == 'dynamic_special':
        floating_holidays = holidays.get_floating_holidays(24)
        for holiday in floating_holidays.keys():
            markup.add(types.InlineKeyboardButton(text=floating_holidays[holiday]['name_eng'],
                                                  callback_data=f'special_holiday,{chat_id},{holiday}'))
        bot.send_message(chat_id, reply_markup=markup, text="Select the event you want to add")

@bot.message_handler(commands=['show'])
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
    # increment_message_count()  # Увеличиваем счётчик сообщений
    if transaction.chat_id_in_transaction(message.chat.id):
        transaction.delete_transactions([message.chat.id])
        bot.reply_to(message, "Transaction cancelled")
        log_event("INFO", f"Transaction cancelled by {message.chat.id}.")
    else:
        handle_replies(message)


def stop(message):
    try:
        log_event("CRITICAL", "Stop command received. Stopping the bot.")
        # notify_admin("Critical event: Stop command received.")
    except Exception as e:
        log_event("ERROR", f"Error is on?: {e}")  # Логирование ошибки


@bot.message_handler(commands=['restart'])
def restart_bot(message):
    if message.chat.id in admins:
        bot.reply_to(message, "Restarting bot and pulling latest updates, please wait a few minutes")
        log_event("INFO", f"Bot restart triggered by {message.chat.username}")
        event_service.reboot_system()
    else:
        bot.reply_to(message, "Unauthorized command.")


@bot.message_handler(commands=['shutdown'])
def stop_bot(message):
    if message.chat.id in admins:
        bot.reply_to(message, "Stopping bot!")
        log_event("CRITICAL", "The system is shutdown!")
        event_service.shutdown_system()
    else:
        bot.reply_to(message, "Unauthorized command.")


@bot.message_handler(commands=['sleep'])
def sleep_bot(message):
    admins = [466698059, 5167789151]

    if message.chat.id in admins:
        bot.reply_to(message, "Putting the system to sleep, please wait...")
        log_event("INFO", f"System sleep triggered by {message.chat.username}")
        event_service.sleep_system()
    else:
        bot.reply_to(message, "Unauthorized command.")


@bot.message_handler(commands=['log'])
def show_logs(message):
    if message.chat.id in admins:
        bot.reply_to(message, text=logger.get_last_log_lines())


@bot.message_handler()
def handle_replies(message):
    if message.text in command_list:
        pass

    log_event("WARNING", f"Unknown command received: {message.text}")

    if chat_id_in_transaction(message.chat.id):
        is_reply, return_message = process_transaction(message)
        if is_reply:
            bot.reply_to(message, return_message)
        else:
            bot.send_message(message.chat.id, return_message)
    else:
        bot.reply_to(message, "Please insert a valid command. To get a list of possible commands insert '/help'")


def send_start_up_notification():
    for admin in admins:
        log_event('INFO', "Bot has started")
        bot.send_message(admin, "Bot has started")


send_start_up_notification()

# start_metrics_server()
bot.polling(non_stop=True)
