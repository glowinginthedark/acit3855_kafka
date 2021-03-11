from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class Request(Base):
    """ Request """

    __tablename__ = "request"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(250), nullable=False)
    username = Column(String(250), nullable=False)
    timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)
    boat_type = Column(String(100), nullable=False)

    def __init__(self, user_id, username, timestamp, boat_type):
        """ Initializes a boat request """
        self.user_id = user_id
        self.username = username
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now() # Sets the date/time record is created
        self.boat_type = boat_type

    def to_dict(self):
        """ Dictionary Representation of a request """
        dict = {}
        dict['id'] = self.id
        dict['user_id'] = self.user_id
        dict['username'] = self.username
        dict['boat_type'] = self.boat_type
        dict['timestamp'] = self.timestamp
        dict['date_created'] = self.date_created

        return dict