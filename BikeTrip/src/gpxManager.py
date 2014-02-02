'''
Created on 01.02.2014.

Module for processing .gpx files 

@author: Sanja
'''

from xml.dom.minidom import parseString, parse
from datetime import datetime
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
    
    '''
    
    def parse_gpx(self,gpxstring):
        '''
        Processes gpx track and returns list of Track objects 
        '''
        doc = parse(gpxstring)
        trkList = doc.getElementsByTagName('trk')
        tracks = []
        try:
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
                                        wp.time = wpAtrr.firstChild.nodeValue
                                tracks[-1].wpList.append(wp)
            return tracks
           
        except:
            raise Exception('File format error')
        
    def DistanceBetweenPlaces(self,lon1, lat1, lon2,  lat2):
        '''
        Calculates distance between two points(lon,lat)
        '''
        dlon = self.Radians(lon2 - lon1);
        dlat = self.Radians(lat2 - lat1);

        a = (math.sin(dlat / 2) * math.sin(dlat / 2)) + math.cos(self.Radians(lat1)) * math.cos(self.Radians(lat2)) * (math.sin(dlon / 2) * math.sin(dlon / 2));
        angle = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
        return angle * RADIUS;
        
    def Radians(self,x):
        '''
        Degree to radians
        '''
        return x * PIx / 180;

    def calculateDistance(self,trList):
        '''
        Calculates total distance for every track in trList
        '''
        total = 0;

        for item in trList:
        
            wpList = item.wpList;
            priv = wpList[0]
            for wp in wpList[1:]:
                total += self.DistanceBetweenPlaces(priv.lon,priv.lat,wp.lon,wp.lat)
                priv = wp

            return total;
    
    def totalClimb(self,trList):
        '''
        Calculates total climb for every track in trList
        '''
        
        total = 0
        for track in trList:
            
            wpList = track.wpList;
            priv = wpList[0]
            for wp in wpList[1:]:
                diff = wp.elev - priv.elev
                if diff > 0:
                    if self.DistanceBetweenPlaces(priv.lon,priv.lat,wp.lon,wp.lat)> 0.003:
                        total += diff
                        
                priv = wp

            return total;
        
        

        
        
        