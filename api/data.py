import calendar
from datetime import datetime
from authentication import *
from models import *
from datetime import timedelta
from gcm import GCM


@endpoints.api(name='data_api',
               version='v2',
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
        Creates a meetup item (v1 - cannot be undone). If within 3 hours of time, it is active.
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

            new_meetup = Meetup(name=request.name, destination=destination, owner=user.key, active=False)
            new_meetup.invited_peeps = [invitee.key for invitee in invitees]
            if request.timeToArrive:
                time_to_arrive_utc = local_to_utc(request.timeToArrive)
                if timedelta(hours=-1) <= time_to_arrive_utc - datetime.now() <= timedelta(hours=3):
                    new_meetup.active = True
                new_meetup.time_to_arrive = time_to_arrive_utc
            new_meetup.put()

            gcm_reg_ids = []
            for peep in invitees:
                peep.meetup_invites.append(new_meetup.key)
                peep.put()
                if peep.gcm_main:
                    gcm_reg_ids.append(peep.gcm_main)

            try:
                gcm = GCM(client_ids.API_SERVER_GCM_PIN)
                data = {'meetup_name': new_meetup.name, 'meetup_owner_name': user.nickname,
                        'active': new_meetup.active, 'meetup_owner_email': user.email}
                gcm.json_request(registration_ids=gcm_reg_ids, data=data, collapse_key='make_meetup')
            except Exception as e:
                print e

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

                        # gcm inform
                        gcm_reg_ids = []
                        for peep in ndb.get_multi([ulm.user for ulm in ndb.get_multi(meetup.peeps)]):
                            gcm_reg_ids.append(peep.gcm_main)
                        try:
                            gcm = GCM(client_ids.API_SERVER_GCM_PIN)
                            data = {'meetup_name': meetup.name, 'meetup_owner_name': owner.nickname,
                                    'active': meetup.active, 'meetup_owner_email': owner.email,
                                    'acceptor_name': user.nickname, 'acceptor_email': user.email}
                            gcm.json_request(registration_ids=gcm_reg_ids, data=data, collapse_key='meetup_accepted')
                        except Exception as e:
                            print e

                        meetup.put()
                        return success()
                    return SuccessMessage(str_value="No pending invite for this meetup!")
                return SuccessMessage(str_value="No such meetup!")
            return SuccessMessage(str_value="No such owner.")
        return no_user()

    @endpoints.method(request_message=message_types.VoidMessage, response_message=MeetupListMessage,
                      http_method="POST", path="get_meetups_accepted", name="get_meetups_accepted")
    def get_meetups_accepted(self, request):
        """
        Returns simple list of accepted meetups associated with user.
        """
        user = check_user()
        if user:
            meetups = ndb.get_multi(user.meetups)
            return MeetupListMessage(success=success(), meetups=[
                MeetupMessage(owner=meetup.owner.get().email, name=meetup.name, created=meetup.created,
                              active=meetup.active) for meetup in meetups
            ])
        return MeetupListMessage(success=no_user())

    @endpoints.method(request_message=message_types.VoidMessage, response_message=MeetupListMessage,
                      http_method="POST", path="get_meetups_unaccepted", name="get_meetups_unaccepted")
    def get_meetups_unaccepted(self, request):
        """
        Returns simple list of unaccepted meetups associated with user.
        """
        user = check_user()
        if user:
            meetups = ndb.get_multi(user.meetup_invites)
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
                    if meetup.active:
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

                            # deactivate if we're done
                            if meetup.time_to_arrive - datetime.now() > timedelta(hours=-1):
                                meetup.active = False
                                meetup.put() #todo: notify

                                # notify
                                gcm_reg_ids = []
                                for peep in ndb.get_multi([ulm.user for ulm in ndb.get_multi(meetup.peeps)]):
                                    gcm_reg_ids.append(peep.gcm_main)
                                try:
                                    gcm = GCM(client_ids.API_SERVER_GCM_PIN)
                                    data = {'meetup_name': meetup.name, 'meetup_owner_name': user.nickname,
                                            'active': meetup.active, 'meetup_owner_email': user.email}
                                    gcm.json_request(registration_ids=gcm_reg_ids, data=data, collapse_key='meetup_deactivated')
                                except Exception as e:
                                    print e

                            # Build the response
                            response = MeetupLocationsUpdateFullMessage(success=success(), UserMeetupLocations=[])
                            for ulm in ndb.get_multi(meetup.peeps):
                                peep = ulm.user.get()
                                if ulm.last_location:
                                    a_plm = PeepLocationsMessage(name=peep.nickname, email=peep.email,
                                                                 latest_location=LocationMessage(
                                                                     lat=ulm.last_location.lat,
                                                                     # GeoPt
                                                                     lon=ulm.last_location.lon,
                                                                     # GeoPt
                                                                     time=ulm.last_update))
                                    if request.details:
                                        locs = [
                                            LocationMessage(lat=loc.location.lat, lon=loc.location.lon, time=loc.time)
                                            for
                                            loc in ndb.get_multi(ulm.locations)]  # LocationItems
                                        a_plm.locations = locs
                                    response.UserMeetupLocations.append(a_plm)
                            return response
                        return MeetupLocationsUpdateFullMessage(
                            success=SuccessMessage(str_value="Not a member of this meetup!"))
                    return MeetupLocationsUpdateFullMessage(
                        success=SuccessMessage(str_value="Meetup is inactive.", int_value=2))
                return MeetupLocationsUpdateFullMessage(success=SuccessMessage(str_value="No such meetup!"))
            return MeetupLocationsUpdateFullMessage(success=SuccessMessage(str_value="No such owner."))
        return MeetupLocationsUpdateFullMessage(success=no_user())


    @endpoints.method(UpMeetupMessageOwner,
                      SuccessMessage, path="activate_meetup", name="activate_meetup")
    def activate_meetup(self, request):
        """Activates the meetup, only if it starts within 3 hours, or has ended an within an hour ago.
        """
        user = check_user()
        if user:
            meetup = Meetup.query(Meetup.owner == user.key, Meetup.name == request.meetup_name).get()
            if meetup:
                time_diff = meetup.time_to_arrive - datetime.now()  # this is in utc
                if timedelta(hours=3) > time_diff > timedelta(hours=-1):
                    meetup.active = True
                    meetup.put()

                    gcm_reg_ids = []
                    for peep in ndb.get_multi([ulm.user for ulm in ndb.get_multi(meetup.peeps)]):
                        gcm_reg_ids.append(peep.gcm_main)
                    try:
                        gcm = GCM(client_ids.API_SERVER_GCM_PIN)
                        data = {'meetup_name': meetup.name, 'meetup_owner_name': user.nickname,
                                'active': meetup.active, 'meetup_owner_email': user.email}
                        gcm.json_request(registration_ids=gcm_reg_ids, data=data, collapse_key='meetup_activated')
                    except Exception as e:
                        print e

                    return SuccessMessage(str_value="Meetup {} activated.".format(meetup.name), int_value=1)
                return SuccessMessage(
                    str_value="Meetup cannot be activated. Time difference to start is {}".format(time_diff),
                    int_value=2)
            return SuccessMessage(str_value="Meetup not found.")
        return no_user()


    @endpoints.method(UpMeetupMessageOwner,
                      SuccessMessage, path="deactivate_meetup", name="deactivate_meetup")
    def deactivate_meetup(self, request):
        """Deactivates the meetup.
        """
        user = check_user()
        if user:
            meetup = Meetup.query(Meetup.owner == user.key, Meetup.name == request.meetup_name).get()
            if meetup:
                meetup.active = False
                meetup.put()

                gcm_reg_ids = []
                for peep in ndb.get_multi([ulm.user for ulm in ndb.get_multi(meetup.peeps)]):
                    gcm_reg_ids.append(peep.gcm_main)
                try:
                    gcm = GCM(client_ids.API_SERVER_GCM_PIN)
                    data = {'meetup_name': meetup.name, 'meetup_owner_name': user.nickname,
                            'active': meetup.active, 'meetup_owner_email': user.email}
                    gcm.json_request(registration_ids=gcm_reg_ids, data=data, collapse_key='meetup_deactivated')
                except Exception as e:
                    print e

                return SuccessMessage(str_value="Meetup {} deactivated.".format(meetup.name), int_value=1)
            return SuccessMessage(str_value="Meetup not found.")
        return no_user()

    @endpoints.method(UpMeetupMessageSmall, SuccessMessage,
                      path="check_active_meetup", name="check_meetup_active")
    def check_active(self, request):
        """ Checks if meetup is active. Please provide meetup owner and name. Returns 2 if active, 1 if inactive,
        0 if there is an error."""
        user = check_user()  # todo: check if the user making request is in the meetup
        if user:
            owner = UserModel.query(UserModel.email == request.owner).get()
            if owner:
                meetup = Meetup.query(Meetup.owner == owner.key, Meetup.name == request.name).get()
                if meetup:
                    if meetup.active:
                        return SuccessMessage(int_value=2, str_value="Meetup is active.")
                    return SuccessMessage(int_value=1, str_value="Meetup is inactive.")
                return SuccessMessage(str_value="Meetup not found.")
            return SuccessMessage(str_value="Owner not found.")
        return no_user()


##################
# Helper Functions
##################

def local_to_utc(dt):
    """
    :type dt: datetime
    :rtype: datetime
    """
    dt = dt - dt.utcoffset()
    secs = time.mktime(dt.timetuple())  # convert to tuple, to seconds
    secs = time.gmtime(secs)  # to GMT/UTC
    return datetime.fromtimestamp(time.mktime(secs))


def utc_to_local(t):
    secs = calendar.timegm(t)
    return time.localtime(secs)