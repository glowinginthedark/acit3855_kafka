import connexion
from connexion import NoContent
from pykafka import KafkaClient
import json
import os
import requests
import yaml
import logging
import logging.config
import datetime


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def create_request(body):
    logger.info('Received event create_request request with a unique id of ' + body['user_id'] + body['timestamp'])

    client = KafkaClient(hosts=app_config['events']['hostname'] + ':' + str(app_config['events']['port']))
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()

    msg = {
        "type": "boat_request",
        "datetime" : datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    # res = requests.post(app_config['boat_request']['url'], json=body)
    # logger.info('Returned event create_request response with status ' + str(res.status_code) + ' and a unique id of ' + body['user_id'] + body['timestamp'])
    return "", 201

def create_schedule_request(body):
    logger.info('Received event schedule_request request with a unique id of ' + body['user_id'] + body['timestamp'])

    client = KafkaClient(hosts=app_config['events']['hostname'] + ':' + str(app_config['events']['port']))
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()

    msg = {
        "type": "boat_schedule_request",
        "datetime" : datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    # res = requests.post(app_config['schedule_request']['url'], json=body)
    # logger.info('Returned event schedule_request response with status ' + str(res.status_code) + ' and a unique id of ' + body['user_id'] + body['timestamp'])
    # return (res.text, res.status_code)
    return "", 201

flaskapp = connexion.FlaskApp(__name__, specification_dir='')
flaskapp.add_api('openapi.yaml', strict_validation=True, validate_responses=True)

if __name__=="__main__":
    flaskapp.run(port=8080)
