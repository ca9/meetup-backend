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

            user_loc = UserLocationMeetup(user=user.key,
                                          meetup=new_meetup.key)  # time is automatic. No last location yet.
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

                        user_loc = UserLocationMeetup(user=user.key, meetup=meetup.key)
                        user_loc.put()

                        meetup.peeps.append(user_loc.key)
                        meetup.put()
                        return success()
                    return SuccessMessage(str_value="No pending invite for this meetup!")
                return SuccessMessage(str_value="No such meetup!")
            return SuccessMessage(str_value="No such owner.")
        return no_user()

    @endpoints.method(endpoints.ResourceContainer(unaccepted=messages.BooleanField(1, default=True)), MeetupListMessage,
                      http_method="POST", path="get_meetups", name="get_meetups")
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


    @endpoints.method(UpMeetupMessageSmall, MeetupDescMessage, http_method="POST",
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

    @endpoints.method(UpLocationMessage, MeetupLocationsUpdateFullMessage, http_method="POST",
                      path="heartbeat", name="heartbeat")
    def heartbeat(self, request):
        """
        Accepts latest location against a meetup. Returns latest locations of meetup. "details" boolean demands
        historical locations.
        :type request: UpLocationMessage
        """
        user = check_user()
        if user:
            owner = UserModel.query(UserModel.email == request.meetup_owner).get()
            if owner:
                meetup = Meetup.query(Meetup.owner == owner.key, Meetup.name == request.meetup_name).get()
                if meetup:
                    if meetup.key in user.meetups:
                        my_meetup_loc = UserLocationMeetup.query(UserLocationMeetup.meetup == meetup.key,
                                                                 UserLocationMeetup.user == user.key).get()
                        if not my_meetup_loc:
                            # Fix the Meetup entry.
                            my_meetup_loc = UserLocationMeetup(meetup=meetup.key, user=user.key)
                            my_meetup_loc.put()
                            meetup.invited_peeps.remove(user.key)
                            meetup.peeps.append(my_meetup_loc.key)
                            meetup.put()

                        # Update me.
                        my_meetup_loc.last_location = ndb.GeoPt(request.lat, request.lon)

                        location = LocationItem(location=my_meetup_loc.last_location)
                        location.put()

                        my_meetup_loc.locations.append(location.key)
                        my_meetup_loc.put()

                        # Build the response
                        response = MeetupLocationsUpdateFullMessage(success=success(), UserMeetupLocations=[])
                        for ulm in ndb.get_multi(meetup.peeps):
                            peep = ulm.user.get()
                            a_plm = PeepLocationsMessage(name=peep.nickname, email=peep.email,
                                                         latest_location=LocationMessage(lat=ulm.last_location.lat,
                                                                                         # GeoPt
                                                                                         lon=ulm.last_location.lon,
                                                                                         # GeoPt
                                                                                         time=ulm.last_update))
                            if request.details:
                                locs = [LocationMessage(lat=loc.location.lat, lon=loc.location.lon, time=loc.time) for
                                        loc in ndb.get_multi(ulm.locations)]  # LocationItems
                                a_plm.locations = locs
                            response.UserMeetupLocations.append(a_plm)

                        return response
                    return MeetupLocationsUpdateFullMessage(
                        success=SuccessMessage(str_value="Not a member of this meetup!"))
                return MeetupLocationsUpdateFullMessage(success=SuccessMessage(str_value="No such meetup!"))
            return MeetupLocationsUpdateFullMessage(success=SuccessMessage(str_value="No such owner."))
        return MeetupLocationsUpdateFullMessage(success=no_user())





