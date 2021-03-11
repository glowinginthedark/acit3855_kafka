import connexion
from connexion import NoContent
import json
import os
import yaml
import logging
import logging.config
import datetime
import requests

from apscheduler.schedulers.background import BackgroundScheduler


JSON_FILE_NAME = 'data.json'

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
        'interval',
        seconds=app_config['scheduler']['period_sec'])
    sched.start()

def get_stats():
    """ retruns statistics about the boat request app """
    logger.info("Request started")
    try:
        with open(app_config['datastore']['filename']) as json_file:
            data = json.load(json_file)
    except IOError:
        logger.error("Statistics do not exist")
        return "", 404

    logger.debug(data)
    logger.info("Request complete")
    return data, 200

def populate_stats():
    """ Periodically update stats """
    logger.info("Start Periodic Processing")

    try:
        with open(app_config['datastore']['filename']) as json_file:
            data = json.load(json_file)
    except IOError:
        data = {
            "num_boat_requests": 0,
            "num_boat_schedule_requests": 0,
            "top_customer_boat_request": 0,
            "top_customer_boat_schedule_request": 0,
            "last_updated": "2021-01-18T07:17:57.615342Z"
        }

    br_url = app_config['eventstore']['url'] + '/orders/boat-request?timestamp=' + data['last_updated']
    br_response = requests.get(br_url)
    
    if br_response.status_code != 200:
        logger.error("Did not get 200 response from " + br_url)

    logger.info("Number of Boat request events received: " 
        + str(len(br_response.json())))

    bsr_url = app_config['eventstore']['url'] +  '/order/boat-schedule?timestamp=' + data['last_updated']
    bsr_response = requests.get(bsr_url)

    if bsr_response.status_code != 200:
        logger.error("Did not get 200 response from " + br_url)

    logger.info("Number of Boat schedule request events received: " 
        + str(len(bsr_response.json())))

    # stats
    data["num_boat_requests"] += len(br_response.json())
    data["num_boat_schedule_requests"] += len(bsr_response.json())

    if len(br_response.json()) > 0:
        br_user_dict = {}

        for br in br_response.json():
            if br['username'] not in br_user_dict:
                br_user_dict[br['username']] = 1
            else:
                br_user_dict[br['username']] += 1

        data["top_customer_boat_request"] = max(br_user_dict, key=br_user_dict.get)
    # else:
    #     data["top_customer_boat_request"] = "NA"

    if len(bsr_response.json()) > 0:
        bsr_user_dict = {}

        for bsr in bsr_response.json():
            if bsr['username'] not in bsr_user_dict:
                bsr_user_dict[bsr['username']] = 1
            else:
                bsr_user_dict[bsr['username']] += 1

        data["top_customer_boat_schedule_request"] = max(bsr_user_dict, key=bsr_user_dict.get)
    # else:
    #     data["top_customer_boat_schedule_request"] = "NA"

    data["last_updated"] = str(datetime.datetime.now()).replace(" ", "T") + "Z"

    with open(app_config['datastore']['filename'], 'w') as outfile:
        json.dump(data, outfile)    

    logger.debug(data)
    logger.info("End Periodic Processing")


flaskapp = connexion.FlaskApp(__name__, specification_dir='')
flaskapp.add_api('openapi.yaml', strict_validation=True, validate_responses=True)

# if __name__=="__main__":
#     flaskapp.run(port=8100)

if __name__ == "__main__":
    # run our standalone gevent server
    init_scheduler()
    flaskapp.run(port=8100, use_reloader=False)
