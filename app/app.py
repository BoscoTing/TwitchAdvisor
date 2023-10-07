from flask import (Flask, 
                   render_template, 
                   request, 
                   redirect, 
                   url_for, 
                   jsonify)
from time import time, sleep
from datetime import datetime
from copy import deepcopy
import threading
import re
import json
import os
import sys
sys.path.insert(0, os.getcwd())

from managers.twitch_api_manager import TwitchDeveloper
from managers.ircbot_manager import TwitchChatListener
from features.viewers_reaction import ViewersReactionAnalyser
from managers.mongodb_manager import MongoDBManager

app = Flask(__name__)

@app.route("/") # main page
def main_page():
    broadcasters = ['sneakylol', 'gosu', 'disguisedtoast', 'scarra', 'trick2g', 'midbeast', 'perkz_lol']
    return render_template('main.html', broadcasters=broadcasters)

@app.route("/api/viewers_reaction", methods=["GET"])
def track_viewers_reaction(): # not in use
    channel = request.args.get("channel") # receive the channel chosen by user

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
    for doc in stats:
        doc['timestamp'] = datetime.timestamp(doc['_id'])
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
    print("selected streaming channel: ", selected_channel)

    if selected_channel not in ['sneakylol', 'gosu', 'scarra', 'disguisedtoast', 'trick2g', 'midbeast', 'perkz_lol']:

        MongoDBManager().delete_many(selected_channel, "tempChatLogs") # delete the log file of previous selected channel.
        print(f"db.tempChatLogs.deleteMany: {selected_channel}")

        try: 
            os.remove(os.getcwd()+f"/chat_logs/{selected_channel}.log")
            print(f"app: temp_delete_log_file: /chat_logs/{selected_channel}.log")

        except: pass

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

    if started_at: 
        started_at = started_at.replace(" ", "+") # request.args.get reads the "+" string as " "
    print("getting historical data: started_at", started_at)

    analyser = ViewersReactionAnalyser(channel)
    stats = analyser.query_historical_stats(started_at) # started_at can be None if not included in request params
    print("getting historical stats:", stats)

    if stats == False:
        return []
    elif stats == []:
        return stats
    
    for doc in stats:
        doc['timestamp'] = datetime.timestamp(doc['timestamp']) # (utc time!!) turn bson time into unix timestamp, and convert into date using javascript.
        del doc["_id"]  

    schedule = analyser.get_historical_schedule() # startedAt time, which are in +8 timezone
    resp_data = {
        'schedule': schedule,
        'stats' : stats
        }
    
    print(resp_data)
    # logging.debug(resp_data)
    resp_data = json.dumps(resp_data)
    return resp_data

@app.route("/historical_plot", methods=["GET"]) # query the result of selected live stream to create a chart.s
def historical_plot(): # not in use
    channel = request.args.get("channel")
    started_at = request.args.get("started_at")
    if started_at: 
        started_at = started_at.replace(" ", "+") # request.args.get reads the "+" string as " "
    print("getting historical data: started_at", started_at)
    # logging.debug("getting historical data: started_at", started_at)

    analyser = ViewersReactionAnalyser(channel)
    stats = analyser.query_historical_stats(started_at)
    if stats == False:
        # return f"We haven't seen {analyser.channel} recently."
        return []
    elif stats == []:
        return stats
    print("getting historical stats:", stats[-1])
    # logging.debug("getting historical stats:", stats[-1])
    
    for doc in stats:
        doc['timestamp'] = datetime.timestamp(doc['timestamp'])
        del doc["_id"]
    timestamps = [entry['timestamp'] for entry in stats]
    chatter_count = [entry['metadata']['chatter_count'] for entry in stats]
    message_count = [entry['metadata']['message_count'] for entry in stats]
    cheers_count = [len(entry['metadata']['cheers']) for entry in stats]
    avg_viewer_count = [ entry['metadata']['message_count'] / entry['metadata']['avg_viewer_count'] * 100 for entry in stats]

    schedule = analyser.get_historical_schedule()

    return render_template(
        'historical_plot.html',
        channel = channel,
        timestamps=timestamps,
        chatter_count=chatter_count,
        message_count=message_count,
        cheers_count=cheers_count,
        avg_viewer_count=avg_viewer_count,
        schedule = schedule
    )

if __name__ == "__main__": 
    app.run(debug=True, port='8000', host='0.0.0.0') 

# debug=False, run app and update data at the same time
# if __name__ == "__main__":      
#     flask_thread = Thread(target=flask_app)
#     flask_thread.start()
#     processing_threads() # 更新user_evtn資料庫，即時更新plotly