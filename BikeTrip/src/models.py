'''
Created on 23.01.2014.

@author: Sanja
'''

from google.appengine.ext import ndb

class Trip(ndb.Model):
    '''
    Models a Trip with name,creation date, from date, to date, description and trip avatar, cities and visibility.
    '''
    
    trip_name = ndb.StringProperty()
    creation_date = ndb.DateProperty(auto_now_add=True)
    from_date = ndb.DateProperty();
    to_date = ndb.DateProperty();
    trip_avatar = ndb.BlobProperty()
    description = ndb.TextProperty()
    cities = ndb.StringProperty(repeated=True)
    visibility = ndb.BooleanProperty()