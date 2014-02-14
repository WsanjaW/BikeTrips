'''
Created on 13.02.2014.

@author: Sanja
'''
from models import Trip,Track,TrackStatistic
   
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
     

  
        