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

def main():
    print('this is python script of ViewersReactionAnalyser')

class ViewersReactionAnalyser():
    def __init__(self, channel):
        self.channel = channel
        self.listener = TwitchChatListener(channel)
        self.db = MongoDBManager()
        self.col = "chat_logs"
        self.api = TwitchDeveloper()
        self.lastest_record = 0 

    def append_start_time(self):
        collection = self.db.connect_collection("schedules")
        doc = {
            "channel": self.channel,
            "started_at": deepcopy(self.api.detect_living_channel(self.channel)['started_at'])
            }
        collection.insert_one(document=doc)

    def recognize_cheers(self, line):
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
        return summary_dict
    
    def parse_chat_logs(self, line): # define the schema of inserted document 
        print("line: ", line)

        """ 
        in the log file, the first section is datetime string format, 
        the second section is Bson time format. Both are in timezone of ROC.
        """
        time_logged = line.split('—')[0].strip()
        time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S') # turn from string to datetime format.
        print("time_logged", time_logged)

        started_at = line.split('—')[1].strip()
        print("started_at", started_at)

        username_message = line.split('—')[2:]
        username_message = '—'.join(username_message).strip()
        print("username_message", username_message)

        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
        ).groups()
        doc = {
            'message': message,
            'cheer': self.recognize_cheers(line),
            'userName': username,
            'insertOrder': self.lastest_record,
            'timestamp': time_logged, # datetime format in timezone of ROC
            'selectionInfo': {
                'channel': channel,
                'startedAt': started_at
                }        
            }
        return doc

    def insert_chat_logs(self, file): # streaming
        collection = self.db.connect_collection("chatLogs")
        latest_doc = [row for row in collection.aggregate([ 
                    {
                        "$match":{
                            "selectionInfo.channel": {"$eq": self.channel}
                            },
                    },
                    { 
                        "$project": {
                            "message": 1,
                            'insertOrder': 1,
                            'timestamp': 1,
                            "selectionInfo": 1
                        }
                    },
                    {
                        "$sort": {
                            "insertOrder": -1
                        },
                    },
                    {
                        "$limit": 1
                    }
                    ])]
        print("latest_doc:", latest_doc)
        if latest_doc == []:
            latest_row = 0
        else: 
            latest_row = latest_doc[0]['insertOrder']
        print(latest_row)
        self.lastest_record = deepcopy(latest_row)

        documents = []
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            new_row = 0
            viewer_count = self.api.detect_living_channel(self.channel)['viewer_count'] # Since viewerCount in Twitch API is updating in a slow pace, I request it for each iteration in while loop.
            for line in lines[latest_row+1:]:
                
                print("line: ", line)
                try:
                    print("parse_line", line)
                    doc = self.parse_chat_logs(line)

                    print("parsed_doc")
                    doc['viewerCount'] = viewer_count

                    if new_row >= 1: # skip the log which has already been inserted last time.
                        documents.append(doc)
                        print("appended chat logs")

                    new_row += 1

                except Exception as e:
                    print(e)
                    # logging.error("insert_chat_logs:", e)
                    pass
                self.lastest_record += 1
            # print(documents)
            if documents:
                self.db.insertmany_into_collection(documents, collection_name="chatLogs")
                print('inserted')
                # logging.debug('inserted.')

    def query_chat_logs(self): # streaming # need to add new filter to find the doc of selected channel.
        # last_record = self.last_record
        collection = self.db.connect_collection(self.col)
        query = {
            "$and": [ 
                {"timestamp": { "$gt": time()-10 }}, 
                {"timestamp": { "$lte": time() }} 
            ] 
        }
        messages_count = collection.count_documents(query)
        chatters_count = collection.distinct(query=query, key="username")

        query = {
            "$sum": [
                {"timestamp": { "$gt": time()-10 }}, 
                {"timestamp": { "$lte": time() }} 
            ]
        }
        cheers_count = collection.aggregate(
            [ 
                { '$match': { "metadata.cheer": "null" } }, 
                { '$group': { "_id": "null", "totalCheer": { "$sum": 0 } } }
            ] 
        )
        self.stats = {
                    "messages": messages_count, 
                    "chatters": chatters_count,
                    "cheers": [result for result in cheers_count],
                }
        return self.stats
    
    def historical_stats(self, started_at): # historical
        query = [
                    {
                        "$match":{
                            "selectionInfo.startedAt": { "$eq": started_at },
                            "selectionInfo.channel": {"$eq": self.channel}
                            }
                    },
                    {
                        "$project": {
                            "timestamp": 1,
                            "selectionInfo": 1,
                            'message': 1,
                            'cheer': 1,
                            'userName': 1,
                            'viewerCount': 1,
                            }
                    },
                    {
                        "$group": {
                            "_id": {
                                "$toDate": {
                                "$subtract": [
                                    { "$toLong": "$timestamp" },
                                    { "$mod": [{ "$toLong": "$timestamp" }, 5000] }
                                    ]
                                }
                            },
                            "messages": { "$addToSet": "$message" },
                            "messageCount": { "$sum": 1 },
                            "userNames": { "$addToSet": "$userName" },
                            "cheers": {
                                "$addToSet": {
                                    "$cond": {
                                        "if": {
                                            "$ne": ["$cheer", {}]
                                            },
                                        "then": "$cheer",
                                        "else": "$skip"
                                        }
                                    }
                                },
                            "averageViewerCount": { "$avg": "$viewerCount"},
                            "channel": {"$first": "$selectionInfo.channel"},
                            "startedAt": {"$first": "$selectionInfo.startedAt"}
                        }
                    },
                    {
                        "$project": {
                            "timestamp": 1,
                            "startedAt": 1,
                            "channel": 1,
                            "cheers": 1,
                            "messages": 1,
                            "messageCount": 1,
                            "chatterCount": {
                                "$size": "$userNames"
                            },
                            "averageViewerCount": 1 
                        }
                    },
                    {
                        "$sort": { "_id": 1 }
                    }
                ]
        collection = self.db.connect_collection("chatLogs")
        stats = [row for row in collection.aggregate(query)]
        return stats

    def sort_isodate_schedule(self, schedule_list):
        def isodate_key(isodate):
            from datetime import datetime
            return datetime.fromisoformat(isodate)
        sorted_schedule_list = sorted(schedule_list, key=isodate_key)
        return sorted_schedule_list

    def avg_sentiment_weighted_by_index(self, score_list):
        weighted_scores = []
        for i in range(len(score_list)):
            weighted_scores.append(score_list[i] * i)
            result = sum(weighted_scores) / sum(score_list)
        return result

    def insert_historical_stats(self): # insert all historical stats data right after the live streaming ends using insertmany.

        """
        This function is called repeatedly when the channel is off-line.

        Query the record of completed task to check if insert_historical_stats has done already or not.
        if the latest task record is behind of the latest startedAt in chatLogs, execute insert_historical_stats.
        """
        task_records_collction = self.db.connect_collection("taskRecords") 
        query = [  
            {
                "$match": {"channel": self.channel} # check the task records of selected channel.
            },
            {
                "$group": {
                    "_id": "null",
                    "taskRecord": {"$addToSet": "$startedAt"}
                    }
            },
            {
                "$project": {
                    "taskRecord": 1,
                    "_id": 0
                }
            }]
        try:
            result = [row for row in task_records_collction.aggregate(query)][0]
            task_records = result['taskRecord']
        except: 
            # result = [row for row in task_records_collction.aggregate(query)]
            task_records = []
        print("completed insert_stats tasks: ", task_records)

        """
        get the latest startedAt record from chatLog collection.
        """
        historical_schedule_list = self.get_historical_schedule()
        print("historical_schedule: ", historical_schedule_list)

        started_at = self.sort_isodate_schedule(historical_schedule_list)[-1]
        print("viewers_reaction: insert_historical_stats", started_at)

        """
        Countinue if insert_stats haven't been executed after channel turned off-line.
        """
        if started_at in task_records:
            print(f"{self.channel}'s live stream started at {started_at} has been calculated and inserted already.")
            logging.info(f"{self.channel}'s live stream started at {started_at} has been calculated and inserted already.")
            
        else: # when latest record in chatLogs is not in startedAt records in taskRecord
            print("viewers_reaction: querying historical_stats...")
            stats = deepcopy(self.historical_stats(started_at)) # self.historical_stats() will need self.started_at
            organized_documents = []
            sentiment_analyser = ChatroomSentiment()
            
            print("viewers_reaction: calculating sentiment_score...")
            for doc in stats:
                # doc = {}
                doc['timestamp'] = doc['_id']
                doc['sentiment'] = sentiment_analyser.historical_stats_sentiment(doc['messages'])
                doc['sentimentScore'] = self.avg_sentiment_weighted_by_index(doc['sentiment'])
                organized_documents.append(doc)
            try:
                print("viewers_reaction: trying to insertmany into chatStats...")
                self.db.insertmany_into_collection(organized_documents, collection_name='chatStats')
                print("successfully insert historical stats.")
            except Exception as e:
                print(e)
                sleep(5)

            """
            record the insert_stats task in taskRecords collection.
            """
            try:
                print("viewers_reaction: trying to insert task record into taskRecords...")
                task_record_document = {
                    "channel": self.channel,
                    "startedAt": started_at, # bson format in +8 timezone
                    "taskName": "insert_stats",
                    "completeTime": datetime.utcnow() # utc time for timeseries collection index.
                }
                self.db.insertone_into_collection(task_record_document, collection_name='taskRecords')
                print("successfully insert task records.")
            except Exception as e:
                print(e)
                sleep(5)    

    def query_historical_stats(self, started_at): # the "started_at" here is the argument requested from flask app, which is different from "self.started_at"

        collection = self.db.connect_collection("chatStats")

        """
        started_at can be None.
        """
        if started_at: # if user chose the schedule date
            print("viewers_reaction.py: query_historical_stats", started_at)
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
            return result

        else: # When user first get into historical page
            try: 
                print("viewers_reaction: try get_historical_schedule")
                schedule = self.get_historical_schedule()
                for i in range(len(schedule)): # find startedAt which has data in chatStats
                    most_current = schedule[i]
                    print("viewers_reaction.py: query_historical_stats most_current", most_current)
                    print("viewers_reaction.py: query_historical_stats self.channel", self.channel)

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
                        return result

            except Exception as e:
                print(e)
                return False

    
    def get_historical_schedule(self):
        """
        Only show the schedule query from chatStats, which have been organized already.
        """
        collection = self.db.connect_collection("chatStats")
        query = [
            {
                "$match": {
                    "channel": {"$eq": self.channel}
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
        print("viewers_reaction: historical schedule", schedule)
        # logging.debug("viewers_reaction: historical schedule", schedule)
        return schedule

    def parse_temp_chat_logs(self, line): # define the schema of inserted document 
        logging.debug("line: ", line)

        time_logged = line.split('—')[0].strip()
        time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')
        logging.debug("time_logged", time_logged)

        started_at = line.split('—')[1].strip()
        logging.debug("started_at", started_at)

        username_message = line.split('—')[2:]
        username_message = '—'.join(username_message).strip()
        logging.debug("username_message", username_message)

        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
        ).groups()
        doc = {
            'message': message,
            'cheer': self.recognize_cheers(line),
            'userName': username,
            'insertOrder': self.lastest_record,
            'timestamp': time_logged,
            'selectionInfo': {
                'channel': channel,
                'startedAt': started_at
                }        
            }
        # logging.warning("parsed_doc", doc)
        return doc

    def insert_temp_chat_logs(self, file): # streaming
        collection = self.db.connect_collection("tempChatLogs")
        latest_doc = [row for row in collection.aggregate([ 
                    {
                        "$match":{
                            "selectionInfo.channel": {"$eq": self.channel}
                            },
                    },
                    { 
                        "$project": {
                            "message": 1,
                            'insertOrder': 1,
                            'timestamp': 1,
                            "selectionInfo": 1
                        }
                    },
                    {
                        "$sort": {
                            "insertOrder": -1
                        },
                    },
                    {
                        "$limit": 1
                    }
                    ])]
        print("latest_doc:", latest_doc)
        if latest_doc == []:
            latest_row = 0
        else: 
            latest_row = latest_doc[0]['insertOrder']
        self.lastest_record = deepcopy(latest_row)
        print("latest_row:", latest_row)

        documents = []
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            new_row = 0
            # if latest_row == 0 or latest_row % 10 == 0:
            viewer_count = self.api.detect_living_channel(self.channel)['viewer_count'] # Since viewerCount in Twitch API is updating in a slow pace, I request it for each iteration in while loop.
            for line in lines[latest_row+1:]:
                print("line: ", line)
                # logging.debug("line: ", line)
                try:
                    print("try parse_temp_chat_logs")
                    doc = self.parse_temp_chat_logs(line)
                    print("parsed_doc")
                    doc['viewerCount'] = viewer_count
                    if new_row >= 1: # skip the log which has already been inserted last time.
                        documents.append(doc)
                        print("appended temporary chat logs")
                    new_row += 1
                except Exception as e:
                    print(e)
                    pass
                self.lastest_record += 1
            if documents:
                self.db.insertmany_into_collection(documents, collection_name="tempChatLogs")
                print('inserted.')

    def temp_stats(self, channel): # temparory stats for streaming plot
        started_at = TwitchDeveloper().detect_living_channel(channel)['started_at']
        query = [
                    {
                        "$match":{
                            "selectionInfo.startedAt": { "$eq": started_at },
                            "selectionInfo.channel": {"$eq": channel}
                            }
                    },
                    {
                        "$project": {
                            "timestamp": 1,
                            "selectionInfo": 1,
                            'message': 1,
                            'cheer': 1,
                            'userName': 1,
                            'viewerCount': 1,
                            }
                    },
                    {
                        "$group": {
                            "_id": {
                                "$toDate": {
                                "$subtract": [
                                    { "$toLong": "$timestamp" },
                                    { "$mod": [{ "$toLong": "$timestamp" }, 5000] }
                                    ]
                                }
                            },
                            "messageCount": { "$sum": 1 },
                            "userNames": { "$addToSet": "$userName" },
                            "cheers": {
                                "$addToSet": {
                                    "$cond": {
                                        "if": {
                                            "$ne": ["$cheer", {}]
                                            },
                                        "then": "$cheer",
                                        "else": "$skip"
                                        }
                                    }
                                },
                            "averageViewerCount": { "$avg": "$viewerCount"},
                            "channel": {"$first": "$selectionInfo.channel"}
                        }
                    },
                    {
                        "$project": {
                            "timestamp": 1,
                            "channel": 1,
                            "cheers": 1,
                            "messageCount": 1,
                            "chatterCount": {
                                "$size": "$userNames"
                            },
                            "averageViewerCount": 1 
                        }
                    },
                    {
                        "$sort": { "_id": 1 }
                    }
                ]
        # logging.warning("started_at", started_at)
        # logging.warning("channel", channel)
        collection = self.db.connect_collection("tempChatLogs")
        # logging.warning(collection)
        temp_stats = [row for row in collection.aggregate(query)]
        # logging.warning(temp_stats)
        return temp_stats
    
    def delete_many_temp(self, channel):
        collection = self.db.connect_collection("tempChatLogs")
        query = { "selectionInfo.channel": channel }
        collection.delete_many(query)

if __name__ == "__main__":
    main()

# use_example

analyser = ViewersReactionAnalyser("scarra")
# # analyser.get_historical_schedule()
# # analyser.insert_historical_stats()
# # print(analyser.query_historical_stats())
# while True:
#     analyser.insert_chat_logs(
#         f"/Users/surfgreen/B/AppworksSchool/projects/personal_project/chat_logs/{analyser.channel}.log",
#         )
#     sleep(3)


task_records = analyser.db.connect_collection("taskRecords")
query = [
    {
        "$match": {"channel": "test"}
    },
    {
        "$group": {
            "_id": "null",
            "taskRecord": {"$addToSet": "$startedAt"}
            }
    },
    {
        "$project": {
            "taskRecord": 1,
            "_id": 0
        }
    }]
result = [row for row in task_records.aggregate(query)][0]
task_records = result['taskRecord']
print(task_records)