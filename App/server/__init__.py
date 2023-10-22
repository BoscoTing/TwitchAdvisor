from flask import Flask

app = Flask(__name__)

from server.controllers import history_chart_controller, realtime_chart_controller