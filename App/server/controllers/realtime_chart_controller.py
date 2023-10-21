from flask import request
from datetime import datetime
import json
import os
import sys
sys.path.insert(0, os.getcwd())

from server import app
from ..utils.logger import send_log, dev_logger
from ..models.mongodb_manager import MongoDBManager
from ..services.realtime_stats import ViewersReactionAnalyserTEMP, TwitchChatListenerTEMP

log_path = "../static/assets/chat_logs/"

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
    dev_logger.info(selected_channel)

    if selected_channel == stream_logs_route.latest_selected_channel: # use if statement so the process won't be interrupted when a same channel is selected
        dev_logger.debug("same channel is selected.")
        return json.dumps({"error": "Same channel is selected"}), 406

    else: # when first entering into chatroom or switching to another channel

        try: # when switching channels: listener.listen_to_chatroom_temp() has been executed
            dev_logger.debug("switching channel...")

            stream_logs_route.listener.sock.close() # need to close the socket first
            dev_logger.debug("closed socket")

            stream_logs_route.listener.keep_listening_temp = False # then stop the while loop
            dev_logger.debug("stopped while loop")

        except:
            pass

        if stream_logs_route.latest_selected_channel: # when switching channels
            os.remove(os.getcwd() + f'/App/server/static/assets/chat_logs/{stream_logs_route.channel}.log')
            dev_logger.debug(os.getcwd() + f'/App/server/static/assets/chat_logs/{stream_logs_route.channel}.log')

            MongoDBManager().delete_many(stream_logs_route.latest_selected_channel, "tempChatLogs") # delete the log file of previous selected channel.
            dev_logger.debug(f"db.tempChatLogs.deleteMany: {stream_logs_route.latest_selected_channel}")


        if selected_channel:
            MongoDBManager().delete_many(selected_channel, "tempChatLogs") # make sure documents of current selected channel in collection are deleted.
            dev_logger.debug(f"app.py -- db.tempChatLogs.deleteMany: {selected_channel}")
            try:
                os.remove(os.getcwd() + f'/App/server/static/assets/chat_logs/{stream_logs_route.channel}.log') # try to delete the log file of current selected channel again, too.
                dev_logger.debug(f"app.py -- temp_delete_log_file: /chat_logs/{selected_channel}.log")
            except Exception as e :
                dev_logger.debug(e)



        stream_logs_route.listener = TwitchChatListenerTEMP(selected_channel) # assign current selected channel to a new listener

        stream_logs_route.latest_selected_channel = selected_channel # after doing those and before starting running, record latest_selected_channel
        print("latest_selected_channel: ", stream_logs_route.latest_selected_channel)

        try:
            send_log('Trying to turn on The while loop and socket.')
            dev_logger.info('Trying to turn on The while loop and socket.')
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
                os.remove(os.getcwd() + f'/App/server/static/assets/chat_logs/{stream_logs_route.channel}.log')
                print(f'deleted /chat_logs/{stream_logs_route.latest_selected_channel}.log') # delete the log file after leaving the chatroom

            except:
                pass

    else:
        pass

    send_log('The while loop and socket are turned off.')
    dev_logger.info('The while loop and socket are turned off.')
    return 'The while loop and socket are turned off.'


@app.route("/api/streaming_stats", methods=["GET"]) # start querying and drawing the chart of selected channel.
def streaming_stats():
    channel = request.args.get("channel")
    analyser = ViewersReactionAnalyserTEMP(channel)
    try:
        analyser.insert_temp_chat_logs(os.getcwd() + f'/App/server/static/assets/chat_logs/{channel}.log')
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
        datetime_taipei = doc['_id']# + timedelta(hours=8)
        doc['timestamp'] = datetime.timestamp(datetime_taipei)
        del doc["_id"]
    resp_data = {
    'stats' : stats
    }
    stats_json = json.dumps(resp_data)
    return stats_json