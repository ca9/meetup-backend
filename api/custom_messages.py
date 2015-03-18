__author__ = 'aditya'

from protorpc import messages, message_types


def no_user():
    return api_reply(str_value="Not connected/No account found.")


class api_reply(messages.Message):
    """
    A standard reply. Because Proto_RPC. Yay.
    """
    str_value = messages.StringField(1)
    int_value = messages.IntegerField(2)


# Important Note: For concealed post messages (request body), we need to include a
# messages.Message object that is well defined (serving as a jsondict). This is
# encapsulated in a ResourceContainer.
class FirstLoginMessage(messages.Message):
    """ JSON that contains all fields of the first message to the server. """
    name = messages.StringField(1, required=True)
    phNumber = messages.StringField(2)
    regID = messages.StringField(3, required=True)
    ShortLivedAuthorizationToken = messages.StringField(4, required=True)


# All profile information for user.
class ProfileMessage(messages.Message):
    """ JSON containing all profile information of the current user. """

    class FriendMessage(messages.Message):
        """ JSON containing all information about friends visible to a user """
        email = messages.StringField(1)
        nickname = messages.StringField(2)
        # mutual = messages.BooleanField(3)

    class MeetupMessage(messages.Message):
        """ Json containing all information about a user's Meetups """
        name = messages.StringField(1)
        created = message_types.DateTimeField(2)

    nickname = messages.StringField(1)
    phone = messages.StringField(2)
    email = messages.StringField(3)
    friends = messages.MessageField(FriendMessage, 4, repeated=True)
    meetups = messages.MessageField(MeetupMessage, 5, repeated=True)
    created = message_types.DateTimeField(6)
    success = messages.BooleanField(7, required=True)


class FriendsMessageInd(messages.Message):
    profiles = messages.MessageField(ProfileMessage.FriendMessage, 1, repeated=True)


class UserEmailList(messages.Message):
    emails = messages.StringField(1, repeated=True)
