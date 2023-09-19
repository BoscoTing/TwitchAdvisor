from datetime import datetime
from time import time
from pytz import timezone
import pandas as pd
import re
import sys
sys.path.insert(0, "/Users/surfgreen/B/AppworksSchool/projects/personal_project")

from databases.mongodb import insert_document, connect_mongo


def get_chat_dataframe(file):
    data = []

    with open(file, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
        # print(lines)
        for line in lines:
            try:
                time_logged = line.split('—')[0].strip()
                time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')

                username_message = line.split('—')[1:]
                username_message = '—'.join(username_message).strip()

                username, channel, message = re.search(
                    ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
                ).groups()
                d = {
                    'dt': time_logged,
                    'channel': channel,
                    'username': username,
                    'message': message
                }
                # print(d)
                data.append(d)
            except Exception:
                pass
            
    return pd.DataFrame().from_records(data) 

def parse_chats(file):
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
        # print(lines)
        for line in lines:
            try:
                time_logged = line.split('—')[0].strip()
                time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')

                username_message = line.split('—')[1:]
                username_message = '—'.join(username_message).strip()

                username, channel, message = re.search(
                    ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
                ).groups()
                d = {
                    'channel': channel,
                    'username': username,
                    'message': message,
                    'sended_at': time_logged
                }
                print(d)
            except Exception:
                pass
                # print("pass")

def parse_chat_mongo(line):
    try:
        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', line.strip()
        ).groups()
        doc = {
            'channel': channel,
            'username': username,
            'message': message,
            'unix_time_stamp': time(),
            'datetime': datetime.now(timezone('ROC'))
        }
        insert_document(connect_mongo("chats"), doc)
        return doc
    except Exception:
        print("pass")

def parse_chat_bert(line):
    try:
        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', line.strip()
        ).groups()
        doc = {
            'channel': channel,
            'username': username,
            'message': message,
            'unix_time_stamp': time(),
            'datetime': datetime.now(timezone('ROC'))
        }
        return doc
    except Exception:
        print("pass")

def recognize_cheers(line):
    line1 = ":@indigoichigo fourchCheers1 fourchCheers2 HSCheers"
    line2 = ":actiteCheer actiteLovSpin actiteShramp actiteLovSpin actiteCheer actiteCtSpin actiteCheer actiteLovSpin actiteCheer actiteShramp actiteCtSpin actiteLovSpin actiteCheer actiteShramp actiteCtSpin actiteLovSpin actiteCheer"
    line3 = ":Cheer100 Perxita esta en riders? jejejejee la primera vez que me entero lol"
    line4 = ":Cheer100 Koi si ficha a elyoya, hacen buena temporad y luchan por títulos y si hacen algun evento seguro que empiezan a formar afición presencial"
    line5 = ":Cheer100 Cheer100 tieni Nanni almeno l'idraulico non lo paghi dandogli il culo:raffaelee___!raffaelee___@raffaelee___.tmi.twitch.tv PRIVMSG #nannitwitch :CHE SCHIFO"
    line6 = ":lesghede_!lesghede_@lesghede_.tmi.twitch.tv PRIVMSG #nannitwitch :ti ho scritto ovunque l'username"
    pattern = re.compile("([A-Za-z]*Cheer)(?:s|)([0-9]{0,5})")
                         #(?=10|100|1000|5000|10000)")
    cheers = pattern.findall(line1)
    rev = 0
    for cheer in cheers:
        if cheer[1] != "":
            rev += int(cheer[1])
    print(cheers)
    print(rev)
recognize_cheers("heheboy")
