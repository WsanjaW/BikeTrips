'''
Created on 13.02.2014.

@author: Sanja
'''
from models import Trip,Track,TrackStatistic
import json
from google.appengine.ext import ndb
   
def sec_to_time(time):
    '''
    Convert seconds given as number to string h:m:s
    '''
    time = int(time)
    h = time/3600
    time = time%3600
    m = time/60
    time = time%60
    s = time
    return "{:0>2d}".format(h) + ":" + "{:0>2d}".format(m) + ":" + "{:0>2d}".format(s)

def time_to_sec(time):
    '''
     Converts time in string format h:m:s to seconds
     '''
    if(time ==""):
        return 0
    t = time.split(':')
    h = int(t[0])
    m = int(t[1])
    s = int(t[2])
    return h * 3600 + m * 60 + s

def calculate_trip_stat(trip_key):
    '''
    Calculates statistic for whole trip
    '''
    #get tracks for trip
    track_query = Track.query(ancestor=trip_key)
    tracks = track_query.fetch(20)
    stats = []
    #get statistic from every track
    for track in tracks:
        track_stat_query= TrackStatistic.query(ancestor=track.key)
        track_stat = track_stat_query.fetch(1)
        if  track_stat != []:
            stats.append(track_stat[0])
   
    #get trip 
    trip= trip_key.get()
  
    #calculate total distance
    dist = sum([s.total_distance for s in stats])
    trip.trip_statistic.total_distance = dist
    
    #calculate total time
    time_sec = sum([time_to_sec(s.total_time) for s in stats])
    time = sec_to_time(time_sec)
    trip.trip_statistic.total_time = time
    
    #calculate avr
    if time_sec > 0:
        trip.trip_statistic.avr_speed = dist/(time_sec * 0.000277778)
    else:
        trip.trip_statistic.avr_speed = 0
   
    #calculate total climb
    climb = sum([s.total_climb for s in stats])
    trip.trip_statistic.total_climb = climb
    
    #calculate max elev
    maxel = max([s.max_elev for s in stats] + [-100])
    trip.trip_statistic.max_elev = maxel
    
    trip.put()
     
def procesCity(json_string):
    '''
    Returns (lat,lng) tuple from given json string in format:
    {
        "totalResultsCount": 150,
            "geonames": [{
        "toponymName": "Zant 0",
        "fcl": "T",
        "name": "Zant 0",
        "countryCode": "DE",
        "lng": "11.61645",
        "fcode": "HLL",
        "geonameId": 7289257,
        "lat": "49.42775"
            }]
    }
    '''
    data = json.loads(json_string)
    try:
        lat = data['geonames'][0]['lat']
        lon = data['geonames'][0]['lng']
        return [float(lat), float(lon)]
    except:
        return [0, 0]
  
def trip_key(trip_userid='0'):
        '''
        Constructs a Datastore key for a Trip entity with userid.
        '''
        
        return ndb.Key('UserTrip', trip_userid)
    
def make_track_tree(id,location,type,season):
    '''
    Create tree (http://www.ztree.me/v3/main.php#_zTreeInfo)
    '''
    #get all trips
    trips_query = Trip.query(ancestor=trip_key(id))
    if location != []:
        trips_query = trips_query.filter(Trip.trip_tags.location.IN(location))
    if type != []:
        trips_query = trips_query.filter(Trip.trip_tags.type.IN(type))
    if season != []:
        trips_query = trips_query.filter(Trip.trip_tags.season.IN(season))
    
    trips = trips_query.fetch()
      
    #create tree structure from trips
    tree = []
    i = 1
    of = 0
    tree.append({'id':0, 'pId':0, 'name':'My Trips','isParent': 'true','open':'true'})
    for trip in trips:
        tree.append({'id':i, 'pId':0, 'name':str(trip.trip_name),'isParent': 'true', 'click':"openTrip('"+ str(trip.key.urlsafe()) +"')"})
        #get tracks from trip
        track_query = Track.query(ancestor=trip.key).order(-Track.creation_date)
        tracks = track_query.fetch(20)
        for track in tracks:
            tree.append({'id':i+10+of, 'pId':i, 'name':str(track.track_name),'click':"openTrack('"+ str(track.key.urlsafe()) +"')"})
            of += 1
        i += 1
        
    return tree


def creatList(s):
    '''
    Create list from string separated by ","
    '''
    l = s.split(',')
    return l
def union(l1,l2):
    '''
    Makes union of two lists
    '''
    l = [x for x in l1 if x not in l2] + l2
    return l
    