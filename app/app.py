from flask import (Flask, 
                   render_template, 
                   request, 
                   )
import pytz
from datetime import datetime, timedelta
import threading
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
    broadcasters = ['SneakyLOL', 'Gosu', 'DisguisedToast', 'Scarra', 'Trick2g', 'Midbeast', 'Perkz LOL']
    # broadcasters = ['sneakylol', 'gosu', 'disguisedtoast', 'scarra', 'trick2g', 'midbeast', 'perkz_lol']
    # week_options = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']
    return render_template(
        'main.html', 
        broadcasters=broadcasters,
        # week_options=week_options
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

@app.route("/api/streaming_stats", methods=["GET"]) # start querying and drawing the chart of selected channel.
def streaming_stats():
    channel = request.args.get("channel")
    analyser = ViewersReactionAnalyser(channel)

    analyser.insert_temp_chat_logs(os.getcwd()+f'/chat_logs/{channel}.log')
    stats = ViewersReactionAnalyser(channel).temp_stats(channel)
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


request_param_lock = threading.Lock()
latest_selected_channel = None
class TwitchChatListenerTEMP(threading.Thread):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.stopped = threading.Event()

    def run(self):
        listener = TwitchChatListener(self.channel)
        listener.listen_to_chatroom_temp()
        print(f"Listening to channel: {self.channel}")
        while not self.stopped.is_set():
            listener.record_logs_temp()
            print("/api/streaming_logs: record_logs_temp")

    def stop(self):
        self.stopped.set()
# start listening to selected channel.
@app.route("/api/streaming_logs", methods=["GET"]) 
def streaming_logs():
    global latest_selected_channel # initial value is None

    selected_channel = request.args.get("channel")
    print("app.py -- selected streaming channel: ", selected_channel)

    # if selected_channel not in ['sneakylol', 'gosu', 'scarra', 'disguisedtoast', 'trick2g', 'midbeast', 'perkz_lol']:

    MongoDBManager().delete_many(selected_channel, "tempChatLogs") # delete the log file of previous selected channel.
    print(f"app.py -- db.tempChatLogs.deleteMany: {selected_channel}")

    try: 
        os.remove(os.getcwd()+f"/chat_logs/{selected_channel}.log")
        print(f"app.py -- temp_delete_log_file: /chat_logs/{selected_channel}.log")
    except: 
        pass

    with request_param_lock:     
        print("request_param_lock")       
        if selected_channel == latest_selected_channel:
            # doesn't change current process when same channel is selected.
            pass
        else: 
            latest_selected_channel = selected_channel

            # (if not the first request) stop the previous listener and assign a new one.
            if hasattr(app, 'listener_thread') and app.listener_thread.is_alive():
                print("Stop a current listener thread")
                app.listener_thread.stop()
                app.listener_thread.join()

            # Start a new listener thread
            print("Start a new listener thread")
            app.listener_thread = TwitchChatListenerTEMP(selected_channel)
            app.listener_thread.start()


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
    now_date = datetime.now().day
    # now_weekday = datetime.now().weekday()
    now_year = datetime.now().year

    overview = Overview()
    if week and year:
        week = int(week)
        year = int(year)
        livestream_schedule = overview.get_livestream_schedule(week, year)
    else: 
        week = (now_date - 1) // 7 + 1
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