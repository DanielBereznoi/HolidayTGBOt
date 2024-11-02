from bot_utils import str_date_to_date, date_format, time_pattern, special_char_pattern
from datetime import datetime, timedelta


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

def is_time_valid(time_str, date_string):
    inserted_date = datetime.strptime(date_string, date_format)
    if time_pattern.search(time_str) is not None:
        hour, minute = time_str.split(":")
        if hour.isdigit() and 0 <= int(hour) < 24 and minute.isdigit() and 0 <= int(minute) < 60 and not is_past_datetime(inserted_date, hour, minute):
            return True
    return False

# to delete
def is_past_datetime(inserted_date, hour, minute):
    event_datetime = datetime.combine(inserted_date, datetime.min.time()) + timedelta(hours=int(hour), minutes=int(minute))
    if event_datetime > datetime.now():
        return False
    else:
        return True

# to delete
def is_valid_event_name(name):
    return len(name) <= 100 and special_char_pattern.search(name) is None

