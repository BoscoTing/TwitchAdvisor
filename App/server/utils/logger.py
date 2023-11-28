import logging
import boto3
import time
from decouple import config

dev_logger = logging.getLogger(name='dev')
dev_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('App/server/flask_app.log')
formatter = logging.Formatter('%(name)s-%(levelname)s [%(filename)s at line %(lineno)s: %(module)s-%(funcName)s]: (%(asctime)s) %(message)s')
file_handler.setFormatter(formatter)
dev_logger.addHandler(file_handler)


client = boto3.client('logs', region_name='ap-southeast-2', aws_access_key_id=config("aws_access_key"),
                               aws_secret_access_key=config("aws_secret_access_key"))


def send_log(log_message):
    log_group_name = "/apps/CloudWatchAgentLog/"
    log_stream_name = f"{config('ip_address')}_{config('instance_id')}"
    response = client.describe_log_streams(logGroupName=log_group_name,
                                           logStreamNamePrefix=log_stream_name)

    log_event = {
        'logGroupName': log_group_name,
        'logStreamName': log_stream_name,
        'logEvents': [
            {
                'timestamp': int(round(time.time() * 1000)),
                'message': log_message
            },
        ],
    }

    #Adding last sequence token to log event before sending logs if it exists
    if 'uploadSequenceToken' in response['logStreams'][0]:
        log_event.update(
            {'sequenceToken': response['logStreams'][0]['uploadSequenceToken']})

    print("logs to send : ", log_event)
    response = client.put_log_events(**log_event)
    time.sleep(1)
    print("Response : ", response)