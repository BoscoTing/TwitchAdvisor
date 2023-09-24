from datetime import datetime
from time import time, sleep
import re
import os
import sys
sys.path.insert(0, os.getcwd())
from copy import deepcopy

from managers.mongodb_manager import MongoDBManager

def main():
    print('this is python script of ViewersReactionAnalyser')

class ViewersReactionAnalyser():
    def __init__(self):
        self.last_record = 0
        self.db = MongoDBManager()
        self.col = "chat_logs"

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

    def parse_chat_logs(self, line):
        time_logged = line.split('—')[0].strip()
        time_logged = datetime.strptime(time_logged, '%Y-%m-%d_%H:%M:%S')
        username_message = line.split('—')[1:]
        username_message = '—'.join(username_message).strip()
        username, channel, message = re.search(
            ':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', username_message
        ).groups()
        doc = {
            'metadata': {
                'channel': channel,
                'username': username,
                'message': message,
                'cheer': self.recognize_cheers(line),
                'row': self.last_record
            },
            'timestamp': time_logged
        }
        return doc

    def insertmany_chat_logs(self, file):
        collection = self.db.connect_collection(self.col)

        latest_doc = [row for row in collection.find({}, {"metadata.row":1}).sort("timestamp", -1).limit(1)]

        if latest_doc == []:
            start_at = 0
        else: 
            start_at = latest_doc[0]['metadata']['row']
        self.last_record = deepcopy(start_at)

        documents = []
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
            for line in lines[start_at:]:
                try:
                    doc = self.parse_chat_logs(line)
                    documents.append(doc)
                except Exception:
                    pass
                self.last_record += 1

            if documents:
                self.db.insertmany_into_collection(documents, self.col)
                print('inserted.')
                # self.last_record = len(lines[start_at:]) # 必須包在if裡面 否則會變回０

    def query_chat_logs(self): # need to add new filter to find the doc of selected channel.
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
        values = {
                    "messages": messages_count, 
                    "chatters": chatters_count,
                    "cheers": [result for result in cheers_count],
                }
        return values
    
if __name__ == "__main__":
    main()

# # use_example
# analyser = ViewersReactionAnalyser()
# while True:
#     analyser.insertmany_chat_logs(
#         "/Users/surfgreen/B/AppworksSchool/projects/personal_project/log/chat.log",
#         )
#     sleep(1)
#     print(analyser.query_chat_logs())