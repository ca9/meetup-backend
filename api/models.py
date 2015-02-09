__author__ = 'aditya'
from common import *


class UserModel(EndpointsModel):
    """
    The default user model.
    """
    user = ndb.UserProperty()
    email = ndb.StringProperty(required=True)

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

    # Friends
    friends = ndb.KeyProperty(repeated=True, kind='UserModel')  # NDB Hack. No other way.

    def add_friend(self, friend):
        if friend not in self.friends:
            self.friends.append(friend)
            self.put()
            return self.friends
        return


class Meetup(EndpointsModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    owner = ndb.KeyProperty(kind='UserModel')
    destination = ndb.GeoPtProperty()