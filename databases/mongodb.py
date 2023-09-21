from pymongo import MongoClient
from decouple import config
host = "13.237.78.96"
port = 27017
username = "bosco"
password = config("mongo_pwd")
database = "personal_project"
global CONNECTION_STRING
CONNECTION_STRING = f"mongodb://{username}:{password}@{host}:{port}/{database}"
def connect_mongo(col_name):
    client = MongoClient(CONNECTION_STRING)
    db = client["personal_project"]
    col = db[col_name]
    return col
def insert_document(collection, data):
    # data = {"username": "John",
    #         "message": "" , 
    #         "sended_at": 30, 
    #         "category": "chatroom"}
    collection.insert_one(data)
    print("inserted.")

def upsert_document(collection, query, upsert_data):
    collection.update(
        query,
        upsert_data,
        {
            'upsert': True,
            'multi': True
        }
    )
    print(query)
    print(upsert_data)

def search_by_query(collection):
    cursor = collection.find({})
    for document in cursor:
          print(document)
    # query = { "name": "John" }
    # results = collection.find(query)
    # for result in results:
    #     print(result)

#client.close()
# search_by_query(connect_mongo())
# search_by_query(connect_mongo("chats"))