from datetime import datetime
from time import time, sleep
from copy import deepcopy
import re
import os
import sys
sys.path.insert(0, os.getcwd())
from copy import deepcopy

from managers.logging_manager import send_log, dev_logger
from managers.mongodb_manager import MongoDBManager
from managers.ircbot_manager import TwitchChatListener
from managers.twitch_api_manager import TwitchDeveloper

class ViewersReactionAnalyser():

    def __init__(self, channel):
        self.channel = channel
        self.listener = TwitchChatListener(channel)
        self.db = MongoDBManager()
        self.col = "chatLogs"
        self.api = TwitchDeveloper()
        self.lastest_record = 0 

    def recognize_cheers(self, line): # used
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
    
    def parse_chat_logs(self, line): # used # define the schema of inserted document 

        """ 
        in the log file, the first section is datetime string format in utc timezone, 
        the second section is Bson time format in +8 timezone.
        """
        time_logged = line.split('—')[0].strip()
        time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S') # turn from string to datetime format.

        started_at = line.split('—')[1].strip()

        viewer_count = int(line.split('—')[2].strip())

        username_message = line.split('—')[3:]
        username_message = '—'.join(username_message).strip()

        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
        ).groups()
        doc = {
            'message': message,
            'cheer': self.recognize_cheers(line),
            'viewerCount': viewer_count,
            'userName': username,
            'insertOrder': self.lastest_record,
            'timestamp': time_logged, # datetime format in timezone of ROC
            'selectionInfo': {
                'channel': channel,
                'startedAt': started_at
                }        
            }
        return doc

    def insert_chat_logs(self): # used
        """
        Only triggered after the channel turn into offline.
        """

        task_records_collction = self.db.connect_collection("taskRecords") 
        query = [  
            {
                "$match": {
                    "channel": self.channel,
                    "taskName": "start_tracking_livestream"}
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
            start_tracking_livestream_records = result['taskRecord']
        except: 
            start_tracking_livestream_records = []
        # send_log(f"completed 'start_tracking_livestream' tasks: {start_tracking_livestream_records}")
        # dev_logger.info("completed 'start_tracking_livestream' tasks: ", start_tracking_livestream_records)

        query = [  
            {
                "$match": {
                    "channel": self.channel,
                    "taskName": "insert_logs"} 
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
            insert_logs_records = result['taskRecord']
        except: 
            insert_logs_records = []
        # send_log(f"completed 'insert_logs_records' tasks: {insert_logs_records}") 
        # dev_logger.info("completed 'insert_logs_records' tasks: ", insert_logs_records)


        """
        compare the start_tracking_livestream_records and insert_logs_records to find 'startedAt' that insert_logs_records is uncompleted
        """
        uncompleted_tasks = list(set(start_tracking_livestream_records).difference(insert_logs_records)) # find uncomplete 'insert_logs' tasks
        send_log(f"uncompleted insert_logs tasks: {uncompleted_tasks}")
        dev_logger.info("uncompleted insert_logs tasks: ", uncompleted_tasks)

        for uncompleted_started_at in uncompleted_tasks:

            documents = []

            if os.path.exists(os.getcwd() + f"/data/chat_logs/{uncompleted_started_at}_{self.channel}.log"): 
                
                with open(
                    os.getcwd() + f"/data/chat_logs/{uncompleted_started_at}_{self.channel}.log", 
                    # os.getcwd() + f"/chat_logs/{uncompleted_started_at}_{self.channel}.log", 

                    'r', 
                    encoding='utf-8'
                    ) as f:

                    lines = f.read().split('\n')

                    for line in lines: #[latest_row + 1:]:

                        try:
                            doc = self.parse_chat_logs(line)
                            documents.append(doc)

                        except Exception as e:
                            # send_log(e)
                            dev_logger.error(e)

                    if documents:
                        # send_log("inserting documents into 'chatLogs' collection...")
                        dev_logger.info("inserting documents into 'chatLogs' collection...")

                        self.db.insertmany_into_collection(documents, collection_name="chatLogs")
                        # send_log('inserted')
                        dev_logger.info('inserted')

                        """
                        record the completed insert_logs task in taskRecords collection.
                        """
                        try:
                            # send_log("viewers_reaction: trying to insert 'insert_logs' task record into taskRecords...")
                            dev_logger.info("viewers_reaction: trying to insert 'insert_logs' task record into taskRecords...")
                            task_record_document = {
                                "channel": self.channel,
                                "startedAt": uncompleted_started_at, # bson format in +8 timezone
                                "taskName": "insert_logs",
                                "completeTime": datetime.utcnow() # utc time for timeseries collection index.
                            }

                            self.db.insertone_into_collection(task_record_document, collection_name='taskRecords')
                            # send_log("successfully insert task records.")
                            dev_logger.info("successfully insert task records.")
                            
                        except Exception as e:
                            # send_log(e)
                            dev_logger.error(e)
            else: 
                print(f"/data/chat_logs/{uncompleted_started_at}_{self.channel}.log doesn't exist.")

    def query_chat_logs(self): # streaming # need to add new filter to find the doc of selected channel.
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
    
    def historical_stats(self, started_at): # used
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

    def insert_historical_stats(self): # insert all historical stats data right after the live streaming ends using insertmany.


        """
        This function is called repeatedly when the channel is off-line.

        Query the record of completed task to check if insert_historical_stats has done already or not.
        if the latest task record is behind of the latest startedAt in chatLogs, execute insert_historical_stats.
        """
        task_records_collction = self.db.connect_collection("taskRecords") 
        query = [  
            {
                "$match": {
                    "channel": self.channel,
                    "taskName": "insert_logs"
                    }
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
        
        dev_logger.info(f"trying to check uncompleted tasks for {self.channel}...")

        """
        get the latest startedAt record of 'insert_logs' task.
        """
        try:
            result = [row for row in task_records_collction.aggregate(query)][0]
            insert_logs_task_records = result['taskRecord']
        except: 
            insert_logs_task_records = []
            
        dev_logger.info("completed insert_logs tasks: ", insert_logs_task_records)


        """
        get the latest startedAt record of 'insert_stats' task.
        """

        query = [  
            {
                "$match": {
                    "channel": self.channel,
                    "taskName": "insert_stats"
                    }
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
            insert_stats_task_records = result['taskRecord']
        except: 
            insert_stats_task_records = []

        # send_log(f"completed insert_stats tasks: {insert_stats_task_records}")
        dev_logger.info("completed insert_stats tasks: ", insert_stats_task_records)


        """
        Countinue if insert_stats haven't been executed after channel turned into off-line.
        """
        uncompleted_tasks = list(set(insert_logs_task_records).difference(insert_stats_task_records)) # find uncomplete 'insert_stats' tasks
        print("uncompleted_tasks: ", uncompleted_tasks)
        for uncompleted_started_at in uncompleted_tasks:

            # send_log(f"completed insert_stats tasks: {insert_stats_task_records}")
            dev_logger.info(f"{self.channel}'s live stream started at {uncompleted_started_at} has not been calculated and inserted.")

            print("viewers_reaction: querying historical_stats...")
            stats = deepcopy(self.historical_stats(uncompleted_started_at)) # calculate chatstats from chatlogs # self.historical_stats() will need self.started_at
            organized_documents = []
            
            print("(skipped) viewers_reaction: calculating sentiment_score...")

            for doc in stats:
                doc['timestamp'] = doc['_id']
                organized_documents.append(doc)

            try:
                # send_log("viewers_reaction: trying to insertmany into chatStats...")
                dev_logger.info("viewers_reaction: trying to insertmany into chatStats...")

                self.db.insertmany_into_collection(organized_documents, collection_name='chatStats')
                # send_log("successfully insert historical stats.")
                dev_logger.info("successfully insert historical stats.")
                print("successfully insert historical stats.")

            except Exception as e:
                # send_log(e)
                dev_logger.error(e)

            """
            record the insert_stats task in taskRecords collection.
            """
            try:
                print("viewers_reaction: trying to insert 'insert_stats' task record into taskRecords...")
                task_record_document = {
                    "channel": self.channel,
                    "startedAt": uncompleted_started_at, # bson format in +8 timezone
                    "taskName": "insert_stats",
                    "completeTime": datetime.utcnow() # utc time for timeseries collection index.
                }
                self.db.insertone_into_collection(task_record_document, collection_name='taskRecords')
                # send_log("successfully insert task records.")
                dev_logger.info("successfully insert task records.")
                print("successfully insert task records.")

            except Exception as e:
                # send_log(e)
                dev_logger.error(e)