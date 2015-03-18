from authentication import *
from models import *


@endpoints.api(name='data_api',
               version='v1',
               description='Access, create or delete data for meetups.',
               audiences=[client_ids.ANDROID_AUDIENCE],  # WEB CLIENT ID
               scopes=[  # Get email and Details
                         endpoints.EMAIL_SCOPE,
                         # Get Contacts
                         client_ids.CONTACTS_SCOPE, client_ids.CONTACTS_SCOPE2],
               allowed_client_ids=client_ids.allowed_client_ids,
               auth_level=AUTH_LEVEL.REQUIRED)
class DataApi(remote.Service):
    """Contains all the logic to access persist data to NDB. This is the key API function."""


    @endpoints.method(UpMeetupCreateMessage,
                      SuccessMessage,
                      http_method="POST",
                      path='make_meetup',
                      name='make_meetup')
    def meetup_insert(self, request):
        """
        Creates a meetup item (v1 - cannot be undone).
        :type request: UpMeetupCreateMessage
        """
        user = check_user()
        if user:
            try:
                destination = ndb.GeoPt(lat=request.lat, lon=request.lon)
            except Exception as e:
                return SuccessMessage(str_value=e.message, int_value=0)
            sim = Meetup.query(Meetup.owner == user.key, Meetup.name == request.name).fetch()
            if len(sim):
                return SuccessMessage(str_value="Meetup with same name exists.", int_value=0)  # Important/duplication
            invitees = UserModel.query(UserModel.email.IN(request.invited)).fetch()

            new_meetup = Meetup(name=request.name, destination=destination, owner=user.key, active=True)
            new_meetup.invited_peeps = [invitee.key for invitee in invitees]
            if request.timeToArrive:
                new_meetup.time_to_arrive = request.timeToArrive
            new_meetup.put()

            for peep in invitees:
                peep.meetup_invites.append(new_meetup.key)  # TODO: Dispatch gcm invite
                peep.put()
            user.meetups.append(new_meetup.key)
            user.put()

            user_loc = UserLocationMeetup(user=user.key)  # time is automatic. No last location yet.
            user_loc.put()

            new_meetup.peeps.append(user_loc.key)
            new_meetup.put()
            return success()
        return no_user()

    @endpoints.method(UpMeetupMessageSmall,
                      SuccessMessage, path="accept_meetup", name="accept_meetup")
    def accept_meetup(self, request):
        """Accepts a meetup for the user.
        """
        user = check_user()
        if user:
            owner = UserModel.query(UserModel.email == request.owner).get()
            if owner:
                meetup = Meetup.query(Meetup.owner == owner.key, Meetup.name == request.name).get()
                if meetup:
                    if meetup.key in user.meetup_invites:
                        user.meetup_invites.remove(meetup.key)
                        user.meetups.append(meetup.key)
                        user.put()

                        user_loc = UserLocationMeetup(user=user.key)
                        user_loc.put()

                        meetup.peeps.append(user_loc.key)
                        meetup.put()
                        return success()
                    return SuccessMessage(str_value="No invite for this meetup!")
                return SuccessMessage(str_value="No such meetup!")
            return SuccessMessage(str_value="No such owner.")
        return no_user()

    @endpoints.method(endpoints.ResourceContainer(unaccepted=messages.BooleanField(1, default=True)), MeetupListMessage,
                      http_method="GET", path="get_meetups", name="get_meetups")
    def get_meetups(self, request):
        """
        Returns simple list of meetups associated with user. If unaccepted = True (default), shows pending invite meetups.
        Else shows active/accepted meetups.
        """
        user = check_user()
        if user:
            if request.unaccepted:
                meetups = ndb.get_multi(user.meetup_invites)
            else:
                meetups = ndb.get_multi(user.meetups)
            return MeetupListMessage(success=success(), meetups=[
                MeetupMessage(owner=meetup.owner.get().email, name=meetup.name, created=meetup.created,
                              active=meetup.active) for meetup in meetups
            ])
        return MeetupListMessage(success=no_user())


    @endpoints.method(UpMeetupMessageSmall, MeetupDescMessage,
                      path="get_meetup_details", name="get_meetup_details")
    def get_meetup_details(self, request):
        """
        Provides full detailed description of a meetup.
        """
        user = check_user()
        if user:
            owner = UserModel.query(UserModel.email == request.owner).get()
            if owner:
                meetup = Meetup.query(Meetup.owner == owner.key, Meetup.name == request.name).get()
                if meetup:
                    if meetup.key in user.meetup_invites + user.meetups:
                        # We have permission to see full description
                        return MeetupDescMessage(success=success(),
                                                 owner=meetup.owner.get().email,
                                                 name=meetup.name,
                                                 pending=[ProfileMessage.FriendMessage(email=peep.email,
                                                                                       nickname=peep.nickname) for peep
                                                          in ndb.get_multi(meetup.invited_peeps)],
                                                 accepted=[ProfileMessage.FriendMessage(email=peep.email,
                                                                                        nickname=peep.nickname) for peep
                                                           in [peepMeetupLoc.user.get() for peepMeetupLoc in
                                                               ndb.get_multi(meetup.peeps)]],
                                                 lat_destination=meetup.destination.lat,
                                                 lon_destination=meetup.destination.lon,
                                                 time_to_arrive=meetup.time_to_arrive,
                                                 created=meetup.created)
                    return MeetupDescMessage(success=SuccessMessage(str_value="No invite for this meetup!"))
                return MeetupDescMessage(success=SuccessMessage(str_value="No such meetup!"))
            return MeetupDescMessage(success=SuccessMessage(str_value="No such owner."))
        return MeetupDescMessage(success=no_user())








