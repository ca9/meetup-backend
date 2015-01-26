__author__ = 'aditya'

from protorpc import messages, remote, message_types
from google.appengine.ext import ndb

from endpoints_proto_datastore.ndb import EndpointsModel
import endpoints
import client_ids


class api_reply(messages.Message):
    """
    A standard reply. Because Proto_RPC. Yay.
    """
    str_value = messages.StringField(1)
    int_value = messages.IntegerField(2)
