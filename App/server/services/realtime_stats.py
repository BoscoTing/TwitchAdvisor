import socket
import logging
import re
import os
import sys
import requests
from copy import deepcopy
from decouple import config
from emoji import demojize
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)

from ..models.mongodb_manager import MongoDBManager
from ..utils.logger import send_log, dev_logger

log_path = "../static/assets/chat_logs/"

sys.path.insert(0, os.getcwd())


def main():
    send_log('this is python script of ViewersReactionAnalyserTEMP')


class TwitchChatListenerTEMP():

    def __init__(self, channel):
        self.sock = None
        self.server = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nickname = 'myproject'
        self.token = config('twitch_token')
        self.channel = channel
        self.db = MongoDBManager()

    def connect_chatroom_temp(self):
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))
        self.sock.send(f"PASS {self.token}\n".encode('utf-8'))
        self.sock.send(f"NICK {self.nickname}\n".encode('utf-8'))
        self.sock.send(f"JOIN {'#' + self.channel}\n".encode('utf-8'))

        resp = self.sock.recv(2048).decode('utf-8')
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s — %(message)s',
                            datefmt='%Y-%m-%d_%H:%M:%S',
                            handlers=[logging.FileHandler(os.getcwd() + f'/App/server/static/assets/chat_logs/{self.channel}.log', 
                                                          mode='w', # use 'w' mode to create log file everytime.
                                                          encoding='utf-8')])
        logging.debug(resp)
        try:
            self.started_at = TwitchDeveloper().detect_living_channel(self.channel)['started_at'] # already turn timezone to +8 for showing on the chart.

        except Exception as e:
            send_log(e)
            return False
    
    """
    1. In 'listen_to_chatroom' function, 'get_total_viewers_thread' function for threading collect 'viewer_count' at the same time.
    2. 'get_total_viewers_thread' pass 'self.viewer_count' to 'record_logs' function in 'while_loop_record_logs_thread'
    3. Add {viewer_count} to the doc, then insert them into "chatLogs" collection.
    """

    def record_logs_temp(self):
        resp = self.sock.recv(2048).decode('utf-8')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S') # use utc time for insert into mongodb time series collection (which accept utc time). 
        formatted_resp = f"{timestamp} — {self.started_at} — {demojize(resp)}" # —
        if resp.startswith('PING'):
            self.sock.send("PONG\n".encode('utf-8'))
        elif len(resp) > 0:
            # logging.info(demojize(resp))
            with open(os.getcwd() + f'/App/server/static/assets/chat_logs/{self.channel}.log', 
                      'a', 
                      encoding='utf-8') as log_file:
                log_file.write(formatted_resp)
        return demojize(resp)
            
    """
    1.create two threads to run a while loop.
        (1) get_total_viewers_thread: In every 30 seconds, send request to get total_viewers.
        (2) while_loop_record_logs_thread: Connect to socket, then insert and return the 'resp' until chatroom got new message.
    2. Start two threads in 'listen_to_chatroom' function.
    3. If total_viewers == False, the live stream might be offline.
    4. When livestream go offline, set keep_listening = False to exit the while loop.
    5. close the socket in case that while_loop_record_logs_thread is still waiting for new message.
    """

    def listen_to_chatroom_temp(self): # realtime_chart_controller

        self.keep_listening_temp = True
        self.connect_chatroom_temp()
        send_log("connect_chatroom_temp")

        while self.keep_listening_temp:
            self.record_logs_temp()

        return False

    def save_start_time(self):
        developer = TwitchDeveloper()
        db = MongoDBManager()
        self.started_time = developer.detect_living_channel(self.channel)
        doc = { 
            "started_time": self.started_time,
            "channel": self.channel
            }
        db.insertone_into_collection(doc, "schedules")

class TwitchDeveloper:
    def __init__(self):
        self.client_id = config('twitch_app_id')
        self.secret = config('twitch_app_secret')

    def get_token(self):
        auth_params = {
            'client_id': config('twitch_app_id'),
            'client_secret': config('twitch_app_secret'),
            'grant_type': 'client_credentials'
        }
        auth_url = 'https://id.twitch.tv/oauth2/token'
        auth_request = requests.post(url=auth_url, params=auth_params) 
        access_token = auth_request.json()['access_token']
        return access_token
    
    def search_channels(self):
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        query = "type=live&language=en&first=100"
        url = f'https://api.twitch.tv/helix/streams?{query}'
        resp = requests.get(url, headers=headers).json()['data']
        # print(resp[0:20])

        channel_dict = {
            'Just Chatting': [],
            'League of Legends': [],
            'Music': []
        }
        if resp:
            for channel in resp:
                if channel['game_name'] in ['League of Legends', 'Just Chatting', 'Music']:
                    game_name = channel['game_name']
                    channel_name = channel['user_login']
                    channel_dict[game_name].append(channel_name)
        else:
            return False
        
        return channel_dict
        
    def detect_living_channel(self, channel):
        
        url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp_data = requests.get(url, headers=headers).json()['data']

        if resp_data:
            """
            turn startedAt into +8 timezone. 
            startedAt will be recorded in log file and then inserted into chatLogs collection.
            """
            taipei_time = datetime.fromisoformat(resp_data[0]['started_at'][:-1]) + timedelta(hours=8)
            taipei_isoformat = datetime.isoformat(taipei_time) + "+08:00"
            resp_data[0]['started_at'] = taipei_isoformat
            logging.info(resp_data[0])
            return resp_data[0]
        
        else:
            return False
        
    def get_total_viewers(self, channel):
        
        url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp_data = requests.get(url, headers=headers).json()['data']

        if resp_data:
            return resp_data[0]['viewer_count']
        
        else:
            return False
    
    def get_broadcaster_id(self, channel):
        url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp_data = requests.get(url, headers=headers).json()['data']
        if resp_data:
            return resp_data[0]['user_id']
        else:
            return False
        
    def get_channel_schedule(self, channel):
        broadcaster_id = self.get_broadcaster_id(channel)
        print(broadcaster_id)
        url = f"https://api.twitch.tv/helix/schedule?broadcaster_id={broadcaster_id}"
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp_data = requests.get(url, headers=headers).json()#['data']
        if resp_data:
            return resp_data#[0]
        else:
            return False

class ViewersReactionAnalyserTEMP():

    def __init__(self, channel):
        self.channel = channel
        self.listener = TwitchChatListenerTEMP(channel)
        self.db = MongoDBManager()
        self.col = "chat_logs"
        self.api = TwitchDeveloper()
        self.lastest_record = 0 

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
        if latest_doc == []:
            latest_row = 0
        else: 
            latest_row = latest_doc[0]['insertOrder']
        self.lastest_record = deepcopy(latest_row)

        documents = []
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            new_row = 0
            """
            request viewer_count from Twitch API and show on streamingPlot section.
            """
            viewer_count = self.api.detect_living_channel(self.channel)['viewer_count'] # Since viewerCount in Twitch API is updating in a slow pace, I request it for each iteration in while loop.
            for line in lines[latest_row+1:]:
                print("line: ", line)
                try:
                    doc = self.parse_temp_chat_logs(line)
                    doc['viewerCount'] = viewer_count
                    if new_row >= 1: # skip the log which has already been inserted last time.
                        documents.append(doc)
                    new_row += 1
                except Exception as e:
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

        collection = self.db.connect_collection("tempChatLogs")
        temp_stats = [row for row in collection.aggregate(query)]
        return temp_stats
    
    def delete_many_temp(self, channel):
        collection = self.db.connect_collection("tempChatLogs")
        query = { "selectionInfo.channel": channel }
        collection.delete_many(query)


if __name__ == "__main__":
    main()