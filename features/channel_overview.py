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

    def get_livestream_schedule(self):
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

        for entry in livestream_schedule:
            # Convert 'startedAt' to datetime object
            entry['startedAtDatetime'] = datetime.strptime(entry['startedAt'], "%Y-%m-%dT%H:%M:%S%z")

            # Extract week of the month and day of the week
            week_of_month = (entry['startedAtDatetime'].day - 1) // 7 + 1
            day_of_week = entry['startedAtDatetime'].strftime("%A")

            entry['weekOfMonth'] = week_of_month
            entry['dayOfWeek'] = day_of_week

            processed_data.append(entry)

        return processed_data
    
# print(Overview().get_livestream_schedule())