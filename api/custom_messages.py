__author__ = 'aditya'

from protorpc import messages, message_types


def no_user():
    """
    :rtype: SuccessMessage
    """
    return SuccessMessage(str_value="Not connected/No account found.", int_value=0)


def success():
    """
    :rtype SuccessMessage
    """
    return SuccessMessage(str_value="Success", int_value=1)


class SuccessMessage(messages.Message):
    """
    A standard reply. Because Proto_RPC. Yay.
    """
    str_value = messages.StringField(1, default="Failed!")
    int_value = messages.IntegerField(2, default=0)


class MeetupMessage(messages.Message):
    """ Json containing Meetup Description """
    name = messages.StringField(1, required=True)
    owner = messages.StringField(2, required=True)
    active = messages.BooleanField(3)
    created = message_types.DateTimeField(4)


# All profile information for user.
class ProfileMessage(messages.Message):
    """ JSON containing all profile information of the current user. """
    success = messages.MessageField(SuccessMessage, 1, required=True)

    class FriendMessage(messages.Message):
        """ JSON containing all information about friends visible to a user """
        email = messages.StringField(1)
        nickname = messages.StringField(2)
        # mutual = messages.BooleanField(3)

    nickname = messages.StringField(2)
    phone = messages.StringField(3)
    email = messages.StringField(4)
    friends = messages.MessageField(FriendMessage, 5, repeated=True)
    meetups = messages.MessageField(MeetupMessage, 6, repeated=True)
    created = message_types.DateTimeField(7)
    home_lat = messages.FloatField(8)
    home_lon = messages.FloatField(9)


class FriendsProfilesMessage(messages.Message):
    success = messages.MessageField(SuccessMessage, 1, required=True)
    profiles = messages.MessageField(ProfileMessage.FriendMessage, 2, repeated=True)


class MeetupDescMessage(messages.Message):
    """ Describes a Meetup.
    """
    success = messages.MessageField(SuccessMessage, 1, required=True)
    owner = messages.StringField(2)
    name = messages.StringField(3)
    pending = messages.MessageField(ProfileMessage.FriendMessage, 4, repeated=True)
    accepted = messages.MessageField(ProfileMessage.FriendMessage, 5, repeated=True)
    lon_destination = messages.FloatField(6)
    lat_destination = messages.FloatField(7)
    time_to_arrive = message_types.DateTimeField(8)
    created = message_types.DateTimeField(9)


class MeetupListMessage(messages.Message):
    """ List of meetups. """
    success = messages.MessageField(SuccessMessage, 1, required=True)
    meetups = messages.MessageField(MeetupMessage, 2, repeated=True)

##################################
"""
Location Heartbeats
"""
##################################

class LocationMessage(messages.Message):
    lat = messages.FloatField(1, required=True)
    lon = messages.FloatField(2, required=True)
    time = message_types.DateTimeField(3)


class PeepLocationsMessage(messages.Message):
    latest_location = messages.MessageField(LocationMessage, 1, required=True)
    locations = messages.MessageField(LocationMessage, 2, repeated=True)
    name = messages.StringField(3, required=True)
    email = messages.StringField(4, required=True)


class MeetupLocationsUpdateFullMessage(messages.Message):
    success = messages.MessageField(SuccessMessage, 1, required=True)
    UserMeetupLocations = messages.MessageField(PeepLocationsMessage, 2, repeated=True)


"""
Should go in the list below
"""


class UpLocationMessage(messages.Message):
    lat = messages.FloatField(1, required=True)
    lon = messages.FloatField(2, required=True)
    meetup_name = messages.StringField(3)
    meetup_owner = messages.StringField(4)
    details = messages.BooleanField(5, default=False)


##################################
"""
Upstream Messages below this point.
"""
##################################


# Important Note: For concealed post messages (request body), we need to include a
# messages.Message object that is well defined (serving as a jsondict). This is
# encapsulated in a ResourceContainer.
class UpFirstLoginMessage(messages.Message):
    """ JSON that contains all fields of the first message to the server. """
    name = messages.StringField(1, required=True)
    phNumber = messages.StringField(2)
    regID = messages.StringField(3, required=True)
    ShortLivedAuthorizationToken = messages.StringField(4, required=True)


class UpUserEmailsMessage(messages.Message):
    emails = messages.StringField(1, repeated=True)


class UpMeetupCreateMessage(messages.Message):
    name = messages.StringField(1, required=True)
    lat = messages.FloatField(2, required=True)
    lon = messages.FloatField(3, required=True)

    invited = messages.StringField(4, repeated=True)  # Can't be required.
    timeToArrive = message_types.DateTimeField(5)


class UpMeetupMessageSmall(messages.Message):
    owner = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)


##################################
"""
End of upstream messages.
"""
##################################
