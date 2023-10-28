# TwitchAdvisor
Website Link: [twitch-advisor.com](twitch-advisor.com)
<p>TwitchAdvisor aims at helping users seeking advertising partnerships on Twitch, enables users to monitor chatroom reactions and review ended live streams.</p>

## Architecture
![image](https://github.com/BoscoTing/TwitchAdvisor/assets/110707173/09cd0fee-279b-4486-922a-3454030f7be2)

## Features
> Live Chat Analytics
<p>即時顯示:<p>

1. 聊天室踴躍度
2. 實況觀看人數
3. 累積付費留言數

>Historical Live Stream Stats
<p>追蹤實況主:</p>

1. 歷史開台時程
2. 歷史聊天室踴躍度

>Weekly Comparisons
<p>每週回顧追蹤實況主:</p>

1. Max Viewer Count (最高同時觀看人數)
2. Max Message Count (最高同時留言數)
3. Average Viewer Count (平均觀看人數)
4. Average Message Count (平均留言數)

## Data
### Sources
1. Twitch API
2. Twitch Chatbots
### ETL

## Tools
> Database

* Mongodb
> Data Orchestration	

* Airflow

> Backend

* Flask

> Data Visualization

* Plotly

> Monitoring

* AWS CloudWatch
