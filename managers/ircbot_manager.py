from decouple import config
from emoji import demojize
import socket
import logging

class TwitchChatListener:
    def __init__(self, channel):
        self.sock = None
        self.server = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nickname = 'myproject'
        self.token = config('twitch_token')
        self.channel = '#' + channel
    
    def connect_chatroom(self):
        self.sock = socket.socket()
        self.sock.connect((self.server, self.port))
        self.sock.send(f"PASS {self.token}\n".encode('utf-8'))
        self.sock.send(f"NICK {self.nickname}\n".encode('utf-8'))
        self.sock.send(f"JOIN {self.channel}\n".encode('utf-8'))
        resp = self.sock.recv(2048).decode('utf-8')
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s — %(message)s',
                            datefmt='%Y-%m-%d_%H:%M:%S',
                            handlers=[logging.FileHandler(f'/Users/surfgreen/B/AppworksSchool/projects/files/log/chat_{self.channel}.log', 
                                                          encoding='utf-8')])
        logging.info(resp)
    
    def record_logs(self):
        resp = self.sock.recv(2048).decode('utf-8')
        if resp.startswith('PING'):
            self.sock.send("PONG\n".encode('utf-8'))  
        elif len(resp) > 0:
            logging.info(demojize(resp))
        return demojize(resp)
    
    def listen_to_chatroom(self):
        self.connect_chatroom()
        while True:
            msg_log = self.record_logs()
            print(msg_log)

# use_example
# if __name__ == "__main__":
#     chat_listener = TwitchChatListener("fanta")
#     chat_listener.listen_to_chatroom() 