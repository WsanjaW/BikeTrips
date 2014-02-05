'''
Created on 01.02.2014.

Module for processing .gpx files 

@author: Sanja
'''

from xml.dom.minidom import parseString, parse
from datetime import datetime,timedelta
from errors import GpxFormatException,GpxDateFormatException
import math



PIx = 3.14159265358979
RADIUS = 6371

class WP():
    '''
    Represents way point with latitude, longitude, elevation and time
    '''
   
    def __init__(self, lat="",lon="",elev="",time=""):
        '''
        Constructor
        '''
        self.lat = lat
        self.lon = lon
        self.elev = elev
        self.time = time
    
class Track():
    '''
    Represents Track with name and list of way points
    '''

    def __init__(self, name,wpList=[]):
        '''
        Constructor
        '''
        self.name = name
        self.wpList = wpList
        
class GPXReader():
    '''
    Class for parsing gpx file
    '''
    
    def parse_gpx(self,gpxstring):
        '''
        Processes gpx track and returns list of Track objects 
        '''
       
        try:
            doc = parseString(gpxstring)
            trkList = doc.getElementsByTagName('trk')
            tracks = []
            for trkNode in trkList:
                wpList = []
                tracks.append(Track(trkNode.getElementsByTagName('name')[0]
                                    .firstChild.nodeValue,wpList))
                
                trksegNodes = trkNode.childNodes
                for trksegNode in trksegNodes:
                    if trksegNode.nodeName == "trkseg":
                        
                        trkptList = trksegNode.childNodes
                       
                        for wpNode in trkptList:
                            if wpNode.nodeName !="#text":
                                wp = WP()
                                wp.lat = float(wpNode.getAttribute('lat'))
                                wp.lon = float(wpNode.getAttribute('lon'))
                                wpAtrrs = wpNode.childNodes
                                for wpAtrr in wpAtrrs:
                                    if wpAtrr.nodeName =="ele":
                                        wp.elev = float(wpAtrr.firstChild.nodeValue)
                                    if wpAtrr.nodeName =="time":
                                        #two possible date formats 2005-09-10T12:55:12.999Z and 2013-08-12T07:17:29Z
                                        #TODO make every standard format available 
                                        try:
                                            wp.time = datetime.strptime(wpAtrr.firstChild.nodeValue,'%Y-%m-%dT%H:%M:%SZ')  
                                        except:
                                            try:
                                                wp.time = datetime.strptime(wpAtrr.firstChild.nodeValue,'%Y-%m-%dT%H:%M:%S.%fZ') 
                                            except:
                                                raise GpxDateFormatException()
                                                
                                            
                                        
                                tracks[-1].wpList.append(wp)
            return tracks
        #TODO better exception handling
        except GpxDateFormatException as e:
            raise e
        except:
            raise GpxFormatException()
        
    



class GPXCalculation():
    '''
    Class for calculating statistics for given track
    '''
    
    def __init__(self,track):
        '''
        Sets Track object 
        '''
        self.track = track
    
    def calculate_distance(self):
        '''
        Calculates total distance 
        '''
        total = 0;
        wpList = self.track.wpList;
        priv = wpList[0]
        for wp in wpList[1:]:
            total += self.distance_between_places(priv.lon,priv.lat,wp.lon,wp.lat)
            priv = wp

        return total;
    
    def total_climb(self):
        '''
        Calculates total climb 
        '''
        
        total = 0           
        wpList = self.track.wpList;
        priv = wpList[0]
        for wp in wpList[1:]:
            if(wp.elev != ""):
                diff = wp.elev - priv.elev
                if diff > 0:
                    if self.distance_between_places(priv.lon,priv.lat,wp.lon,wp.lat)> 0.003:
                        total += diff
                        
                priv = wp

        return total;
        
    def total_time(self):
        '''
        Calculates total moving time 
        '''
        total = timedelta()
       
        wpList = self.track.wpList
        priv = wpList[0]
        for wp in wpList:
            if(wp.time != ""):
                dt = wp.time - priv.time
                if self.distance_between_places(priv.lon,priv.lat,wp.lon,wp.lat) > 0.003 and dt.total_seconds() < 105:
                    total += dt
                priv = wp
        return total
    
    def avr_speed(self):
        '''
        Calculates average moving speed 
        '''
        total_distance = self.calculate_distance()
        total_time = self.total_time()
        if total_distance == 0:
            return 0
        if total_time.total_seconds() == 0:
            return 0
        
        return total_distance/(total_time.total_seconds() * 0.000277778)
    
    def max_elev(self):
        '''
        Calculates max elevation 
        '''
        m = -100
        m = max([x.elev for x in self.track.wpList if x.elev != ""] + [-100])
        
        return m   
     
    def distance_between_places(self,lon1, lat1, lon2,  lat2):
        '''
        Calculates distance between two points(lon,lat)
        '''
        dlon = self.radians(lon2 - lon1);
        dlat = self.radians(lat2 - lat1);

        a = (math.sin(dlat / 2) * math.sin(dlat / 2)) + math.cos(self.radians(lat1)) * math.cos(self.radians(lat2)) * (math.sin(dlon / 2) * math.sin(dlon / 2));
        angle = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
        return angle * RADIUS;
        
    def radians(self,x):
        '''
        Degree to radians
        '''
        return x * PIx / 180;

        