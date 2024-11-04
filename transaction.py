import bot_message_text
from validation import is_date_invalid, is_past_datetime, is_invalid_repeating_flag, is_time_invalid, is_invalid_event_name
import event_service

current_transactions = {}
deleted_transactions = []
import time

def chat_id_in_transaction(chat_id):
    return chat_id in current_transactions.keys()

def add_transaction(chat_id, is_inline):
    current_transactions[chat_id] = [time.time(), is_inline]
    print(current_transactions)

def process_transaction(message):
    chat_id = message.chat.id
    transaction = current_transactions.get(chat_id)
    if is_inline_transaction(chat_id):
        return process_inline_transaction(message)
    return process_multistep_transaction(message, transaction)

def is_inline_transaction(chat_id):

    print(current_transactions)
    return current_transactions[chat_id][1] == True

def process_inline_transaction(message):
    elements = message.text.split(" - ")
    update_transaction_timeout(message.chat.id)
    if len(elements) != 4:
        return True, "Invalid inserted message. Please use format: DD.MM.YYYY - HH:mm - Event name - Repeating(y/n)"

    date_str, time_str,name, repeating_flag = elements
    invalid_date = is_date_invalid(date_str)
    invalid_time = is_time_invalid(time_str)
    hour, minute = time_str.split(":")
    past_datetime = is_past_datetime(date_str, int(hour), int(minute))
    name_invalid = is_invalid_event_name(name)
    repeating_flag_invalid = is_invalid_repeating_flag(repeating_flag)
    if not invalid_date and not invalid_time and not past_datetime and not name_invalid and not repeating_flag_invalid:
        repeating = repeating_flag in ['y', 'true', 'yes']
        saved = event_service.add_data_to_db(message.chat.id, date_str, hour, minute, name, repeating)
        if saved:
            return False, f"Event added - {date_str} {hour}:{minute} {name}, repeating: {repeating}"
        return bot_message_text.transaction_messages_eng.get('event_not_saved')
    else:
        validators = [invalid_date, invalid_time, past_datetime, name_invalid, repeating_flag_invalid]
        error_messages = list(filter(lambda x: not isinstance(x, bool), validators))
        print(validators)
        error_message = "\n".join(error_messages)
        return True, error_message


def check_transaction_timeout():
    global deleted_transactions
    while True:
        # logger.info("Checking transaction timeout...")
        # Directly remove timed-out transactions
        keys_to_remove = [key for key, value in current_transactions.items() if value[0] + 1 * 60 <= time.time()]
        delete_transactions(keys_to_remove)
        deleted_transactions = keys_to_remove
        time.sleep(10)

def get_timed_out_transactions():
    if len(deleted_transactions) > 0:
        copy = deleted_transactions.copy()
        deleted_transactions.clear()
        return copy
    return False

def delete_transactions(keys):
    for key in keys:
        if key in current_transactions:
            # logger.info("Deleting transactions...")
            current_transactions.pop(key, None)  # Use pop with default to. avoid errors





def update_transaction_timeout(chat_id):
    transaction = current_transactions[chat_id]
    transaction[0] = time.time()
    current_transactions[chat_id] = transaction


def process_multistep_transaction(message, transaction):
    message_text = message.text
    chat_id = message.chat.id
    transaction_phase = len(transaction)
    update_transaction_timeout(chat_id)
    if transaction_phase == 2:  # Adding date
        date_invalid = is_date_invalid(message_text)
        if not date_invalid:
            transaction.append(message_text)
            return False, "Next, please insert the time (24h format) when the event would happen."
        else:
            return True, date_invalid

    elif transaction_phase == 3:  # Adding time
        time_invalid = is_time_invalid(message_text)
        hour, minute = message_text.split(":")
        past_datetime = is_past_datetime(transaction[2], hour, minute)
        if not time_invalid:
            if not past_datetime:
                transaction.append(message_text)
                return False, "Next, please insert the event name."
            return True, past_datetime
        return True, time_invalid

    elif transaction_phase == 4:  # Adding event name
        invalid_name = is_invalid_event_name(message_text)
        if not invalid_name:
            transaction.append(message_text)
            return False, "Next, specify if the event would be repeating yearly (true/false)."
        else:
            return True, invalid_name

    elif transaction_phase == 5:  # Adding repeating flag
        repeating_flag = message_text.lower()
        flag_invalid = is_invalid_repeating_flag(repeating_flag)
        if not flag_invalid:
            _, _, date, time_str, name = transaction
            hour, minute = time_str.split(":")
            repeating = repeating_flag.lower() in ["yes", "y", "true"]
            saved = event_service.add_data_to_db(chat_id, date, hour, minute, name, repeating)
            current_transactions.pop(chat_id)
            if saved:
                return False, f"Event added - {date} {hour}:{minute} {name}, repeating: {repeating}"
            else:
                return False, bot_message_text.transaction_messages_eng.get('event_not_saved')
        else:
            return True, flag_invalid
