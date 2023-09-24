from datetime import datetime, timedelta
import os
import sys
sys.path.insert(0, os.getcwd())

from managers.mongodb_manager import MongoDBManager
from managers.models_manager import SentimentAnalyser

class ChatroomSentiment:
    def __init__(self):
        self.db = MongoDBManager()
        self.col = "chat_logs"
        self.analyser = SentimentAnalyser('cardiffnlp/twitter-roberta-base-sentiment')

    def analyse_new_messages(self):
        collection = self.db.connect_collection(self.col)
        query = {
            "$and": [ 
                {"timestamp": { "$gt": datetime.now()-timedelta(seconds=20) }}, 
                {"timestamp": { "$lte": datetime.now() }} 
            ] 
        }
        result = collection.find(query).sort("timestamp", -1).limit(5)
        messages = [doc['message'] for doc in result]

        score_list = [0, 0, 0] # [count(neg), count(neu), count(pos)]
        for msg in messages:
            score_list[self.analyser.sentiment_score(msg)] += 1 # sentiment_score: 0(negative), 1(neutral), 2(positive)
        
        return score_list
# ChatroomSentiment().analyse_new_messages()