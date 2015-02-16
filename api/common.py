__author__ = 'aditya'

from protorpc import messages, remote, message_types
from google.appengine.ext import ndb
from google.appengine.api import oauth, users, urlfetch

from endpoints_proto_datastore.ndb import EndpointsModel
from endpoints import AUTH_LEVEL
import endpoints
import client_ids
import os
import json
import time

class api_reply(messages.Message):
    """
    A standard reply. Because Proto_RPC. Yay.
    """
    str_value = messages.StringField(1)
    int_value = messages.IntegerField(2)
