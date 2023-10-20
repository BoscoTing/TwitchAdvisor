from flask import render_template, request
from datetime import datetime
import re
import json
import os
import sys
sys.path.insert(0, os.getcwd())

from server import app
from managers.logging_manager import send_log
from managers.mongodb_manager import MongoDBManager

from ..services.viewers_reaction import ViewersReactionAnalyser, Overview


@app.route("/")
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
    def process_name(name):
        # Capitalize the first letter of each word and handle "lol" pattern
        name = re.sub(r'\b\w', lambda x: x.group(0).upper(), name)
        name = re.sub(r'_lol\b', ' LOL', name, flags=re.IGNORECASE)
        return name
    broadcasters = [process_name(channel) for channel in tracked_channels_list]
    """
    1. set default week number for overviewPlot.
    2. query min/max week number.
    """
    now_week_of_year = datetime.now().isocalendar().week
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


@app.route("/api/historical_data", methods=["GET"]) # query the result of selected live stream to create a chart.s
def historical_stats():
    channel = request.args.get("channel")
    started_at = request.args.get("started_at")
    # send_log(f"flask historical_stats: started_at {started_at}")
    if started_at:
        started_at = started_at.replace(" ", "+") # request.args.get reads the "+" string as " "
    # send_log(f"flask historical_stats: started_at {started_at}")

    analyser = ViewersReactionAnalyser(channel)
    # send_log(f"flask historical_stats: started_at {started_at}")
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
    # send_log(f"current_tracking_channels: {current_tracking_channels}")

    current_tracking_channels.append(added_channel)
    # send_log(f"current_tracking_channels: {current_tracking_channels}")
    doc = {
        "channel": current_tracking_channels,
        "addedTime": datetime.now()
    }
    tracking_channels_collection.insert_one(doc)

@app.route("/api/overview_data", methods=["GET"])
def overiew_stats():
    week = request.args.get("week")
    year = request.args.get("year")

    # send_log(f'flask: request.args.get("week") = {week}')
    # send_log(f'flask: request.args.get("year") = {year}')

    now_week_of_year = datetime.now().isocalendar().week
    now_year = datetime.now().year

    overview = Overview()
    if week and year:
        week = int(week)
        year = int(year)
        livestream_schedule = overview.get_livestream_schedule(week, year)
    else: # when first load the page, show data this week in overviewPlot
        week = now_week_of_year
        year = now_year
        # send_log(f"default week/year: {week}/{year}")
        livestream_schedule = overview.get_livestream_schedule(week, year)

    return livestream_schedule