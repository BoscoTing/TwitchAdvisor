from datetime import datetime
import os
import sys
sys.path.insert(0, os.getcwd())

from managers.mongodb_manager import MongoDBManager

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
                    },
                    'avgViewerCount': {
                        '$avg': '$averageViewerCount'
                    },
                    'maxViewerCount': {
                        '$max': '$averageViewerCount'
                    },
                    'totCheerCount': {
                        '$sum': {'$sum': "$cheers"}
                    },
                }
            }, {
                '$project': {
                    '_id': False, 
                    'channel': '$_id.channel', 
                    'startedAt': '$_id.startedAt', 
                    'avgSentimentScore': 1, 
                    'maxMessageCount': 1, 
                    'avgMessageCount': 1,
                    'avgViewerCount': 1,
                    'maxViewerCount': 1,
                    'totCheerCount': 1
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
    
    def get_schedule_week_range(self):
        task_records = self.db.connect_collection("chatStats")
        query = [
            {
                '$group': {
                    '_id': {
                        'channel': '$channel', 
                        'startedAt': '$startedAt'
                    }
                }
            }, {
                '$project': {
                    '_id': False, 
                    'channel': '$_id.channel', 
                    'startedAt': '$_id.startedAt', 
                }
            }
        ]
        
        result = task_records.aggregate(query)
        livestream_schedule = [row for row in result]
        sorted_startedAt  = sorted([datetime.fromisoformat(doc['startedAt']) for doc in livestream_schedule])
        min = sorted_startedAt[0]
        max = sorted_startedAt[-1]
        print(f"schedule_range: {min} to {max}")
        # max = sorted_startedAt[-1].timestamp()
        schedule_range_list = [
            f"{min.year}-W{min.isocalendar().week}",
            f"{max.year}-W{max.isocalendar().week}"
            ]

        return schedule_range_list