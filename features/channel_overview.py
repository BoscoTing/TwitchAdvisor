from datetime import datetime, timedelta
from time import time, sleep
from copy import deepcopy
import logging
import re
import os
import sys
sys.path.insert(0, os.getcwd())
from copy import deepcopy

from managers.mongodb_manager import MongoDBManager
from managers.ircbot_manager import TwitchChatListener
from managers.twitch_api_manager import TwitchDeveloper
from features.chatroom_sentiment import ChatroomSentiment

class Overview:
    def __init__(self):
        self.db = MongoDBManager()

    def get_livestream_schedule(self, week, year):
        print(f'channel_overview.py: get_livestream_schedule({week}, {year})')
        task_records = self.db.connect_collection("chatStats")
        query = [
            {
                '$group': {
                    '_id': {
                        'channel': '$channel', 
                        'startedAt': '$startedAt'
                    }, 
                    'avgSentimentScore': {
                        '$avg': '$sentimentScore'
                    }, 
                    'maxMessageCount': {
                        '$max': '$messageCount'
                    }, 
                    'avgMessageCount': {
                        '$avg': '$messageCount'
                    }
                }
            }, {
                '$project': {
                    '_id': False, 
                    'channel': '$_id.channel', 
                    'startedAt': '$_id.startedAt', 
                    'avgSentimentScore': 1, 
                    'maxMessageCount': 1, 
                    'avgMessageCount': 1
                }
            }
        ]
        
        result = task_records.aggregate(query)
        livestream_schedule = [row for row in result]

        processed_data = []
        for doc in livestream_schedule:

            started_at_date = datetime.fromisoformat(doc['startedAt'])
            doc['startedAtUnixTimestamp'] = datetime.fromisoformat(doc['startedAt']).timestamp()

            doc['year'] = started_at_date.year
            doc['month'] = started_at_date.month
            doc['dayOfMonth'] = started_at_date.day
            doc['weekDay'] = started_at_date.weekday()
            doc['weekOfMonth'] = (doc['dayOfMonth'] - 1) // 7 + 1
            doc['weekOfYear'] = started_at_date.isocalendar().week

            weekday_names = ['Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.']
            doc['weekDayName'] = weekday_names[doc['weekDay']]

            if week == doc['weekOfYear'] and year == doc['year']:
                processed_data.append(doc)

        return processed_data