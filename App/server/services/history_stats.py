from datetime import datetime
import os
import sys
sys.path.insert(0, os.getcwd())

from ..models.mongodb_manager import MongoDBManager
from ..utils.logger import send_log, dev_logger

def main():
    print('this is python script of ViewersReactionAnalyser')

class ViewersReactionAnalyser():

    def __init__(self, channel):
        self.channel = channel
        self.db = MongoDBManager()
        self.col = "chat_logs"
        self.lastest_record = 0 

    def sort_isodate_schedule(self, schedule_list):
        def isodate_key(isodate):
            return datetime.fromisoformat(isodate)
        sorted_schedule_list = sorted(schedule_list, key=isodate_key)
        return sorted_schedule_list

    def query_historical_stats(self, started_at): # the "started_at" here is the argument requested from flask app, which is different from "self.started_at"

        collection = self.db.connect_collection("chatStats")

        """
        started_at can be None.
        """
        if started_at: # if user chose the schedule date
            dev_logger.debug(("started_at", started_at))
            result = [row for row in collection.aggregate([
                {
                    "$match": {
                        "startedAt": started_at,
                        "channel": self.channel
                    }
                },
                {
                    "$sort": {
                        "timestamp": -1
                    }
                }
                ])]
            dev_logger.debug(("result[-1]", result[-1]))

            return result

        else: # When user first get into historical page
            try: 
                dev_logger.debug("viewers_reaction.py - query_historical_stats: trying to get schedule")

                schedule = self.get_historical_schedule()

                most_current = schedule[-1]
                dev_logger.debug("most_current", most_current)
                dev_logger.debug("self.channel", self.channel)

                result = [row for row in collection.aggregate([
                    {
                        "$match": {
                            "startedAt": most_current,
                            "channel": self.channel
                        }
                    },
                    {
                        "$sort": {
                            "timestamp": -1
                        }
                    }
                    ])]
                
                if result!=False and result!=[]:
                    print("viewers_reaction.py - query_historical_stats - result[-1]", result[-1])
                    return result

            except Exception as e:
                send_log(e)
                dev_logger.error(e)
                return False

    def get_historical_schedule(self):

        """
        1. Only show the schedule query from taskRecords whose taskName is 'insert_stats'
        2. taskName='insert_stats' means that the channel's stats data have been organized already at the time 'startedAt'.
        """
        collection = self.db.connect_collection("taskRecords")
        query = [
            {
                "$match": {
                    "channel": {"$eq": self.channel},
                    "taskName": "insert_stats" 
                }
            },
            {
                "$project": {
                    "startedAt": 1,
                    "_id": 1
                }
            },
            {
                "$group": {
                    "_id": "null", 
                    "schedule": {"$addToSet": "$startedAt"}
                }
            }
        ]

        schedule = [row['schedule'] for row in collection.aggregate(query)][0]
        sorted_schedule = self.sort_isodate_schedule(schedule)
        print("viewers_reaction.py - query_historical_stats - sorted_schedule:", sorted_schedule)
        print("viewers_reaction: historical sorted_schedule", sorted_schedule)
        return sorted_schedule


class Overview():

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
        schedule_range_list = [
            f"{min.year}-W{min.isocalendar().week}",
            f"{max.year}-W{max.isocalendar().week}"
            ]

        return schedule_range_list


if __name__ == "__main__":
    main()