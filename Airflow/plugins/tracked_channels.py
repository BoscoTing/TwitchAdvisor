from .mongodb_manager import MongoDBManager
from .logging_manager import dev_logger

def get_tracked_channels():
    db = MongoDBManager()
    tracked_channels_collection = db.connect_collection("trackedChannels") # query from "trackingChannels" collection
    query = [
            {
                "$sort": {"addedTime": -1}
                }, 
            {
                "$limit": 1
                }
        ] # the query to get the tracked channels 
    
    result = tracked_channels_collection.aggregate(query)
    tracked_channels_list = [row['channels'] for row in result][0]
    dev_logger.info(f"tracked_channels: {tracked_channels_list}")

    return tracked_channels_list