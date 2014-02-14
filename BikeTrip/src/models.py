'''
Created on 23.01.2014.

@author: Sanja
'''

from google.appengine.ext import ndb
from google.appengine.ext import blobstore

class Track(ndb.Model):
    '''
    Models a Track
    '''
    track_name = ndb.StringProperty()
    creation_date = ndb.DateTimeProperty(auto_now_add=True)
    blob_key =ndb.BlobKeyProperty()
    status = ndb.StringProperty()
     

class TrackStatistic(ndb.Model):
    '''
    Models Statistic.
    ****CHANGED to parent model to ensure consistency**** Has reference to Track to provide one-to-many relationship****
    
    *TrackStatistic dosen't belongs to same group as corresponding track
    *total_time is StringProperty because it measure duration, so no other formats were appropriate
    '''
#     track = ndb.KeyProperty(kind=Track)
    name = ndb.StringProperty()
    total_distance = ndb.FloatProperty()
    total_time = ndb.StringProperty()
    avr_speed = ndb.FloatProperty()
    total_climb = ndb.FloatProperty()
    max_elev = ndb.FloatProperty()
    
class Trip(ndb.Model):
    '''
    Models a Trip with name,creation date, from date, to date, description and trip avatar, cities and visibility.
    '''
    
    trip_name = ndb.StringProperty()
    creation_date = ndb.DateTimeProperty(auto_now_add=True)
    from_date = ndb.DateProperty();
    to_date = ndb.DateProperty();
    trip_avatar = ndb.BlobProperty()
    description = ndb.TextProperty()
    cities = ndb.StringProperty(repeated=True)
    visibility = ndb.BooleanProperty()
    #for trip statistic
    trip_statistic = ndb.StructuredProperty(TrackStatistic)

    


    
