from pymongo import MongoClient
from decouple import config 

class MongoDBManager:
    def __init__(self):
        host = config("mongodb_host")
        port = 27017
        username = 'bosco'
        password = config("mongodb_pwd")
        database = "personal_project"
        self.CONNECTION_STRING = f"mongodb://{username}:{password}@{host}:{port}/{database}"
        self.client = MongoClient(self.CONNECTION_STRING)
        self.db = self.client[database]
    
    def connect_collection(self, col):
        collection = self.db[col]
        return collection
    
    def insertmany_into_collection(self, documents, collection_name):
        collection = self.db[collection_name]
        collection.insert_many(documents)

    def insertone_into_collection(self, document, collection_name):
        collection = self.db[collection_name]
        collection.insert_one(document)

    def query_historical_data(self, channel, started_at):
        collection = self.db["chat_logs"]
        query = collection.find({}, {"metadata.started_at": { "$in": [started_at]},
                                     "metadata.channel": {"in": [channel]}})
    def delete_many(self, channel, collection):
        collection = self.db[collection]
        query = {"selectionInfo.channel": channel }
        collection.delete_many(query)
# collection.find({}, {"metadata.row":1}).sort("timestamp", -1).limit(1)]

# use_example
# if __name__ == "__main__":
#     mongodb_manager = MongoDBManager()
# MongoDBManager().delete_many("froggen", 'tempChatLogs')