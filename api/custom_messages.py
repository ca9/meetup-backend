__author__ = 'aditya'

from protorpc import messages, message_types


def no_user():
    """
    :rtype: SuccessMessage
    """
    return SuccessMessage(str_value="Not connected/No account found.")


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


# All profile information for user.
class ProfileMessage(messages.Message):
    """ JSON containing all profile information of the current user. """
    success = messages.MessageField(SuccessMessage, 1, required=True)

    class FriendMessage(messages.Message):
        """ JSON containing all information about friends visible to a user """
        email = messages.StringField(1)
        nickname = messages.StringField(2)
        # mutual = messages.BooleanField(3)

    class MeetupMessage(messages.Message):
        """ Json containing all information about a user's Meetups """
        name = messages.StringField(1)
        created = message_types.DateTimeField(2)

    nickname = messages.StringField(2)
    phone = messages.StringField(3)
    email = messages.StringField(4)
    friends = messages.MessageField(FriendMessage, 5, repeated=True)
    meetups = messages.MessageField(MeetupMessage, 6, repeated=True)
    created = message_types.DateTimeField(7)


class FriendsProfilesMessage(messages.Message):
    success = messages.MessageField(SuccessMessage, 1, required=True)
    profiles = messages.MessageField(ProfileMessage.FriendMessage, 2, repeated=True)

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
