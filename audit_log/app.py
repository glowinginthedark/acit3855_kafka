import connexion
from connexion import NoContent
import yaml
import logging
import logging.config
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
# import os
# import pymysql
# import datetime

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from base import Base
# from schedule_request import ScheduleRequest
# from request import Request
# from threading import Thread


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def get_boat_request(index):
    """ Get Boat request in History """
    hostname = "%s:%d" % (app_config["events"]["hostname"],
    app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Here we reset the offset on start so that we retrieve
    # messages at the beginning of the message queue.
    # To prevent the for loop from blocking, we set the timeout to
    # 100ms. There is a risk that this loop never stops if the
    # index is large and messages are constantly being received!
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
    consumer_timeout_ms=1000)
    logger.info("Retrieving boat request at index %d" % index)

    try:
        i = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if msg['type'] != 'boat_request':
                continue
            
            if i == index:
                return msg, 200
            
            i+=1

        raise Exception("No more messages found")
    except:
        logger.error("No more messages found")
        logger.error("Could not find boat_request at index %d" % index)
        return { "message": "Not Found"}, 404

def get_scheduled_boat_request(index):
    """ Get Boat schedule request in History """
    hostname = "%s:%d" % (app_config["events"]["hostname"],
    app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Here we reset the offset on start so that we retrieve
    # messages at the beginning of the message queue.
    # To prevent the for loop from blocking, we set the timeout to
    # 100ms. There is a risk that this loop never stops if the
    # index is large and messages are constantly being received!
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
    consumer_timeout_ms=1000)
    logger.info("Retrieving boat request at index %d" % index)

    try:
        i = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if msg['type'] != 'boat_schedule_request':
                continue
            
            if i == index:
                return msg, 200
            
            i+=1

        raise Exception("No more messages found")
    except:
        logger.error("No more messages found")
        logger.error("Could not find boat_request at index %d" % index)
        return { "message": "Not Found"}, 404

flaskapp = connexion.FlaskApp(__name__, specification_dir='')
flaskapp.add_api('openapi.yaml', strict_validation=True, validate_responses=True)

if __name__=="__main__":
    # t1 = Thread(target=process_messages)
    # t1.setDaemon(True)
    # t1.start()
    flaskapp.run(port=8110)
