from decouple import config
from emoji import demojize
import socket
import logging

from preparing_doc import parse_chat_mongo

sock = socket.socket()
server = 'irc.chat.twitch.tv'
port = 6667
nickname = 'learndatasci'
token = config("twitch_token")
channel = '#fanta'

sock.connect((server, port))
sock.send(f"PASS {token}\n".encode('utf-8'))
sock.send(f"NICK {nickname}\n".encode('utf-8'))
sock.send(f"JOIN {channel}\n".encode('utf-8'))
resp = sock.recv(2048).decode('utf-8')
# sock.close()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s — %(message)s',
                    datefmt='%Y-%m-%d_%H:%M:%S',
                    handlers=[logging.FileHandler('/Users/surfgreen/B/AppworksSchool/projects/files/log/chat.log', encoding='utf-8')])

logging.info(resp)

def get_chats():
    resp = sock.recv(2048).decode('utf-8')
    # print(resp)
    if resp.startswith('PING'):
        sock.send("PONG\n".encode('utf-8'))
    elif len(resp) > 0:
        print(demojize(resp))
        logging.info(demojize(resp))
    return demojize(resp)

while True:
    chat_log = get_chats()
    parse_chat_mongo(chat_log)