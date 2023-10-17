import logging
import boto3
import time
from decouple import config

dev_logger: logging.Logger = logging.getLogger(name='dev')
dev_logger.setLevel(logging.DEBUG)
handler: logging.StreamHandler = logging.StreamHandler()
formatter: logging.Formatter = logging.Formatter('%(name)s-%(levelname)s [%(filename)s at line %(lineno)s: %(module)s-%(funcName)s]: (%(asctime)s) %(message)s')
handler.setFormatter(formatter)
dev_logger.addHandler(handler)

client = boto3.client('logs', region_name='ap-southeast-2', aws_access_key_id=config("aws_access_key"),
                               aws_secret_access_key=config("aws_secret_access_key"))

LOG_GROUP_NAME = "/apps/CloudWatchAgentLog/"
LOG_STREAM_NAME = f"{config('ip_address')}_{config('instance_id')}"

def send_log(log_group_name, log_stream_name, log_message):
    # Getting last sequence token
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

# send_log(LOG_GROUP_NAME, LOG_STREAM_NAME, 'test')