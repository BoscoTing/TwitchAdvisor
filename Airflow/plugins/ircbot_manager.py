from decouple import config
from datetime import datetime
from emoji import demojize
from threading import Thread
import time
import socket
import logging
import os

from .logging_manager import dev_logger
from .twitch_api_manager import TwitchDeveloper
from .mongodb_manager import MongoDBManager

class TwitchChatListener():
    
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

        dev_logger.debug(f"trying to get 'startedAt' for {self.channel}'s live stream...")
        try:
            self.started_at = TwitchDeveloper().detect_living_channel(self.channel)['started_at'] # already turn timezone as Taipei for showing on the chart.

        except Exception as e:
            dev_logger.error(e)
            return False
         
        """
        record the start_tracking_livestream task in taskRecords collection.
        """
        dev_logger.info(f"{self.channel}'s live stream started at {self.started_at}")
        try:
            dev_logger.debug("ircbot_manager: trying to insert 'start_tracking_livestream' task record into taskRecords...")
            task_record_document = {
                "channel": self.channel,
                "startedAt": self.started_at, # bson format in Taipei timezone
                "taskName": "start_tracking_livestream",
                "completeTime": datetime.utcnow() # utc time for mongodb time series collection
            }
            self.db.insertone_into_collection(task_record_document, collection_name='taskRecords')
            dev_logger.info("successfully insert task records.")

        except Exception as e:
            dev_logger.error(e)
            
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s — %(message)s',
                            datefmt='%Y-%m-%d_%H:%M:%S',
                            handlers=[logging.FileHandler(os.getcwd() + f'/data/chat_logs/{self.started_at}_{self.channel}.log', 
                                                          mode='a',
                                                          encoding='utf-8')])
        
        dev_logger.info(f"Writing logs in /dags/chat_logs/{self.started_at}_{self.channel}.log")
    
    """
    1. In 'listen_to_chatroom' function, 'get_total_viewers_thread' function for threading collect 'viewer_count' at the same time.
    2. 'get_total_viewers_thread' pass 'self.viewer_count' to 'record_logs' function in 'while_loop_record_logs_thread'
    3. Add {viewer_count} to the doc, then insert them into "chatLogs" collection.
    """
    def record_logs(self, viewer_count):
        resp = self.sock.recv(2048).decode('utf-8')
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S') # utc time for mongodb time series collection
        formatted_resp = f"{timestamp} — {self.started_at} — {viewer_count} — {demojize(resp)}" 

        if resp.startswith('PING'):
            self.sock.send("PONG\n".encode('utf-8'))
        elif len(resp) > 0:
            logging.debug(demojize(resp))
            with open(os.getcwd() + f'/data/chat_logs/{self.started_at}_{self.channel}.log', 
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
        self.total_viewers = self.developer.get_total_viewers(self.channel) # request the total_viewer once at first
        while self.keep_listening:
            if int(time.monotonic()) % 60 == 0: # send requests once per minute to avoid from being banned
                self.total_viewers = self.developer.get_total_viewers(self.channel)
                dev_logger.debug("total_viewers:", self.total_viewers)

                if not self.total_viewers: # self.total_viewers will be False when the stream is not alive
                    dev_logger.debug("leaving chatroom...")

                    self.keep_listening = False
                    self.sock.close()
                    dev_logger.info("left chatroom.")


    def while_loop_record_logs_thread(self):
        while self.keep_listening:
            try:
                self.record_logs(self.total_viewers) # record the total_viewer too
            except Exception as e:
                dev_logger.error(e)

    def listen_to_chatroom(self):
        self.connect_chatroom()
        self.total_viewers_thread = Thread(target=self.get_total_viewers_thread)
        self.record_logs_thread = Thread(target=self.while_loop_record_logs_thread)

        self.total_viewers_thread.start()
        dev_logger.info("start total_viewers_thread")

        time.sleep(10) # wait for the response: viewer_count

        self.record_logs_thread.start()
        dev_logger.info("start record_logs_thread")

        self.record_logs_thread.join()
        dev_logger.info("join record_logs_thread")

        self.total_viewers_thread.join()
        dev_logger.info("join total_viewers_thread")
 
    def save_start_time(self):
        developer = TwitchDeveloper()
        db = MongoDBManager()
        self.started_time = developer.detect_living_channel(self.channel)
        doc = { 
            "started_time": self.started_time,
            "channel": self.channel
            }
        db.insertone_into_collection(doc, "schedules")