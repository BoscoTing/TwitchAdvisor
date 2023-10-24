import logging
import requests
from decouple import config
from datetime import datetime, timedelta
logging.basicConfig(level=logging.ERROR)

class TwitchDeveloper():
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