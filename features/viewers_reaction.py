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
        logging.debug("line: ", line)

        time_logged = line.split('—')[0].strip()
        time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')
        logging.debug("time_logged: ", time_logged)

        started_at = line.split('—')[1].strip()
        logging.debug("started_at: ", started_at)

        username_message = line.split('—')[2:]
        username_message = '—'.join(username_message).strip()

        # logging.info(username_message)
        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
        ).groups()
        doc = {
            'metadata': {
                'channel': channel,
                'started_at': started_at,
                'username': username,
                'message': message,
                'cheer': self.recognize_cheers(line),
                'row': self.lastest_record
            },
            'timestamp': time_logged
        }
        # logging.warning(doc[-1])
        return doc

    def insert_chat_logs(self, file): # streaming
        collection = self.db.connect_collection(self.col)
        # latest_doc = [row for row in collection.find({}, {"metadata.row":1}).sort("timestamp", -1).limit(1)]
        latest_doc = [row for row in collection.aggregate([
                    {
                        "$match":{
                            "metadata.channel": {"$eq": self.channel}
                            },
                    },
                    { 
                        "$project": {
                            "timestamp": 1,
                            "metadata": 1
                        }
                    },
                    {
                        "$sort": {
                            "metadata.row": -1
                        },
                    },
                    {
                        "$limit": 1
                    }
                    ])]
        logging.info(latest_doc)
        if latest_doc == []:
            latest_row = 0
        else: 
            latest_row = latest_doc[0]['metadata']['row']
        logging.warning(latest_row)
        self.lastest_record = deepcopy(latest_row)

        documents = []
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            new_row = 0
            viewer_count = self.api.detect_living_channel(self.channel)['viewer_count'] # Since viewerCount in Twitch API is updating in a slow pace, I request it for each iteration in while loop.
            for line in lines[latest_row+1:]:
                logging.debug("line: ", line)
                try:
                    logging.debug("trying parsing chat_logs...")
                    doc = self.parse_chat_logs(line)
                    doc['metadata']['viewer_count'] = viewer_count
                    if new_row >= 1: # skip the log which has already been inserted last time.
                        documents.append(doc)
                        logging.debug(doc)   
                        logging.debug("appended chat logs")
                    new_row += 1
                except Exception as e:
                    print(e)
                    logging.error(e)
                    pass
                self.lastest_record += 1

            if documents:
                print(documents)
                self.db.insertmany_into_collection(documents, collection_name=self.col)
                print('inserted.')

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
    
    def historical_stats(self): # historical
        # collection = self.db.connect_collection("schedules")
        # schedule = [row for row in collection.find(({})).sort('started_at', -1).limit(1)][0]
        query = [
                    {
                        "$match":{
                            "metadata.started_at": { "$eq": self.started_at },
                            "metadata.channel": {"$eq": self.channel}
                            }
                    },
                    {
                        "$project": {
                            "timestamp": 1,
                            "metadata": 1
                            }
                    },
                    {
                        "$group": {
                            "_id": {
                                "$toDate": {
                                "$subtract": [
                                    { "$toLong": "$timestamp" },
                                    { "$mod": [{ "$toLong": "$timestamp" }, 30000] }
                                    ]
                                }
                            },
                        "message_count": { "$sum": 1 },
                        "usernames": { "$addToSet": "$metadata.username" },
                        "cheers": {
                            "$addToSet": {
                                "$cond": {
                                    "if": {
                                        "$ne": ["$metadata.cheer", {}]
                                        },
                                    "then": "$metadata.cheer",
                                    "else": "$skip"
                                    }
                                }
                            },
                        "avg_viewer_count": { "$avg": "$metadata.viewer_count"}
                        }
                    },
                    {
                        "$project": {
                            "channel": 1,
                            "cheers": 1,
                            "message_count": 1,
                            "chatter_count": {
                                "$size": "$usernames"
                            },
                            "avg_viewer_count": 1 
                        }
                    },
                    {
                        "$sort": { "_id": 1 }
                    }
                ]
        collection = self.db.connect_collection("chat_logs")
        stats = [row for row in collection.aggregate(query)]
        return stats

    def insert_historical_stats(self): # insert all historical stats data right after the live streaming ends using insertmany.
        self.started_at = self.get_historical_schedule()[-1]
        stats = deepcopy(self.historical_stats()) # self.historical_stats() will need self.started_at
        organized_documents = []
        for doc in stats:
            organized_doc = {}
            organized_doc['timestamp'] = doc['_id']
            organized_doc['metadata'] = {
                "channel": self.channel,
                "started_at": self.started_at,
                "avg_viewer_count": doc['avg_viewer_count'],
                "message_count": doc['message_count'],
                "chatter_count": doc['chatter_count'],
                "cheers": doc['cheers']
            }
            organized_documents.append(organized_doc)
        try:
            self.db.insertmany_into_collection(organized_documents, collection_name='chat_stats')
        except Exception as e:
            print(e)
            sleep(5)
            pass

    def query_historical_stats(self, started_at): # the "started_at" here is the argument requested from flask app, which is different from "self.started_at"
        # self.started_at = self.get_historical_schedule()[-1]
        collection = self.db.connect_collection("chat_stats")
        if started_at: # if user chose the schedule date
            logging.warning(started_at)
            result = [row for row in collection.aggregate([
                {
                    "$match": {
                        "metadata.started_at": started_at,
                        "metadata.channel": self.channel
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
                most_current = self.get_historical_schedule()[-1]
                logging.warning(type(most_current))
                result = [row for row in collection.aggregate([
                    {
                        "$match": {
                            "metadata.started_at": most_current,
                            "metadata.channel": self.channel
                        }
                    },
                    {
                        "$sort": {
                            "timestamp": -1
                        }
                    }
                    ])]
                return result

            except Exception as e:
                logging.error("query_historical_stats:", e)
                return False

    
    def get_historical_schedule(self):
        collection = self.db.connect_collection("chat_logs")
        query = [
            {
                "$match": {
                    "metadata.channel": {"$eq": self.channel}
                }
            },
            {
                "$project": {
                    "metadata.started_at": 1,
                    "_id": 0 
                }
            },
            {
                "$group": {
                    "_id": "null",  # Use null to group all documents into one group
                    "schedule": {"$addToSet": "$metadata.started_at"}
                }
            }
        ]

        schedule = [row['schedule'] for row in collection.aggregate(query)][0]
        print(schedule)
        return schedule

    def parse_temp_chat_logs(self, line): # define the schema of inserted document 
        logging.debug("line: ", line)

        time_logged = line.split('—')[0].strip()
        time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')
        logging.debug("time_logged", time_logged)

        started_at = line.split('—')[1].strip()
        logging.warning("started_at", started_at)

        username_message = line.split('—')[2:]
        username_message = '—'.join(username_message).strip()
        logging.warning("username_message", username_message)

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
        logging.warning("parsed_doc", doc)
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
        logging.info("latest_doc:", latest_doc)
        if latest_doc == []:
            latest_row = 0
        else: 
            latest_row = latest_doc[0]['insertOrder']
        logging.warning(latest_row)
        self.lastest_record = deepcopy(latest_row)

        documents = []
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            new_row = 0
            viewer_count = self.api.detect_living_channel(self.channel)['viewer_count'] # Since viewerCount in Twitch API is updating in a slow pace, I request it for each iteration in while loop.
            for line in lines[latest_row+1:]:
                logging.debug("line: ", line)
                try:
                    logging.warning("parse_line", line)
                    doc = self.parse_temp_chat_logs(line)
                    logging.warning("parsed_doc", doc)
                    doc['viewerCount'] = viewer_count
                    if new_row >= 1: # skip the log which has already been inserted last time.
                        documents.append(doc)
                        logging.warning(doc)   
                        logging.warning("appended temporary chat logs")
                    new_row += 1
                except Exception as e:
                    print(e)
                    logging.error("insert_temp_chat_logs:", e)
                    pass
                self.lastest_record += 1
            # print(documents)
            if documents:
                logging.info(documents)
                self.db.insertmany_into_collection(documents, collection_name="tempChatLogs")
                logging.warning('inserted.')

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
                            'timestamp': 1,
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
        logging.warning("started_at", started_at)
        logging.warning("channel", channel)
        collection = self.db.connect_collection("tempChatLogs")
        logging.warning(collection)
        temp_stats = [row for row in collection.aggregate(query)]
        logging.warning(temp_stats)

        return temp_stats

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