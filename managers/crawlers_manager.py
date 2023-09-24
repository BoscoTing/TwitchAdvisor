from bs4 import BeautifulSoup
from datetime import datetime
import json
import time
import requests
import sys
sys.path.insert(0, "/Users/surfgreen/B/AppworksSchool/projects/personal_project")

# from databases.mongodb import insert_document, connect_mongo

channel_info = {}
def get_viewers_count(channel):
    url = "https://gql.twitch.tv/gql"
    headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US
Authorization: OAuth ndxdik0vr21cnkufi345tkbtopsazl
Cache-Control: no-cache
Client-Id: kimne78kx3ncx6brgo4mv6wki5h1ko
Client-Session-Id: 1b8f60e0e8f4dc13
Client-Version: 2422581f-d61b-4550-8ffb-f5a3cc520cdb
Connection: keep-alive
Content-Length: 6755
Content-Type: text/plain;charset=UTF-8
Host: gql.twitch.tv
Origin: https://www.twitch.tv
Pragma: no-cache
Referer: https://www.twitch.tv/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-site
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36
X-Device-Id: 133135d02f62011e
sec-ch-ua: "Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "macOS"
"""
    headers = dict(i.split(": ") for i in headers.strip("\n").split("\n"))
    payloads = {"operationName":"UseViewCount","variables":{"channelLogin":""},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"00b11c9c428f79ae228f30080a06ffd8226a1f068d6f52fbc057cbde66e994c2"}}}
    payloads["variables"]['channelLogin'] = channel
    payloads = json.dumps(payloads)
    response = requests.post(url, headers=headers, data=payloads)
    resp_json = response.json()
    viewers_count = resp_json['data']['user']['stream']['viewersCount']
    channel_info[int(time.time())] = {'channel':channel, 'viewers_count': viewers_count}
    # df = pd.DataFrame({'channel':channel, 'viewers_count': viewers_count}, index=[time.time()])
    # df.index.name = "time"
    # return df
    return viewers_count

def get_active_viewers(channel):
    url = "https://gql.twitch.tv/gql"
    headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US
Authorization: OAuth ndxdik0vr21cnkufi345tkbtopsazl
Cache-Control: no-cache
Client-Id: kimne78kx3ncx6brgo4mv6wki5h1ko
Client-Integrity: v4.public.eyJjbGllbnRfaWQiOiJraW1uZTc4a3gzbmN4NmJyZ280bXY2d2tpNWgxa28iLCJjbGllbnRfaXAiOiI1OS4xMjAuMTEuMTI1IiwiZGV2aWNlX2lkIjoiMTMzMTM1ZDAyZjYyMDExZSIsImV4cCI6IjIwMjMtMDktMThUMDg6NTA6MTFaIiwiaWF0IjoiMjAyMy0wOS0xOFQwNDo1MDoxMVoiLCJpc19iYWRfYm90IjoiZmFsc2UiLCJpc3MiOiJUd2l0Y2ggQ2xpZW50IEludGVncml0eSIsIm5iZiI6IjIwMjMtMDktMThUMDQ6NTA6MTFaIiwidXNlcl9pZCI6IjExMDI1NzI2OCJ9Igqz4Xdbsyq6SBBCJ6UfOX3AZUHosT_WyMTtjQYtY-KpH-0VfgY6Z4R8-94w4QJxysC8RSTnSL21tOxBADADCw
Client-Session-Id: 13d87fcd248018f8
Client-Version: 848e3bc2-5166-4b90-9299-fea720c24767
Connection: keep-alive
Content-Length: 200
Content-Type: text/plain;charset=UTF-8
Host: gql.twitch.tv
Origin: https://www.twitch.tv
Pragma: no-cache
Referer: https://www.twitch.tv/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-site
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36
X-Device-Id: 133135d02f62011e
sec-ch-ua: "Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "macOS"
"""
    headers = dict(i.split(": ") for i in headers.strip("\n").split("\n"))
    payloads = {"operationName":"CommunityTab","variables":{"login":""},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"2e71a3399875770c1e5d81a9774d9803129c44cf8f6bad64973aa0d239a88caf"}}}
    payloads["variables"]['login'] = channel
    payloads = json.dumps(payloads)
    response = requests.post(url, headers=headers, data=payloads)
    resp_json = response.json()
    active_viewers = resp_json['data']['user']['channel']['chatters']['viewers']    
    active_viewers_list = []
    for a in active_viewers:
        active_viewer = a['login']
        active_viewers_list.append(active_viewer)
    return active_viewers_list[:20]

def get_channels():
    url = "https://www.twitch.tv/directory/category/league-of-legends"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')
    html = soup.prettify(resp)
    print(html)

get_channels()
# while True:
#     viewers_count = get_viewers_count("livekiss")
#     active_viewers = get_active_viewers("livekiss")
#     print(
#         viewers_count, 
#         active_viewers
#         )
#     time.sleep(5)
# get_viewers_count("fanta")