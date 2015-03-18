import httplib2, random
from endpoints_proto_datastore.ndb import EndpointsUserProperty
import oauth2client
from oauth2client.appengine import StorageByKeyName
from oauth2client.client import OAuth2WebServerFlow
from atom.auth import EndpointsAuth, GDataAuth
from models import *
from uuid import *

from endpoints import AUTH_LEVEL
import endpoints
import client_ids
import os
import json
from protorpc import remote
import time


developers = ("aditya11009@iiitd.ac.in", "vedant12118@iiitd.ac.in", "shubham12101@iiitd.ac.in")


def check_user():
    """
    Checks if a UserModel exists against current OAuth token.
    Returns NULL/None if none found.
    :return: UserModel corresponding to given auth token.
    :rtype: UserModel
    """
    try:
        user = get_user()
        email = user.email()
        userqry = UserModel.query(UserModel.email == email)
        if userqry.count():
            return userqry.get()
    except Exception as e:
        print e.args, e.message
    return None


import gdata.data
import gdata.contacts
import gdata.contacts.client
import gdata.contacts.data


@endpoints.api(name='users_api',
               version='v2',
               description="Handle Users and Accounts for Meetups Apps.",
               audiences=[client_ids.ANDROID_AUDIENCE],  # WEB CLIENT ID
               scopes=[  # Get email and Details
                         endpoints.EMAIL_SCOPE,
                         # Get Contacts
                         client_ids.CONTACTS_SCOPE, client_ids.CONTACTS_SCOPE2],
               allowed_client_ids=client_ids.allowed_client_ids,
               auth_level=AUTH_LEVEL.REQUIRED)
class UserApi(remote.Service):
    """
    All the API endponts for User Accounts for Meetup - WayHome app.
    """

    @endpoints.method(endpoints.ResourceContainer(UpFirstLoginMessage),  # Goes in
                      SuccessMessage,  # Comes out
                      http_method='POST',
                      path='first_login',
                      name='first_login', auth_level=AUTH_LEVEL.REQUIRED)
    def first_login(self, request):
        e_user = get_user()
        # Only time get_user is directly called, check_user is bypassed. Check_user checks DB.
        if e_user:
            if check_user():
                print str(e_user) + "already has an account"
                return SuccessMessage(str_value="Account already exists.",
                                      int_value=2)
            user = UserModel(id=e_user.user_id(),
                             nickname=request.name,
                             phone=request.phNumber,
                             gcm_main=request.regID,
                             email=e_user.email())
            flow = OAuth2WebServerFlow(client_id=client_ids.WEB_CLIENT_ID,
                                       client_secret=client_ids.CLIENT_SECRET,
                                       scope=client_ids.CONTACTS_SCOPE + " " + endpoints.EMAIL_SCOPE,
                                       redirect_uri='urn:ietf:wg:oauth:2.0:oob',
                                       grant_type='authorization_code')
            credentials = flow.step2_exchange(request.ShortLivedAuthorizationToken)
            if credentials:
                user.put()
                # https://developers.google.com/api-client-library/python/guide/google_app_engine
                storage = StorageByKeyName(UserModel, user.key.id(), 'credentials')
                storage.put(credentials)
            return SuccessMessage(str_value="Created Account for " + user.nickname, int_value=1)
        return no_user()

    @endpoints.method(endpoints.ResourceContainer(value=messages.StringField(1, required=True),
                                                  item=messages.StringField(2, required=True)),
                      SuccessMessage,
                      http_method="GET",
                      path="change_item",
                      name="change_item", auth_level=AUTH_LEVEL.REQUIRED)
    def change_item(self, request):
        user = check_user()
        if user:
            if request.item == "nickname":
                user.update_name(request.value)
                user.put()
            elif request.item == "phone":
                user.phone = request.value.replace(" ", "").replace("-", '')
                user.put()
            else:
                return SuccessMessage(str_value="Cannot access " + request.item)
            return SuccessMessage(str_value=request.item + " changed to " + request.value, int_value=1)
        return no_user()

    @endpoints.method(response_message=ProfileMessage, http_method="GET",
                      path="get_profile",
                      name="get_profile",
                      auth_level=AUTH_LEVEL.REQUIRED)
    def get_profile(self, request):
        user = check_user()
        if user:
            response = ProfileMessage(success=success(),
                                      nickname=user.nickname,
                                      phone=user.phone,
                                      email=user.email,
                                      created=user.created)
            friends_list, friends = ndb.get_multi(user.friends), []
            for friend in friends_list:
                friends.append(ProfileMessage.FriendMessage(email=friend.email,
                                                            nickname=friend.nickname))
            meetups_list, meetups = ndb.get_multi(user.meetups), []
            for meetup in meetups_list:
                meetups.append(ProfileMessage.MeetupMessage(name=meetup.name, created=meetup.created))
            response.friends = friends
            response.meetups = meetups
            return response
        return ProfileMessage(success=no_user())

    @endpoints.method(endpoints.ResourceContainer(email=messages.StringField(1, required=True),
                                                  add=messages.BooleanField(2, required=True, default=True)),
                      SuccessMessage,
                      http_method="GET", name="add_remove_friend_by_email", path="add_remove_friend_by_email",
                      auth_level=AUTH_LEVEL.REQUIRED)
    def add_remove_friend_by_email(self, request):
        user = check_user()
        if user:
            if request.add:
                success_edit = user.add_friend_from_email(request.email)
                if success_edit:
                    return SuccessMessage(str_value=request.email + " added as friend!", int_value=1)
            else:
                success_edit = user.remove_friend_from_email(request.email)
                if success_edit:
                    return SuccessMessage(str_value=request.email + " removed as friend!", int_value=1)
            return SuccessMessage(str_value=request.email + " not found!")
        return no_user()

    @endpoints.method(UpUserEmailsMessage,
                      SuccessMessage, http_method="POST", name="bulk_add", path="bulk_add")
    def add_friends_bulk(self, request):
        """
        Accepts a list of user-emails, each of which get added to your friends (two-way).

        :type request: UpUserEmailsMessage
        """
        user = check_user()
        if user:
            response = SuccessMessage(int_value=1, str_value="")
            for email in request.emails:
                response.str_value += user.add_friend_from_email(email) + ", "
            return response
        return no_user()

    @endpoints.method(response_message=FriendsProfilesMessage,
                      auth_level=AUTH_LEVEL.REQUIRED, name='create_dummies', path="create_dummies")
    def create_dummies(self, request):
        user = check_user()
        if user and user.email.lower() in developers:
            n1 = ('woody', 'buzz', 'jessie', 'rex', 'potato', 'sid')
            n2 = ('walle', 'eve', 'axiom', 'captain', 'beta')
            n3 = ('aldrin', 'mik', 'jagger', 'romeo', 'charlie')
            profiles = []
            for i in range(5):
                name = '-'.join([random.choice(n1), random.choice(n2), random.choice(n3)])
                email = name + "@example.com"
                dummy = UserModel(id=email, nickname=name,
                                  phone=str(int(random.random() * (10 ** 10))),
                                  gcm_main=str(uuid4()),
                                  email=email)
                dummy.put()
                profiles.append(ProfileMessage.FriendMessage(email=email, nickname=name))
                if random.random() > 0.5:
                    dummy.friends.append(user.key)
                    user.friends.append(dummy.key)
                user.put()
                dummy.put()
            return FriendsProfilesMessage(success=success(), profiles=profiles)
        return FriendsProfilesMessage(success=no_user())

    @endpoints.method(response_message=FriendsProfilesMessage,
                      path="refresh_contacts",
                      name="refresh_contacts")
    def refresh_contacts(self, request):
        """ Returns (email list of) people you know but havent added on Meetup (from google contacts),
            and adds them to your contacts (if they have an account).
        """
        user_model = check_user()
        if user_model:
            storage = StorageByKeyName(UserModel, user_model.key.id(), 'credentials')
            credentials = storage.get()
            credentials.refresh(httplib2.Http())
            gd_client = gdata.contacts.client.ContactsClient(source='<var>intense-terra-821</var>',
                                                             auth_token=GDataAuth(credentials.access_token))
            # all_contacts(gd_client)
            found_friends = find_users(gd_client)
            old_friends = ndb.get_multi(user_model.friends)
            new_friends = [friend for friend in found_friends if friend not in old_friends and friend != user_model]
            for friend in new_friends:
                friend.friends.append(user_model)
                user_model.friends.append(friend)
            return FriendsProfilesMessage(success=success(), profiles=[
                ProfileMessage.FriendMessage(email=friend.email, nickname=friend.nickname) for friend in new_friends
            ])
        return FriendsProfilesMessage(success=no_user())

    @endpoints.method(response_message=FriendsProfilesMessage,
                      path="get_friends",
                      name="get_friends")
    def get_friends(self, request):
        """ Returns your friends' profiles.
        """
        user_model = check_user()
        if user_model:
            return FriendsProfilesMessage(profiles=[ProfileMessage.FriendMessage(email=friend.email,
                                                                                 nickname=friend.nickname)
                                                    for friend in ndb.get_multi(user_model.friends)])
        return FriendsProfilesMessage(profiles=[ProfileMessage.FriendMessage(email="unauthenticated",
                                                                             nickname="unauthenticated")])

    @endpoints.method(message_types.VoidMessage,
                      SuccessMessage,
                      path="ping_hello",
                      http_method="GET",
                      name="ping_hello")
    def hello_ping(self, request):
        return SuccessMessage(str_value="Hi, received ping.", int_value=1)


def find_users(gd_client):
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 1000
    feed = gd_client.GetContacts(q=query)
    contacts, snumbers, semails = [], [], []
    for i, entry in enumerate(feed.entry):
        name, numbers, emails = "", [], []
        try:
            if entry.name:
                name = entry.name.full_name.text
            for email in entry.email:
                emails.append(email.address)
                semails.append(email.address)
            for number in entry.phone_number:
                form_num = str(number.text).replace(" ", "").replace("-", '')
                numbers.append(form_num)
                snumbers.append(form_num)
            if len(emails) or len(numbers):
                contacts.append((name, numbers, emails))
        except Exception as e:
            print e
    match_numbers = UserModel.query(UserModel.phone.IN(snumbers)).fetch()
    match_emails = UserModel.query(UserModel.email.IN(semails)).fetch()
    return match_emails + match_numbers


def all_contacts(gd_client):
    """
    Takes an authentication gdata client and prints all contacts neatly.
    :param gd_client: gdata client object with authentication token thrown in.
    :return: Null.
    """
    query = gdata.contacts.client.ContactsQuery()
    # updated_min = '2008-01-01'
    # query.updated_min = updated_min
    query.max_results = 1500
    feed = gd_client.GetContacts(q=query)
    for i, entry in enumerate(feed.entry):
        print "Contact {0} + {1}".format(i, '*' * 50)
        try:
            if entry.name:
                if entry.name.full_name:
                    print '\n%s' % entry.name.full_name.text
            if entry.content:
                print '    %s' % entry.content.text
            # Display the primary email address for the contact.
            for email in entry.email:
                if email.primary and email.primary == 'true':
                    print '    %s' % email.address
            # Show the contact groups that this contact is a member of.
            for group in entry.group_membership_info:
                print '    Member of group: %s' % group.href
            # Display extended properties.
            for extended_property in entry.extended_property:
                if extended_property.value:
                    value = extended_property.value
                else:
                    value = extended_property.GetXmlBlob()
                print '    Extended Property - %s: %s' % (extended_property.name, value)
        except Exception as e:
            print e


# https://code.google.com/p/googleappengine/issues/detail?id=8848
# https://code.google.com/p/googleappengine/issues/detail?id=10753
def get_user():
    """A workaround implementation for getting user.
    """
    auth = os.getenv('HTTP_AUTHORIZATION')
    bearer, token = auth.split()
    token_type = 'id_token'
    if 'OAUTH_USER_ID' in os.environ:
        token_type = 'access_token'
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?%s=%s'
           % (token_type, token))
    user = {}
    wait = 1
    for i in range(3):
        resp = urlfetch.fetch(url)
        if resp.status_code == 200:
            user = json.loads(resp.content)
            break
        elif resp.status_code == 400 and 'invalid_token' in resp.content:
            url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?%s=%s'
                   % ('access_token', token))
        else:
            time.sleep(wait)
            wait += i
    ret_user = users.User(
        email=user['email'],
        _user_id=user['user_id']
    )
    if "issuer" in user:
        ret_user.__federated_identity = user['issuer']
    return ret_user
