from flask import (Flask, 
                   render_template, 
                   request, 
                   redirect, 
                   url_for, 
                   jsonify)
from time import time
import re
import json
import os
import sys
sys.path.insert(0, os.getcwd())

from managers.twitch_api_manager import TwitchDeveloper
app = Flask(__name__)

# main page
@app.route("/")
def main_page():
    return render_template('main_page.html')

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

debug=True
if __name__ == "__main__": 
    app.run(debug=True, port='8000', host='0.0.0.0') 

# debug=False, run app and update data at the same time
# if __name__ == "__main__":      
#     flask_thread = Thread(target=flask_app)
#     flask_thread.start()
#     processing_threads() # 更新user_evtn資料庫，即時更新plotly
