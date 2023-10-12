from decouple import config
from datetime import datetime
from emoji import demojize
import socket
import logging
import os
import sys
sys.path.insert(0, os.getcwd())

from managers.twitch_api_manager import TwitchDeveloper
from managers.mongodb_manager import MongoDBManager

class TwitchChatListener:
    def __init__(self, channel):
        self.sock = None
        self.server = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nickname = 'myproject'
        self.token = config('twitch_token')
        self.channel = channel
        self.db = MongoDBManager()
        # self.started_at = TwitchDeveloper().detect_living_channel(self.channel)
    
    def connect_chatroom(self):
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))
        self.sock.send(f"PASS {self.token}\n".encode('utf-8'))
        self.sock.send(f"NICK {self.nickname}\n".encode('utf-8'))
        self.sock.send(f"JOIN {'#' + self.channel}\n".encode('utf-8'))

        resp = self.sock.recv(2048).decode('utf-8')
        print(f"getting 'startedAt' for {self.channel}'s live stream...")
        self.started_at = TwitchDeveloper().detect_living_channel(self.channel)['started_at'] # already turn timezone to +8 for showing on the chart.
        """
        record the start_tracking_livestream task in taskRecords collection.
        """
        print(f"{self.channel}'s live stream started at {self.started_at}")
        try:
            print("ircbot_manager: trying to insert 'start_tracking_livestream' task record into taskRecords...")
            task_record_document = {
                "channel": self.channel,
                "startedAt": self.started_at, # bson format in +8 timezone
                "taskName": "start_tracking_livestream",
                "completeTime": datetime.utcnow() # utc time for timeseries collection index.
            }
            self.db.insertone_into_collection(task_record_document, collection_name='taskRecords')
            print("successfully insert task records.")

        except Exception as e:
            print(e)
            
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s — %(message)s',
                            datefmt='%Y-%m-%d_%H:%M:%S',
                            handlers=[logging.FileHandler(os.getcwd() + f'/dags/chat_logs/{self.started_at}_{self.channel}.log', 
                                                          mode='a',
                                                          encoding='utf-8')])
        print(f"Writing logs in /dags/chat_logs/{self.started_at}_{self.channel}.log")
        logging.info(resp)

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
                            handlers=[logging.FileHandler(os.getcwd() + f'/chat_logs/{self.channel}.log', 
                                                          mode='w', # use 'w' mode to create log file everytime.
                                                          encoding='utf-8')])
        logging.info(resp)
        self.started_at = TwitchDeveloper().detect_living_channel(self.channel)['started_at']
    
    def record_logs(self):
        resp = self.sock.recv(2048).decode('utf-8')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S') # use utc time for insert into mongodb time series collection (which accept utc time). 
        formatted_resp = f"{timestamp} — {self.started_at} — {demojize(resp)}" 
        if resp.startswith('PING'):
            self.sock.send("PONG\n".encode('utf-8'))
        elif len(resp) > 0:
            logging.info(demojize(resp))
            with open(os.getcwd() + f'/dags/chat_logs/{self.started_at}_{self.channel}.log', 
                      'a', 
                      encoding='utf-8') as log_file:
                log_file.write(formatted_resp)
        return demojize(resp)
    
    def record_logs_temp(self):
        resp = self.sock.recv(2048).decode('utf-8')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S') # use utc time for insert into mongodb time series collection (which accept utc time). 
        formatted_resp = f"{timestamp} — {self.started_at} — {demojize(resp)}" # —
        if resp.startswith('PING'):
            self.sock.send("PONG\n".encode('utf-8'))
        elif len(resp) > 0:
            logging.info(demojize(resp))
            with open(os.getcwd() + f'/chat_logs/{self.channel}.log', 
                      'a', 
                      encoding='utf-8') as log_file:
                log_file.write(formatted_resp)
        return demojize(resp)
    
    def listen_to_chatroom(self):
        self.connect_chatroom()
        while True:
            self.record_logs()

    def listen_to_chatroom_temp(self):
        self.connect_chatroom_temp()
 
    def save_start_time(self):
        developer = TwitchDeveloper()
        db = MongoDBManager()
        self.started_time = developer.detect_living_channel(self.channel)
        doc = {
            "started_time": self.started_time,
            "channel": self.channel
            }
        db.insertone_into_collection(doc, "schedules")

# use_example

# if __name__ == "__main__":
#     chat_listener = TwitchChatListener("scarra")
#     chat_listener.save_start_time()
#     chat_listener.listen_to_chatroom() 