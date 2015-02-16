from atom.auth import EndpointsAuth
from models import *


def check_user():
    """
    Checks if a UserModel exists against current OAuth token.
    Returns NULL/None if none found.
    :return: UserModel corresponding to given auth token.
    """
    user = endpoints.get_current_user()
    email = user.email()
    userqry = UserModel.query(UserModel.email == email)
    if userqry.count():
        return userqry.get()
    return None


def check_or_make():
    """
    Will return a user, or make the current user one.
    Maps to E-Mail ID.
    :return: A User, retrieved or created.
    """
    user = check_user()
    if not user:
        user = endpoints.get_current_user()
        user = UserModel(user=user,
                         email=user.email(),
                         nickname=user.nickname(),
                         id=user.user_id())
        user.put()
    return user


import gdata.data
import gdata.contacts
import gdata.contacts.client
import gdata.contacts.data


@endpoints.api(name='users_api',
               version='v1',
               description="Handle Users and Accounts for Meetups Apps.",
               audiences=[client_ids.ANDROID_AUDIENCE],  # WEB CLIENT ID
               scopes=[  # Get email and Details
                         endpoints.EMAIL_SCOPE,
                         # Get Contacts
                         client_ids.CONTACTS_SCOPE],
               allowed_client_ids=client_ids.allowed_client_ids,
               auth_level=AUTH_LEVEL.REQUIRED)
class UserApi(remote.Service):
    """
    All the API endponts for User Accounts for Meetup - WayHome app.
    """

    # Important Note: For concealed post messages (request body), we need to include a
    # messages.Message object that is well defined (serving as a jsondict). This is
    # encapsulated in a ResourceContainer.
    class FirstLoginMessage(messages.Message):
        """ JSON that contains all fields of the first message to the server. """
        name = messages.StringField(1, required=True)
        phNumber = messages.StringField(2, required=True)
        regID = messages.StringField(3, required=True)

    @endpoints.method(endpoints.ResourceContainer(FirstLoginMessage),  # Goes in
                      api_reply,  # Comes out
                      http_method='POST',
                      path='first_login',
                      name='first_login', auth_level=AUTH_LEVEL.REQUIRED)
    def first_login(self, request):
        print "login request from" + str(request)
        e_user = get_user()
        if e_user:
            print "logged in with" + str(e_user)
            if check_user():
                print str(e_user) + "already has an account"
                return api_reply(str_value="Account already exists.",
                                 int_value=2)
            user = UserModel(nickname=request.name,
                             phone=request.phNumber,
                             gcm_main=request.regID,
                             email=e_user.email(),
                             id=e_user.user_id(),
                             user=e_user)
            print "Made new user" + str(user)
            user.put()
            print "User saved"
            return api_reply(str_value="Created Account for " + user.nickname,
                             int_value=1)
        print "you're not logged in"
        return api_reply(str_value="Unauthenticated. Please login.",
                         int_value=0)


    # Todo: This takes a token different from the endpoints token (under HTTP_AUTH). Make it a POST.
    # Make endpoints_auth with that token.
    @endpoints.method(path="print_contacts",
                      name="print_contacts")
    def get_contacts(self, request):
        e_user = get_user()
        if e_user:
            gd_client = gdata.contacts.client.ContactsClient(source='<var>intense-terra-821</var>',
                                                             auth_token=EndpointsAuth())
            # all_contacts(gd_client)
            all_contacts(gd_client)
        return message_types.VoidMessage()

    @endpoints.method(message_types.VoidMessage,
                      api_reply,
                      path="ping_hello",
                      http_method="GET",
                      name="ping_hello")
    def hello_ping(self, request):
        return api_reply(str_value="Hi, received ping.", int_value=1)


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
                    print '\n%s' % (entry.name.full_name.text)
            if entry.content:
                print '    %s' % (entry.content.text)
            # Display the primary email address for the contact.
            for email in entry.email:
                if email.primary and email.primary == 'true':
                    print '    %s' % (email.address)
            # Show the contact groups that this contact is a member of.
            for group in entry.group_membership_info:
                print '    Member of group: %s' % (group.href)
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
    """A workaround implementation for getting user."""
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
    return users.User(
        email=user['email'],
        federated_provider=user['issuer'],
        _user_id=user['user_id']
    )