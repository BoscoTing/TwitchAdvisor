from decouple import config
from datetime import datetime
from emoji import demojize
from threading import Thread, Event

import time
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
        self.developer = TwitchDeveloper()
    
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
            
        # logging.basicConfig(level=logging.DEBUG,
        #                     format='%(asctime)s — %(message)s',
        #                     datefmt='%Y-%m-%d_%H:%M:%S',
        #                     handlers=[logging.FileHandler(os.getcwd() + f'/dags/chat_logs/{self.started_at}_{self.channel}.log', 
        #                                                   mode='a',
        #                                                   encoding='utf-8')])
        
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s — %(message)s',
                            datefmt='%Y-%m-%d_%H:%M:%S',
                            handlers=[logging.FileHandler(os.getcwd() + f'/chat_logs/{self.started_at}_{self.channel}.log', 
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
            # with open(os.getcwd() + f'/dags/chat_logs/{self.started_at}_{self.channel}.log', 
            #           'a', 
            #           encoding='utf-8') as log_file:
            #     log_file.write(formatted_resp)
            with open(os.getcwd() + f'/chat_logs/{self.started_at}_{self.channel}.log', 
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
            

    """
    1.create two threads to run a while loop.
        (1) get_total_viewers_thread: In every 30 seconds, send request to get total_viewers.
        (2) while_loop_record_logs_thread: Connect to socket, then insert and return the 'resp' until chatroom got new message.
    2. Start two threads in 'listen_to_chatroom' function.
    3. If total_viewers == False, the live stream might be offline.
    4. When livestream go offline, set keep_listening = False to exit the while loop.
    5. close the socket in case that while_loop_record_logs_thread is still waiting for new message.
    """

    def get_total_viewers_thread(self):
        self.keep_listening = True
        while self.keep_listening:
            if int(time.monotonic()) % 30 == 0:
                self.total_viewers = self.developer.get_total_viewers(self.channel)
                # print(time.monotonic())
                print("total_viewers:", self.total_viewers)

                if not self.total_viewers: # total_viewers will be False when the stream is not alive,
                    print("leave chatroom")
                    self.keep_listening = False
                    print("set event.is_set()")
                    self.sock.close()

    def while_loop_record_logs_thread(self):
        while self.keep_listening:
            try:
                print(self.record_logs())
            except:
                print("set sock.close()")

    def listen_to_chatroom(self):
        self.connect_chatroom()
        self.total_viewers_thread = Thread(target=self.get_total_viewers_thread)
        self.record_logs_thread = Thread(target=self.while_loop_record_logs_thread)

        self.total_viewers_thread.start()
        print("start total_viewers_thread")

        self.record_logs_thread.start()
        print("start record_logs_thread")

        self.record_logs_thread.join()
        print("join record_logs_thread")

        self.total_viewers_thread.join()
        print("join total_viewers_thread")


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

if __name__ == "__main__":
    chat_listener = TwitchChatListener("trumporbiden2024")
    chat_listener.save_start_time()
    chat_listener.listen_to_chatroom() 