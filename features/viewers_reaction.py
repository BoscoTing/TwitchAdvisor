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
        # self.started_at = deepcopy(self.api.detect_living_channel(channel)['started_at'])
        # print(self.start_at)

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
        # print(summary_dict)
        return summary_dict
    
    def parse_chat_logs(self, line): # define the schema of inserted document 
        print("line: ", line)
        # logging.debug("line: ", line)

        time_logged = line.split('—')[0].strip()
        time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')
        print("time_logged", time_logged)
        # logging.debug("time_logged", time_logged)

        started_at = line.split('—')[1].strip()
        print("started_at", started_at)
        # logging.debug("started_at", started_at)

        username_message = line.split('—')[2:]
        username_message = '—'.join(username_message).strip()
        print("username_message", username_message)
        # logging.debug("username_message", username_message)

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
        # logging.info("latest_doc:", latest_doc)
        if latest_doc == []:
            latest_row = 0
        else: 
            latest_row = latest_doc[0]['insertOrder']
        print(latest_row)
        # logging.debug(latest_row)
        self.lastest_record = deepcopy(latest_row)

        documents = []
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            new_row = 0
            viewer_count = self.api.detect_living_channel(self.channel)['viewer_count'] # Since viewerCount in Twitch API is updating in a slow pace, I request it for each iteration in while loop.
            for line in lines[latest_row+1:]:
                print("line: ", line)
                # logging.debug("line: ", line)
                try:
                    print("parse_line", line)
                    # logging.info("parse_line", line)
                    doc = self.parse_chat_logs(line)
                    print("parsed_doc")
                    # logging.info("parsed_doc")
                    doc['viewerCount'] = viewer_count
                    if new_row >= 1: # skip the log which has already been inserted last time.
                        documents.append(doc)
                        print("appended chat logs")
                        # logging.debug("appended chat logs")
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
        # logging.warning("started_at", started_at)
        # logging.warning("channel", channel)
        collection = self.db.connect_collection("chatLogs")
        # logging.warning(collection)
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
        historical_schedule_list = self.get_historical_schedule()
        print("historical_schedule: ", historical_schedule_list)
        started_at = self.sort_isodate_schedule(historical_schedule_list)[-1]
        # started_at = self.get_historical_schedule()[-1]
        print("viewers_reaction: insert_historical_stats", started_at)
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
            print("successfully insertmany.")
        except Exception as e:
            print(e)
            sleep(5)

    def query_historical_stats(self, started_at): # the "started_at" here is the argument requested from flask app, which is different from "self.started_at"
        # self.started_at = self.get_historical_schedule()[-1]
        collection = self.db.connect_collection("chatStats")
        if started_at: # if user chose the schedule date
            print("viewers_reaction.py: query_historical_stats", started_at)
            # logging.debug("viewers_reaction.py: query_historical_stats", started_at)
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

        else: # If user chose the schedule date doesn't select a date. Usually happend when user first get into historical page.
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
                # logging.error("query_historical_stats:", e)
                return False

    
    def get_historical_schedule(self):
        collection = self.db.connect_collection("chatLogs")
        query = [
            {
                "$match": {
                    "selectionInfo.channel": {"$eq": self.channel}
                }
            },
            {
                "$project": {
                    "selectionInfo.startedAt": 1,
                    "_id": 1
                }
            },
            {
                "$group": {
                    "_id": "null", 
                    "schedule": {"$addToSet": "$selectionInfo.startedAt"}
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

# analyser = ViewersReactionAnalyser("scarra")
# # analyser.get_historical_schedule()
# # analyser.insert_historical_stats()
# # print(analyser.query_historical_stats())
# while True:
#     analyser.insert_chat_logs(
#         f"/Users/surfgreen/B/AppworksSchool/projects/personal_project/chat_logs/{analyser.channel}.log",
#         )
#     sleep(3)