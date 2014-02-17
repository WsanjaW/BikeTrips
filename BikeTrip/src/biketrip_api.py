'''
Created on 16.02.2014.

@author: Sanja
'''
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from models import Trip


class StatisticMes(messages.Message):
    total_distance = messages.FloatField(1)
    total_time = messages.StringField(2)
    avr_speed = messages.FloatField(3)
    total_climb = messages.FloatField(4)
    max_elev = messages.FloatField(5)
    
class TripMes(messages.Message):
    '''
    Trip message
    '''
    trip_name = messages.StringField(1)
# #     creation_date = messages.StringField(2)
# #     from_date = messages.StringField(2);
#     to_date = ndb.DateProperty();
    trip_avatar = messages.StringField(2)
    description = messages.StringField(3)
    cities = messages.StringField(4,repeated=True)
#     visibility = ndb.BooleanProperty()
#     #for trip statistic
    trip_statistic = messages.MessageField(StatisticMes,5)



class TripCollection(messages.Message):
    '''
    Collection of Trip messages
    '''
    items = messages.MessageField(TripMes, 1, repeated=True)
    

@endpoints.api(name='biketrips', version='v1',description="Bike trips API v1",documentation="localhost:8080")
class HelloWorldApi(remote.Service):
    '''
    BikeTrips API v1.
    '''
    ID_RESOURCE = endpoints.ResourceContainer(
                            message_types.VoidMessage,
                            stat=messages.BooleanField(1),
                            name=messages.StringField(2),
                            page=messages.IntegerField(3),
                            )

    
    @endpoints.method(ID_RESOURCE, TripCollection,
                      path='gettrips', http_method='GET',
                      name='trips.getTrips')
    def trip_list(self, request):
        trips = []
        p = 10
        if request.page:
            p = request.page
        
        if request.name:
            
            trip_query = Trip.query(Trip.trip_name==request.name)
        else:
            trip_query = Trip.query()
    
        for trip in trip_query.fetch(p):
            t = TripMes(trip_name=trip.trip_name)
            if trip.trip_avatar:
                t.trip_avatar = 'http://localhost:8080/img?img_id=' + trip.key.urlsafe()
            t.description = trip.description
            t.cities = trip.cities
            if request.stat == True:
                t.trip_statistic = StatisticMes(total_time=request.name)
            trips.append(t)
        return TripCollection(items=trips)

   

application = endpoints.api_server([HelloWorldApi])

