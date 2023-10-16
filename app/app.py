from flask import (Flask, 
                   render_template, 
                   request, 
                   )
import pytz
from datetime import datetime, timedelta
import re
import json
import os
import sys
sys.path.insert(0, "/Users/surfgreen/B/AppworksSchool/projects/personal_project")

from managers.twitch_api_manager import TwitchDeveloper
from managers.ircbot_manager import TwitchChatListener
from features.viewers_reaction import ViewersReactionAnalyser
from features.channel_overview import Overview
from managers.mongodb_manager import MongoDBManager

app = Flask(__name__)

@app.route("/") # main page
def main_page():
    db = MongoDBManager()
    tracked_channels_collection = db.connect_collection("trackedChannels") # query from "trackingChannels" collection
    query = [
            {
                "$sort":{"addedTime": -1}
                }, 
            {
                "$limit": 1
                }
        ] # the query to get the tracked channels 
    result = tracked_channels_collection.aggregate(query)

    tracked_channels_list = [row['channels'] for row in result][0]
    broadcasters = [" ".join(i.split("_")).title() for i in tracked_channels_list]

    """
    1. set default week number for overviewPlot.
    2. query min/max week number.
    """
    now_week_of_year=datetime.now().isocalendar().week
    now_year = datetime.now().year
    week_value = f"{now_year}-W{now_week_of_year}"

    overview = Overview()
    schedule_week_range = overview.get_schedule_week_range()
    start_week = schedule_week_range[0]
    end_week = schedule_week_range[1]
    return render_template(
        'main.html', 
        broadcasters=broadcasters,
        week_value=week_value,
        start_week=start_week,
        end_week=end_week
    )


@app.route("/api/update_channels", methods=["GET"])
def get_channel_list():
    def snake_case(key):
        return '_'.join(
            re.sub('([A-Z][a-z]+)', r' \1',
            re.sub('([A-Z]+)', r' \1',
            key.replace('-', ' '))).split()).lower()
    if request.method == "GET":
        channel_dict = TwitchDeveloper().search_channels()
        
        renamed_channel_dict = {} # renamed keys of channel_dict using snake case
        for key, value in channel_dict.items():
            renamed_key = snake_case(key)
            if value not in ['sneakylol', 'gosu', 'disguisedtoast', 'scarra', 'trick2g', 'midbeast', 'perkz_lol']:
                renamed_channel_dict[renamed_key] = value
            data = {'data': renamed_channel_dict}

        channel_json = json.dumps(data)
        return channel_json

"""
1. Create a class and assign to stream_logs_route outside of the view
2. Use the stream_logs_route inside the 'streaming_logs' by: 
        global stream_logs_route
3. So the different requests to /api/streaming_logs are using the same 'StreamingLogsRoute' class to listen to channel.
4. Now we can controll the same listener with different requests which are sended to '/api/streaming_logs'.
"""
class StreamingLogsRoute:
    def __init__(self):
        self.keep_listening_temp = True
        self.latest_selected_channel = None

stream_logs_route = StreamingLogsRoute()

@app.route("/api/streaming_logs", methods=["GET", "POST"]) 
def streaming_logs():

    global stream_logs_route
    selected_channel = request.args.get("channel")
    print("app.py -- selected streaming channel: ", selected_channel)

    if selected_channel == stream_logs_route.latest_selected_channel: # use if statement so the process won't be interrupted when a same channel is selected
        print("same channel is selected.")
        return json.dumps({"error": "Same channel is selected"}), 406

    else: # when first entering into chatroom or switching to another channel

        try: # when switching channels: listener.listen_to_chatroom_temp() has been executed 
            print("switching channel...")

            stream_logs_route.listener.sock.close() # need to close the socket first
            print("closed socket")

            stream_logs_route.listener.keep_listening_temp = False # then stop the while loop
            print("stopped while loop")

        except:
            pass

        if stream_logs_route.latest_selected_channel: # when switching channels
            os.remove(os.getcwd()+f"/chat_logs/{stream_logs_route.latest_selected_channel}.log")
            print(f'deleted /chat_logs/{stream_logs_route.latest_selected_channel}.log') # delete the log file after leaving the chatroom

            MongoDBManager().delete_many(stream_logs_route.latest_selected_channel, "tempChatLogs") # delete the log file of previous selected channel.
            print(f"app.py -- db.tempChatLogs.deleteMany: {stream_logs_route.latest_selected_channel}")

        else:
            pass

        if selected_channel: 
            MongoDBManager().delete_many(selected_channel, "tempChatLogs") # make sure documents of current selected channel in collection are deleted.
            print(f"app.py -- db.tempChatLogs.deleteMany: {selected_channel}")
            try: 
                os.remove(os.getcwd()+f"/chat_logs/{selected_channel}.log") # try to delete the log file of current selected channel again, too.
                print(f"app.py -- temp_delete_log_file: /chat_logs/{selected_channel}.log")
            except: 
                pass

        else:
            pass


        stream_logs_route.listener = TwitchChatListener(selected_channel) # assign current selected channel to a new listener

        stream_logs_route.latest_selected_channel = selected_channel # after doing those and before starting running, record latest_selected_channel
        print("latest_selected_channel: ", stream_logs_route.latest_selected_channel)
        
        try:
            stream_logs_route.listener.listen_to_chatroom_temp()

        except:
            event = request.args.get("event") # recogize the refresh event in order not to respond {"error": "Same channel is selected"} when refreshing
            print('event:', event)
            # print('live:', live)

            if event == None and 'live' not in vars():
                return json.dumps({"error": "Channel is offline"}), 406



def event_listener():
    """
    When javascript detecting onload or beforeunload, receive the request from js and stop the while loop and socket connection in 'streaming_logs'
    """
    event = request.args.get("event")
    print('event listener:', event)

    if event and stream_logs_route:
        try:
            stream_logs_route.listener.sock.close()
            print('closed the socket')
        except Exception as e:
            print(e)

        stream_logs_route.keep_listening_temp = False
        print('stopped the while loop')

        if stream_logs_route.latest_selected_channel:

            MongoDBManager().delete_many(stream_logs_route.latest_selected_channel, "tempChatLogs") # delete the log file of previous selected channel.
            print(f"app.py -- db.tempChatLogs.deleteMany: {stream_logs_route.latest_selected_channel}")

            try:
                os.remove(os.getcwd()+f"/chat_logs/{stream_logs_route.latest_selected_channel}.log")
                print(f'deleted /chat_logs/{stream_logs_route.latest_selected_channel}.log') # delete the log file after leaving the chatroom
                
            except:
                pass

    else:
        pass

    return 'The while loop and socket are off.'


@app.route("/api/streaming_stats", methods=["GET"]) # start querying and drawing the chart of selected channel.
def streaming_stats():
    channel = request.args.get("channel")
    analyser = ViewersReactionAnalyser(channel)
    try:
        analyser.insert_temp_chat_logs(os.getcwd()+f'/chat_logs/{channel}.log')
    except Exception as e:
        print(e, "channel seleted is offline")

        global stream_logs_route
        if stream_logs_route:
            print("trying to stop streaming_logs process...")
            try:
                stream_logs_route.listener.sock.close()
                print('closed the socket')
            except Exception as e:
                print(e)

            stream_logs_route.keep_listening_temp = False
            print('stopped the while loop')
        stream_logs_route.keep_listening_temp = False

        return json.dumps({'error': 'channel is offline'})
    stats = analyser.temp_stats(channel)
    """
    'timestamp' is in utc timezone, need to be transformed before showing on application.
    """
    for doc in stats:
        # print(doc['_id'])
        # "2023-10-10 05:00:55"
        datetime_taipei = doc['_id'] + timedelta(hours=8)
        doc['timestamp'] = datetime.timestamp(datetime_taipei)
        del doc["_id"]
    resp_data = {
    'stats' : stats
    }
    stats_json = json.dumps(resp_data)
    return stats_json


@app.route("/api/historical_data", methods=["GET"]) # query the result of selected live stream to create a chart.s
def historical_stats():
    channel = request.args.get("channel")
    started_at = request.args.get("started_at")
    print("flask historical_stats: started_at", started_at)
    if started_at: 
        started_at = started_at.replace(" ", "+") # request.args.get reads the "+" string as " "
    print("flask historical_stats: started_at", started_at)

    analyser = ViewersReactionAnalyser(channel)
    print("flask query_historical_stats: started_at", started_at)
    stats = analyser.query_historical_stats(started_at) # started_at can be None if not included in request params

    if stats == False or stats == []:
        return []
    
    def avg_sentiment_weighted_by_index(score_list):
            weighted_scores = []
            for i in range(len(score_list)):
                weighted_scores.append(score_list[i] * i)
                result = sum(weighted_scores) / sum(score_list)
            return result

    for doc in stats:
        doc['timestamp'] = datetime.timestamp(doc['timestamp']) # (utc time!!) turn bson time into unix timestamp, and convert into date using javascript.

        """
        If the historical stats have calculated the 'sentiment', then process them and pass to javascipt.
        """
        try: 
            doc['sentiment'] = avg_sentiment_weighted_by_index(doc['sentiment'])
        except:
            pass

        del doc["_id"]  

    schedule = analyser.get_historical_schedule() # startedAt time, which are in +8 timezone
    for i in range(len(schedule)):
        schedule[i] = schedule[i][:-6].replace("T", " ")

    """
    'timestamp' is in utc timezone, need to be transformed before showing on application.
    """
    resp_data = {
        'schedule': schedule,
        'stats' : stats
        }

    resp_data = json.dumps(resp_data)
    return resp_data

@app.route("/api/record_tracking_channels", methods=["GET"])
def record_tracking_channels():
    added_channel = request.args.get("added_channel")
    db = MongoDBManager()
    tracking_channels_collection = db.connect_collection("trackingChannels")
    query = [
        {
            "$sort":{"addedTime": -1}
            }, 
        {
            "$limit": 1
            }
    ]
    result = tracking_channels_collection.aggregate(query)
    current_tracking_channels = [row['channels'] for row in result][0]
    print("current_tracking_channels: ", current_tracking_channels)

    current_tracking_channels.append(added_channel)
    print("current_tracking_channels: ", current_tracking_channels)
    doc = {
        "channel": current_tracking_channels,
        "addedTime": datetime.now(),
        # "identity": "added"
    }
    tracking_channels_collection.insert_one(doc)

@app.route("/api/overview_data", methods=["GET"])
def overiew_stats():
    week = request.args.get("week")
    year = request.args.get("year")

    print(f'flask: request.args.get("week") = {week}')
    print(f'flask: request.args.get("year") = {year}')

    # now_month = datetime.now().month
    # now_date = datetime.now().day
    # now_weekday = datetime.now().weekday()
    now_week_of_year = datetime.now().isocalendar().week
    now_year = datetime.now().year

    overview = Overview()
    if week and year:
        week = int(week)
        year = int(year)
        livestream_schedule = overview.get_livestream_schedule(week, year)
    else: # when first load the page, show data this week in overviewPlot
        # week = (now_date - 1) // 7 + 1
        week = now_week_of_year
        year = now_year
        print('default week/year:', f"{week}/{year}")
        livestream_schedule = overview.get_livestream_schedule(week, year)

    return livestream_schedule
    

if __name__ == "__main__": 
    app.run(debug=True, port='8000', host='0.0.0.0') 

# debug=False, run app and update data at the same time
# if __name__ == "__main__":      
#     flask_thread = Thread(target=flask_app)
#     flask_thread.start()
#     processing_threads() # 更新user_evtn資料庫，即時更新plotly