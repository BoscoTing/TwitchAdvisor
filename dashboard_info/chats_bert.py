from transformers import AutoTokenizer, AutoModelForSequenceClassification
from time import time
from datetime import datetime
from pytz import timezone
import pandas as pd
import numpy as np
import torch
import whisper
import re
import sys
sys.path.insert(0, "/Users/surfgreen/B/AppworksSchool/projects/personal_project")

from databases.mongodb import connect_mongo, insert_document
from data_sources.chat_logs import get_chats
# model_name = 'cardiffnlp/twitter-roberta-base-sentiment'
model_name = "nlptown/bert-base-multilingual-uncased-sentiment"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
def sentiment_score(chat):
    tokens = tokenizer.encode(chat, return_tensors='pt')
    result = model(tokens)
    return int(torch.argmax(result.logits)) + 1

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
                    'channel': channel,
                    'username': username,
                    'message': message,
                    'unix_time_stamp': time_logged.timestamp(),
                    'datetime': time_logged
                }
                data.append(d)
            except Exception:
                pass
    return pd.DataFrame().from_records(data)

def predict_dataframe():
    df = get_chat_dataframe('/Users/surfgreen/B/AppworksSchool/projects/personal_project/testing/log/chat.log')
    df = df[df["unix_time_stamp"]>time()-20]

    start = time()
    df['sentiment'] = df['message'].apply(lambda x: sentiment_score(x[:512]))
    end = time()
    print(df[['message', 'sentiment']])
    print(df['sentiment'].mean())
    print(end-start)

def predict_log():
    chat_log = get_chats()