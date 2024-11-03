from datetime import datetime
import re

special_char_pattern = re.compile(r'[@_!#$%^&*()<>?/|}{~:]')
time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
date_format = "%d.%m.%Y"
command_list = ["start", "stop", "addevent", "deleteevent", "addholiday", "allevents"]
repeating_flag_values =  ["yes", "y", "no", "n", "true", "false"]

def str_date_to_date(date_str):
    return datetime.strptime(date_str, date_format)

if __name__ == '__main__':
    text = "text"
    if text:
        print(text)