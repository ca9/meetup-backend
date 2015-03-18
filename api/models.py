__author__ = 'aditya'
from custom_messages import *
from oauth2client.appengine import CredentialsNDBProperty

from google.appengine.ext import ndb
from google.appengine.api import oauth, users, urlfetch
from endpoints_proto_datastore.ndb import EndpointsModel


class UserModel(EndpointsModel):
    """
    Our user model.
    """
    email = ndb.StringProperty(required=True)

    # COUGH COUGH COUGH
    # https://code.google.com/p/google-api-python-client/issues/detail?id=267
    credentials = CredentialsNDBProperty()

    # Name
    nickname = ndb.StringProperty()

    def update_name(self, name):
        self.nickname = name
        return name

    # Meetups
    meetups = ndb.KeyProperty(repeated=True, kind='Meetup')

    def add_meetup(self, a_meetup):
        self.meetups.append(a_meetup)
        self.put()
        return a_meetup

    # GCM Registration ID of Location uploading device.
    gcm_main = ndb.StringProperty()
    gcm_list = ndb.StringProperty(repeated=True)

    def add_device(self, gcm_id, main=True):
        if main:
            self.gcm_main = gcm_id
        if gcm_id not in self.gcm_list:
            self.gcm_list.append(gcm_id)
        self.put()
        return self.gcm_main

    phone = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    # Friends
    friends = ndb.KeyProperty(repeated=True, kind='UserModel')  # NDB Hack. No other way.

    def add_friend_from_email(self, email):
        friend = UserModel.query_method(UserModel.email == email).get()
        if friend and friend not in self.friends:
            self.friends.append(friend)
            self.put()
            return True
        return False

    def remove_friend_from_email(self, email):
        friend = UserModel.query_method(UserModel.email == email).get()
        if friend and friend in self.friends:
            self.friends.remove(friend)
            self.put()
            return True
        return False

        # def check_mutual(self, friend):
        # """
        # :type friend: UserModel
        #     :rtype: bool
        #     """
        #     if self.key in friend.friends and friend.key in self.friends:
        #         return True
        #     return False


class UserLocationMeetup(EndpointsModel):
    user = ndb.KeyProperty(kind="UserModel", required=True)
    locations = ndb.GeoPtProperty(repeated=True)
    last_location = ndb.GeoPtProperty()
    last_update = ndb.DateTimeProperty(auto_now=True)


class Meetup(EndpointsModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    name = ndb.StringProperty(required=True)
    active = ndb.BooleanProperty(required=True, default=True)
    owner = ndb.KeyProperty(kind='UserModel', required=True)
    destination = ndb.GeoPtProperty()
    invited_peeps = ndb.KeyProperty(kind="UserModel", repeated=True)
    # Has all the peeps and their locations.
    peeps = ndb.KeyProperty(kind="UserLocationMeetup", repeated=True)