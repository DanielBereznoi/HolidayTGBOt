from bot_utils import str_date_to_date, date_format, time_pattern, special_char_pattern, repeating_flag_values
from datetime import datetime, timedelta
from bot_message_text import transaction_messages_eng


def is_date_invalid(date_string):
    print("Validating date...")

    inserted_date = str_date_to_date(date_string)
    if inserted_date >= str_date_to_date(datetime.today().strftime(date_format)):
        return False
    else:
        return transaction_messages_eng.get('wrong_date_format')



def is_time_invalid(time_str):
    if time_pattern.search(time_str) is not None:
        hour, minute = time_str.split(":")
        if hour.isdigit() and 0 <= int(hour) < 24 and minute.isdigit() and 0 <= int(minute) < 60:
            return False
    return transaction_messages_eng.get("wrong_time_format")


# to delete
def is_past_datetime(date_str, hour, minute):
    inserted_date = str_date_to_date(date_str)
    event_datetime = datetime.combine(inserted_date, datetime.min.time()) + timedelta(hours=int(hour),
                                                                                 minutes=int(minute))
    print(f'{str(event_datetime)} > {datetime.now} is { event_datetime > datetime.now()}')
    if event_datetime > datetime.now():
        return False
    return transaction_messages_eng.get("past_datetime")


# to delete
def is_invalid_event_name(name):
    error_message = ''
    if len(name) > 100:
        error_message += transaction_messages_eng.get('wrong_name_length')
    if special_char_pattern.search(name) is not None:
        if error_message != '':
            error_message += '\n'
        error_message += transaction_messages_eng.get('special_characters_in_name')
    valid_name = len(name) <= 100 and special_char_pattern.search(name) is None
    if error_message == '':
        return False
    return error_message


def is_invalid_repeating_flag(flag):
    valid = flag in repeating_flag_values
    if valid:
        return False
    return transaction_messages_eng.get('wrong_repeating_flag')
