# TwitchAdvisor
Website Link: [twitch-advisor.com](https://twitch-advisor.com)
<p>TwitchAdvisor aims at helping users seeking advertising partnerships on Twitch, enables users to monitor chatroom reactions and review ended live streams.</p>

## Architecture
![image](https://github.com/BoscoTing/TwitchAdvisor/assets/110707173/09cd0fee-279b-4486-922a-3454030f7be2)

## Features
### Live Chat Analytics
即時顯示:
1. 聊天室踴躍度
2. 實況觀看人數
3. 累積付費留言數

![Recording 2023-10-28 at 19 56 55](https://github.com/BoscoTing/TwitchAdvisor/assets/110707173/e8841a70-0d5d-4416-b417-3196969afc93)
### Historical Live Stream Stats
追蹤實況主:
1. 歷史開台時程
2. 歷史聊天室踴躍度

![Recording 2023-10-28 at 20 04 34](https://github.com/BoscoTing/TwitchAdvisor/assets/110707173/677f2801-ec89-4f2a-bd88-ca8f920ec1b0)
### Weekly Comparisons
每週回顧追蹤實況主:

1. Highest Viewer Count (最高同時觀看人數)
2. Highest Message Count (最高同時留言數)
3. Average Viewer Count (平均觀看人數)
4. Average Message Count (平均留言數)

![Recording 2023-10-28 at 20 16 36](https://github.com/BoscoTing/TwitchAdvisor/assets/110707173/1182df00-939a-43f4-9b0a-236fc910ec8f)
## Data Processing
> Extract
1. Collect data from two sources in different frequency using multithreading
    * Twitch API
    * Twitch Chatbots
2. Write data into log files

> Transform
* Parse infomation from logs
    * Live stream started time
    * Viewer count
    * Cheers
    * User name

> Load
* Insert into MongoDB time series collection

> Transform
* Aggregate data
    * Average viewer count in 5s
    * Average new message count in 5s
    * Total cheer count

## Data Orchestration
Using Airflow decorators to automatically generate DAGs and tasks for every tracked broadcasters 

>DAGs:
1. Check if broadcasters are online through Twitch API and trigger DAG runs
2. (Generated by Airflow decorators) Triggered to process data from online broadcasters' live streams
3. Insert data of ended live streams into 'chatLogs' collection
4. Aggregated documents in 'chatLogs' and insert them into 'chatStats' collection


## Tools
### Database

* Mongodb
### Data Orchestration	

* Airflow

### Backend

* Flask

### Data Visualization

* Plotly

### Monitoring

* AWS CloudWatch
