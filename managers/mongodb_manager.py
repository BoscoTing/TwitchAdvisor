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



# use_example
# if __name__ == "__main__":
#     mongodb_manager = MongoDBManager()