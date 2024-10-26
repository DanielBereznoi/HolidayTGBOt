import json
import platform

bot_token = None
db_username = None
db_password = None
db_name = None

if platform.system() == 'Windows':
    path_to_secret = "../secret.json"
else:
    path_to_secret = "/home/dabere/projects/betterfriend/env/secret.json"

def parse_secret():
    global bot_token, db_username, db_password, db_name
    with open(path_to_secret) as secret_file:
        secret = json.load(secret_file)

    bot_token = secret["bot_token"]
    db_username = secret["db_username"]
    db_password = secret["db_password"]
    db_name = secret["db_name"]



if __name__ == '__main__':
    parse_secret()
    print(bot_token)

