from datetime import datetime
import re

special_char_pattern = re.compile(r'[@_!#$%^&*()<>?/|}{~:]')
time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
date_format = "%d.%m.%Y"
datetime_strformat = "%Y-%m-%d %H:%M:%S"
command_list = ["start", "stop", "addevent", "deleteevent", "addholiday", "allevents"]
repeating_flag_values =  ["yes", "y", "no", "n", "true", "false", "t", "f"]

commands = {
    'add': {'command': '/add', 'description': "Add a new event in multiple steps"},
    'addinline': {'command': '/addinline', 'description': "Add a new event in one line"},
    'delete': {'command': '/delete', 'description': "Delete your saved event"},
    'special': {'command': '/special', 'description': "Add a holiday"},
    'show': {'command': '/show', 'description': "Show all your saved events"},
    'cancel': {'command': '/cancel', 'description': "Cancel event addition process"},
    'help': {'command': '/help', 'description': "Show all commands and their description"}
}

admin_commands = {
    'restart': {'command': '/restart', 'description': "Restart the system"},
    'shutdown': {'command': '/shutdown', 'description': "Shut down the system"},
    'sleep': {'command': '/sleep', 'description': "Enter system into sleep mode"},
    'log': {'command': '/log', 'description': "Show latest logs"}
}

def str_date_to_date(date_str):
    return datetime.strptime(date_str, date_format)

if __name__ == '__main__':
    text = "text"
    if text:
        print(text)
