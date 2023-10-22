```
personal_project
├─ Airflow
│  ├─ airflow.cfg
│  ├─ config
│  ├─ dags
│  │  ├─ common
│  │  └─ twitch_advisor
│  │     ├─ __pycache__
│  │     │  ├─ all_insert_stats_dags.cpython-310.pyc
│  │     │  ├─ dags_generator.cpython-310.pyc
│  │     │  ├─ generate_dags.cpython-310.pyc
│  │     │  ├─ insert_stats_dags.cpython-310.pyc
│  │     │  ├─ trigger_insert_logs_dags.cpython-310.pyc
│  │     │  └─ trigger_listen_dags.cpython-310.pyc
│  │     ├─ dags_generator.py
│  │     ├─ insert_stats_dags.py
│  │     ├─ trigger_insert_logs_dags.py
│  │     └─ trigger_listen_dags.py
│  ├─ data
│  │  └─ twitch_advisor
│  ├─ logs
│  ├─ plugins
│  │  └─ scripts
│  │     └─ twitch_advisor
│  │        ├─ __pycache__
│  │        │  ├─ channel_overview.cpython-310.pyc
│  │        │  ├─ chatroom_sentiment.cpython-310.pyc
│  │        │  ├─ ircbot_manager.cpython-310.pyc
│  │        │  ├─ logging_manager.cpython-310.pyc
│  │        │  ├─ mongodb_manager.cpython-310.pyc
│  │        │  ├─ twitch_api_manager.cpython-310.pyc
│  │        │  └─ viewers_reaction.cpython-310.pyc
│  │        ├─ channel_overview.py
│  │        ├─ ircbot_manager.py
│  │        ├─ logging_manager.py
│  │        ├─ mongodb_manager.py
│  │        ├─ twitch_api_manager.py
│  │        └─ viewers_reaction.py
│  └─ webserver_config.py
├─ App
│  ├─ __pycache__
│  │  ├─ app.cpython-310.pyc
│  │  └─ config.cpython-310.pyc
│  ├─ application.py
│  └─ server
│     ├─ __init__.py
│     ├─ __pycache__
│     │  └─ __init__.cpython-310.pyc
│     ├─ controllers
│     │  ├─ __pycache__
│     │  │  ├─ history_chart_controller.cpython-310.pyc
│     │  │  └─ realtime_chart_controller.cpython-310.pyc
│     │  ├─ history_chart_controller.py
│     │  └─ realtime_chart_controller.py
│     ├─ models
│     │  ├─ __pycache__
│     │  │  └─ mongodb_manager.cpython-310.pyc
│     │  └─ mongodb_manager.py
│     ├─ services
│     │  ├─ __pycache__
│     │  │  ├─ history_stats.cpython-310.pyc
│     │  │  ├─ realtime_stats.cpython-310.pyc
│     │  │  ├─ viewers_reaction.cpython-310.pyc
│     │  │  └─ viewers_reaction_temp.cpython-310.pyc
│     │  ├─ history_stats.py
│     │  └─ realtime_stats.py
│     ├─ static
│     │  ├─ assets
│     │  ├─ historicalPlot.js
│     │  ├─ mainPage.js
│     │  ├─ overviewPlot.js
│     │  ├─ streamingPlot.js
│     │  └─ style.css
│     ├─ templates
│     │  └─ main.html
│     └─ utils
│        ├─ __pycache__
│        │  └─ logger.cpython-310.pyc
│        ├─ logger.py
│        └─ util.py
├─ README.md
├─ docker-compose.yaml
├─ requirements.txt
└─ scheduled_dags
   └─ .cache
      └─ snowflake

```