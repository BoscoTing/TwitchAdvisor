from flask import (Flask, 
                   render_template, 
                   request, 
                   redirect, 
                   url_for, 
                   jsonify)
from time import time, sleep
from datetime import datetime
import logging
import re
import json
import os
import sys
sys.path.insert(0, os.getcwd())
import argparse
parser = argparse.ArgumentParser()
parser.add_argument( '-log',
                     '--loglevel',
                     default='warn',
                     help='Provide logging level. Example --loglevel debug, default=warning' )
args = parser.parse_args()
logging.basicConfig( level=args.loglevel.upper() )

from managers.twitch_api_manager import TwitchDeveloper
from managers.ircbot_manager import TwitchChatListener
from features.viewers_reaction import ViewersReactionAnalyser

app = Flask(__name__)

@app.route("/") # main page
def main_page():
    broadcasters = ['sneakylol', 'gosu', 'disguisedtoast', 'scarra']
    return render_template('main.html', broadcasters=broadcasters)

@app.route("/api/viewers_reaction", methods=["GET"])
def track_viewers_reaction():
    channel = request.args.get("channel") # receive the channel chosen by user
    # Airflow Dag of TwitchChatListener:
    #   a existing DAG still tracking default channels.
    #   another DAG will be triggered to execute a new script that is ready for tracking new channel.

    # Airflow Dag of ViewersReactionAnalyser: 
    #   a existing DAG still tracking the log messages of default channel.
    #   another DAG will be triggered to execute a new script that is parsing the log messages of selected channel.

    # listener = TwitchChatListener(channel)

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
            renamed_channel_dict[renamed_key] = value
            data = {'data': renamed_channel_dict}

        channel_json = json.dumps(data)
        return channel_json

@app.route("/api/streaming_logs", methods=["GET"]) # start listening to selected channel and insert document into collection
def streaming_plot():
    channel = request.args.get("channel")
    listener = TwitchChatListener(channel)
    listener.listen_to_chatroom_temp()
    while True:
        listener.record_logs_temp()
            
@app.route("/api/streaming_stats", methods=["GET"]) # start querying and drawing the chart of selected channel.
def streaming_stats():
    channel = request.args.get("channel")
    analyser = ViewersReactionAnalyser(channel)
    analyser.insert_temp_chat_logs(os.getcwd() + f'/chat_logs/{channel}.log')
    stats = ViewersReactionAnalyser(channel).temp_stats(channel)
    for doc in stats:
        doc['timestamp'] = datetime.timestamp(doc['_id'])
        del doc["_id"]
    logging.warning(stats)
    resp_data = {
    'stats' : stats
    }
    stats_json = json.dumps(resp_data)
    return stats_json

@app.route("/api/historical_data", methods=["GET"]) # query the result of selected live stream to create a chart.s
def historical_stats():
    channel = request.args.get("channel")
    started_at = request.args.get("started_at")
    if started_at: 
        started_at = started_at.replace(" ", "+") # request.args.get reads the "+" string as " "
    logging.warning("getting historical data: started_at", started_at)

    analyser = ViewersReactionAnalyser(channel)
    stats = analyser.query_historical_stats(started_at)
    if stats == False or stats == []:
        return f"We haven't seen {analyser.channel} recently."
    logging.warning("getting historical stats:", stats[-1])
    
    for doc in stats:
        doc['timestamp'] = datetime.timestamp(doc['timestamp'])
        del doc["_id"]  

    schedule = analyser.get_historical_schedule()
    resp_data = {
        'shedule': schedule,
        'stats' : stats
        }
    resp_data = json.dumps(resp_data)
    return resp_data

@app.route("/historical_plot", methods=["GET"]) # query the result of selected live stream to create a chart.s
def historical_plot():
    channel = request.args.get("channel")
    started_at = request.args.get("started_at")
    if started_at: 
        started_at = started_at.replace(" ", "+") # request.args.get reads the "+" string as " "
    logging.warning("getting historical data: started_at", started_at)

    analyser = ViewersReactionAnalyser(channel)
    stats = analyser.query_historical_stats(started_at)
    if stats == False or stats == []:
        return f"We haven't seen {analyser.channel} recently."
    logging.warning("getting historical stats:", stats[-1])
    
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
