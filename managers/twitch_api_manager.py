from decouple import config
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
        
    def get_channel_info(self, channel):
        url = f'https://api.twitch.tv/helix/streams?user_login={channel}'
        headers = {
            'Client-ID' : config('twitch_app_id'),
            'Authorization' :  "Bearer " + self.get_token()
        }
        resp = requests.get(url, headers=headers).json()['data']
        if resp:
            return resp[0]
        else:
            return False

# use_example

# twitch_api = TwitchDeveloper()
# channels = twitch_api.search_channels()
# print(channels['League of Legends'])