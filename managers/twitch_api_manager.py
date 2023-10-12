from decouple import config
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.ERROR)
import pytz
import requests
import json

class TwitchDeveloper:
    def __init__(self):
        self.client_id = config('twitch_app_id')
        self.secret = config('twitch_app_secret')

    def get_token(self):
        auth_params = {
            'client_id': config('twitch_app_id'),
            'client_secret': config('twitch_app_secret'),
            'grant_type': 'client_credentials'
        }
        auth_url = 'https://id.twitch.tv/oauth2/token'
        auth_request = requests.post(url=auth_url, params=auth_params) 
        access_token = auth_request.json()['access_token']
        return access_token
    
    def search_channels(self):
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        query = "type=live&language=en&first=100"
        url = f'https://api.twitch.tv/helix/streams?{query}'
        resp = requests.get(url, headers=headers).json()['data']
        # print(resp[0:20])

        channel_dict = {
            'Just Chatting': [],
            'League of Legends': [],
            'Music': []
        }
        if resp:
            for channel in resp:
                if channel['game_name'] in ['League of Legends', 'Just Chatting', 'Music']:
                    game_name = channel['game_name']
                    channel_name = channel['user_login']
                    channel_dict[game_name].append(channel_name)
        else:
            return False
        
        return channel_dict
        
    def detect_living_channel(self, channel):
        
        url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp_data = requests.get(url, headers=headers).json()['data']

        if resp_data:
            """
            turn startedAt into +8 timezone. 
            startedAt will be recorded in log file and then inserted into chatLogs collection.
            """
            taipei_time = datetime.fromisoformat(resp_data[0]['started_at'][:-1]) + timedelta(hours=8)
            taipei_isoformat = datetime.isoformat(taipei_time) + "+08:00"
            resp_data[0]['started_at'] = taipei_isoformat
            logging.info(resp_data[0])
            return resp_data[0]
        
        else:
            return False
        
    def get_total_viewers(self, channel):
        
        url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp_data = requests.get(url, headers=headers).json()['data']

        if resp_data:
            return resp_data[0]['viewer_count']
        
        else:
            return False
    
    def get_broadcaster_id(self, channel):
        url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp_data = requests.get(url, headers=headers).json()['data']
        if resp_data:
            return resp_data[0]['user_id']
        else:
            return False
        
    def get_channel_schedule(self, channel):
        broadcaster_id = self.get_broadcaster_id(channel)
        print(broadcaster_id)
        url = f"https://api.twitch.tv/helix/schedule?broadcaster_id={broadcaster_id}"
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp_data = requests.get(url, headers=headers).json()#['data']
        if resp_data:
            return resp_data#[0]
        else:
            return False
# use_example

# twitch_api = TwitchDeveloper()
# result = twitch_api.detect_living_channel("trick2g")
# print(result)