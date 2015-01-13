import endpoints
from google.appengine.ext import ndb
from protorpc import remote

from endpoints_proto_datastore.ndb import EndpointsModel


class UserModel(EndpointsModel):
    """
    The default user model.
    """
    email = ndb.StringProperty()
    nickname = ndb.StringProperty()
    meetups = ndb.IntegerProperty(repeated=True)

    def add_meetup(self, a_meetup):
        self.meetups.append(a_meetup.id)


class Meetup(EndpointsModel):
    created = ndb.DateTimeProperty(auto_now_add=True)
    owner = ndb.IntegerProperty()


def check_or_make():
    """
    The holy grail of authentication. Will return a user, or make the current user one.
    Maps to E-Mail ID.
    :return: A User, retrieved or created.
    """
    user = endpoints.get_current_user()
    email = user.email()
    userqry = UserModel.query(UserModel.email == email)
    if userqry.count():
        return userqry.get()
    user = UserModel(email=user.email(),
                     nickname=user.nickname())
    user.put()
    return user


@endpoints.api(name='data_api',
               version='v1',
               description='Access, create or delete data for meetups.',
               audiences=[endpoints.API_EXPLORER_CLIENT_ID])
class DataApi(remote.Service):
    """ Contains all the logic to access persist data to NDB. This is the key API function.
    """

    @UserModel.method(path='check_make_user', name='user.fetch',
                      user_required=True)
    def check_or_make_user(self, query):
        return check_or_make()


    @Meetup.method(path='make_meetup', http_method='POST', name='meetup.insert',
                   user_required=True)
    def meetup_insert(self, a_meetup):
        owner = check_or_make()
        # Create the Meetup object first
        a_meetup.owner = owner.id
        a_meetup.put()  # Now it gets a "KEY"
        owner.add_meetup(a_meetup)
        return a_meetup

    @Meetup.query_method(path='meetups', name='meetup.list',
                         user_required=True)
    def meetup_list(self, query):
        return query.filter(Meetup.owner == check_or_make())







