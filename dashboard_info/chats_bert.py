from transformers import AutoTokenizer, AutoModelForSequenceClassification
from time import time, sleep
from datetime import datetime
from pytz import timezone
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import torch
import whisper
import re
import sys
import os
sys.path.insert(0, os.getcwd())

from databases.mongodb import connect_mongo, insert_document
model_name = 'cardiffnlp/twitter-roberta-base-sentiment'
# model_name = "nlptown/bert-base-multilingual-uncased-sentiment"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
def sentiment_score(chat):
    tokens = tokenizer.encode(chat, return_tensors='pt')
    result = model(tokens)
    return int(torch.argmax(result.logits))# + 1

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
    df = get_chat_dataframe('/Users/surfgreen/B/AppworksSchool/projects/files/log/chat.log')
    df = df[df["unix_time_stamp"]>time()-20]

    start = time()
    df['sentiment'] = df['message'].apply(lambda x: sentiment_score(x[:512]))
    end = time()
    print(df[['message', 'sentiment']])
    print(df['sentiment'].mean())
    print(end-start)

def execute_query(latest):
    collection = connect_mongo("chats")
    filter = {
            "$and": [ 
                {"unix_time_stamp": { "$gte": latest-10 }}, 
                {"unix_time_stamp": { "$lte": time() }} 
                ] 
        }
    result = collection.find(filter)
    messages = [doc['message'] for doc in result]
    try:
        latest_doc = collection.find(filter).skip(collection.count_documents(filter) - 1)
        # print(collection.count_documents(filter) - 1)
        global lastest_record_time
        lastest_record_time = latest_doc[0]['unix_time_stamp']
        # print(lastest_record_time)
    except:
        # print("No messages")
        pass
    return messages

def predict_log():
    df_msg_log = df_msg_log._append(
        pd.DataFrame(
            execute_query(),
            index=[ datetime.now(timezone("ROC")).strftime('%H:%M:%S') ]
        )
    )

def analyze_new_msg():  
    # global score_list
    score_list = [0, 0, 0] # [count(neg), count(neu), count(pos)]
    if "lastest_record_time" in globals():
        print("lastest_record_time: ", lastest_record_time)
        message_list = execute_query(latest=lastest_record_time)
    else: 
        # print("lastest_record_time" in globals())
        message_list = execute_query(latest=time()-10)
        # print("finding..")
    for msg in message_list:
        score_list[sentiment_score(msg)] += 1 # sentiment_score: 0(negative), 1(neutral), 2(positive)
    return score_list