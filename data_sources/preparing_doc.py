from datetime import datetime
from time import time
from pytz import timezone
import pandas as pd
import re
import sys
import os
sys.path.insert(0, os.getcwd())

from databases.mongodb import insert_document, connect_mongo, upsert_document
from dashboard_info.chats_bert import sentiment_score

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
        for line in lines[-10:]:
            try:
                time_logged = line.split('—')[0].strip()
                time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')

                username_message = line.split('—')[1:]
                username_message = '—'.join(username_message).strip()

                username, channel, message = re.search(
                    ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
                ).groups()
                # d = {
                #     'channel': channel,
                #     'username': username,
                #     'message': message,
                #     'sended_at': time_logged
                # }
                doc = {
                    'metadata': {
                        'channel': channel,
                        'username': username,
                        'message': message,
                        'cheer': recognize_cheers(line)
                    },
                    'timestamp': time_logged
                    # 'datetime': datetime.now(timezone('ROC'))
                }
                print(doc)
                return doc
            except Exception:
                pass
                # print("pass")

def parse_chat_mongo(line):
    try:
        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', line.strip()
        ).groups()
        doc = {
            'metadata': {
                'channel': channel,
                'username': username,
                'message': message,
                'cheer': recognize_cheers(line)
            },
            'timestamp': datetime.now()
            # 'datetime': datetime.now(timezone('ROC'))
        }
        insert_document(connect_mongo("chat_logs"), doc)
        return doc
    except Exception:
        print("pass")

def parse_chat_bert(line):
    try:
        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', line.strip()
        ).groups()
        doc = {
            'metadata': {
                'channel': channel,
                'username': username,
                'message': message,
                'cheer': recognize_cheers(line)
            },
            'timestamp': datetime.now()
            # 'datetime': datetime.now(timezone('ROC'))
        }
        print(doc)
        doc_sentiment = {
            "sentiment": sentiment_score(message)
        }
        print(doc_sentiment)
        upsert_document(connect_mongo("chat_logs", doc, doc_sentiment))
        return doc
    except Exception:
        print("pass")

def recognize_cheers(line):
    pattern = re.compile("([A-Za-z]*Cheer)(?:s|)([0-9]{0,5})")
                         #(?=10|100|1000|5000|10000)")
    cheers = pattern.findall(line)

    summary_dict = {}
    for cheer in cheers:
        cheer_name = cheer[0]
        amount = cheer[1]

        if cheer_name in summary_dict.keys():
            if amount != "":
                summary_dict[cheer_name] += int(amount)
            elif amount == "":
                summary_dict[cheer_name] += 1

        else:
            if amount != "":
                summary_dict[cheer_name] = int(amount)
            elif amount == "":
                summary_dict[cheer_name] = 1
    # print(summary_dict)
    return summary_dict

# line1 = ":@indigoichigo fourchCheers1 fourchCheers2 HSCheers"
# line2 = ":actiteCheer actiteLovSpin actiteShramp actiteLovSpin actiteCheer actiteCtSpin actiteCheer actiteLovSpin actiteCheer actiteShramp actiteCtSpin actiteLovSpin actiteCheer actiteShramp actiteCtSpin actiteLovSpin actiteCheer"
# line3 = ":Cheer100 Perxita esta en riders? jejejejee la primera vez que me entero lol"
# line4 = ":Cheer100 Koi si ficha a elyoya, hacen buena temporad y luchan por títulos y si hacen algun evento seguro que empiezan a formar afición presencial"
# line5 = ":Cheer100 Cheer100 tieni Nanni almeno l'idraulico non lo paghi dandogli il culo:raffaelee___!raffaelee___@raffaelee___.tmi.twitch.tv PRIVMSG #nannitwitch :CHE SCHIFO"
line6 = ":lesghede_!lesghede_@lesghede_.tmi.twitch.tv PRIVMSG #nannitwitch :ti ho scritto ovunque l'username"    
msg1 = ":sos02588520!sos02588520@sos02588520.tmi.twitch.tv PRIVMSG #lolworldchampionship :wow gunblade still exist here"

print(parse_chats("/Users/surfgreen/B/AppworksSchool/projects/backup_persona_project/testing/log/chat.log"))