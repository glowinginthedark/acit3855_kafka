import connexion
from connexion import NoContent
import json
import os
import yaml
import pymysql
import logging
import logging.config
import datetime
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_
from base import Base
from schedule_request import ScheduleRequest
from request import Request
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)


logger = logging.getLogger('basicLogger')


print("mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(
        app_config['datastore']['user'],
        app_config['datastore']['password'],
        app_config['datastore']['hostname'],
        app_config['datastore']['port'],
        app_config['datastore']['db']
    ))

logger.info("Connecting to DB. Hostname:" + app_config['datastore']['hostname'] + ", Port:" + str(app_config['datastore']['port']))

DB_ENGINE = create_engine(
    "mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(
        app_config['datastore']['user'],
        app_config['datastore']['password'],
        app_config['datastore']['hostname'],
        app_config['datastore']['port'],
        app_config['datastore']['db']
    )
)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def process_messages():
    """ Process event messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    
    retries = 0 

    while retries <= int(app_config['events']['max_retries']):
        try:
            logger.info("Trying to connect to kafka. try #" + str(retries + 1))
            client = KafkaClient(hosts=hostname)
            break
        except:
            logger.error("kafka connection failed.")
            time.sleep(int(app_config['events']['retry_sleep_duration']))
            retries += 1

    topic = client.topics[str.encode(app_config["events"]["topic"])]
    
    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
    reset_offset_on_start=False,
    auto_offset_reset=OffsetType.LATEST)# This is blocking - it will wait for a new message

    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]

        if msg["type"] == "boat_request":
            create_request(payload)
        elif msg["type"] == "boat_schedule_request":
            create_schedule_request(payload)

        # Commit the new message as being read
        consumer.commit_offsets()

# boat requests

def get_boat_requests(timestamp, end_timestamp):
    """ Gets boat requests created after a given time """

    session = DB_SESSION()

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    print(timestamp_datetime)

    readings = session.query(Request).filter(and_(Request.date_created >= timestamp_datetime, Request.date_created < end_timestamp_datetime))

    results_list = []

    for reading in readings:
        results_list.append(reading.to_dict())

    session.close()

    logger.info("Query boat requests after %s returns %d results" % (timestamp, len(results_list)))

    return results_list, 200

def create_request(body):
    session = DB_SESSION()

    boat_req = Request(body['user_id'],
                body['username'],
                body['timestamp'],
                body['boat_type'])

    session.add(boat_req)

    session.commit()
    session.close()

    logger.debug('Stored event create_request with a unique id of ' + body['user_id'] + body['timestamp'])

# boat schedule requests

def get_scheduled_boat_requests(timestamp, end_timestamp):
    """ Gets boat schedule requests created after a given time """

    session = DB_SESSION()

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    print(timestamp_datetime)

    readings = session.query(ScheduleRequest).filter(and_(ScheduleRequest.date_created >= timestamp_datetime, ScheduleRequest.date_created < end_timestamp_datetime))

    results_list = []

    for reading in readings:
        results_list.append(reading.to_dict())

    session.close()

    logger.info("Query scheduled boat requests after %s returns %d results" % (timestamp, len(results_list)))

    return results_list, 200


def create_schedule_request(body):
    session = DB_SESSION()

    boat_req = ScheduleRequest(body['user_id'],
                body['username'],
                body['timestamp'],
                body['boat_type'],
                body['schedule_time'])

    session.add(boat_req)

    session.commit()
    session.close()

    logger.debug('Stored event schedule_request with a unique id of ' + body['user_id'] + body['timestamp'])

flaskapp = connexion.FlaskApp(__name__, specification_dir='')
flaskapp.add_api('openapi.yaml', base_path="/storage", strict_validation=True, validate_responses=True)


if __name__=="__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    flaskapp.run(port=8090)
