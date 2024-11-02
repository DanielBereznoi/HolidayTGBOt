from datetime import datetime
import re

special_char_pattern = re.compile(r'[@_!#$%^&*()<>?/|}{~:]')
time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
date_format = "%d.%m.%Y"

def str_date_to_date(date_str):
    return datetime.strptime(date_str, date_format)