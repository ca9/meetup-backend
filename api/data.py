from authentication import *
from models import *


@endpoints.api(name='data_api',
               version='v1',
               description='Access, create or delete data for meetups.',
               audiences=client_ids.allowed_client_ids,
               scopes=[  # Get email and Details
                         endpoints.EMAIL_SCOPE,
                         # Get Contacts
                         client_ids.CONTACTS_SCOPE
               ])
class DataApi(remote.Service):
    """Contains all the logic to access persist data to NDB. This is the key API function."""


    @Meetup.method(path='make_meetup',
                   http_method='POST',
                   name='meetup.insert',
                   user_required=True)
    def meetup_insert(self, a_meetup):
        owner = check_or_make()
        # Create the Meetup object first
        a_meetup.owner = owner.key
        a_meetup.put()
        # Now it gets a "KEY"
        owner.add_meetup(a_meetup.key)
        return a_meetup

    @Meetup.query_method(path='meetups',
                         name='meetup.list',
                         user_required=True)
    def meetup_list(self, query):
        return query.filter(Meetup.owner == check_or_make().key)








