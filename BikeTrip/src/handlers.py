'''
Created on 28.01.2014.

@author: Sanja
'''
import os
import webapp2
import jinja2
import json
import urllib
import time

import helper

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.datastore.datastore_query import Cursor


from datetime import datetime,timedelta
from models import Trip,Track,TrackStatistic
from gpxManager import GPXReader,GPXCalculation
from errors import GpxFormatException,GpxDateFormatException


#set jinja templates environment
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def trip_key(trip_userid='0'):
        '''
        Constructs a Datastore key for a Trip entity with userid.
        '''
        
        return ndb.Key('UserTrip', trip_userid)


class ShowTrips(webapp2.RequestHandler):
    '''
    Shows either newest trips or trips for logged in user
    '''
    
    def get(self):
        
        user = users.get_current_user()
        id ='0'
        #check if user is logged in and creates appropriate url
        if user:
            id = user.user_id()
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        #parameter mytrips = True if only users trips should be shown  
        mytrips = self.request.get('mytrips')
        
        if mytrips == 'True':
            trips_query = Trip.query(ancestor=trip_key(id)).order(-Trip.creation_date)
        else:
            trips_query = Trip.query(Trip.visibility==True).order(-Trip.creation_date)
              
        trips, next_curs, more = trips_query.fetch_page(5)
        
        tripsstats = {}
        #get all statistics
        for trip in trips:
            stat_query = TrackStatistic.query(ancestor=trip.key).fetch(1)
            tripsstats[trip.key]=stat_query
        #return index page
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'trips':trips,'cursor':next_curs,'more':more,'stats':tripsstats}
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.write(template.render(template_values))
    
   
    
class AddTrip(webapp2.RequestHandler):
    '''
    Handles form for adding trip
    '''
    def get(self):
        '''
        Show form
        '''
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext}
        template = JINJA_ENVIRONMENT.get_template('templates/addtrip.html')
        self.response.write(template.render(template_values))
    
    def post(self):
        '''
        Adds trip to datastore
        '''
        user = users.get_current_user()
        id = '0'
        if user:
            id = user.user_id()
        
        #TODO some checking      
        trip = Trip(parent=trip_key(id))
        trip.trip_name = self.request.get('trip_name')
        
        trip.description = self.request.get('description')
        trip.cities =  self.get_cities(self.request.get('cities'))
        avatar = self.request.get('img')
        if  avatar:
            trip.trip_avatar = avatar
        
        trip.from_date = datetime.strptime( self.request.get('from_date'), '%m/%d/%Y')  
        trip.to_date = datetime.strptime(self.request.get('to_date'), '%m/%d/%Y')
        
        if self.request.get('visibility') == 'True':
            trip.visibility = True
        else:
            trip.visibility = False
        
        trip.put()
        #create statistic for whole trip 
        ts = TrackStatistic(parent=trip.key,name=trip.trip_name)
        ts.total_distance = 0
        ts.total_time = ""
        ts.avr_speed = 0
        ts.total_climb = 0
        ts.max_elev = -100
        ts.put()
       
        #redirect to mytrips because showing all tips will only be consistent in scope of user
        # and only eventually consistent for whole datastore  
        self.redirect('/alltrips?mytrips=True')
    
    def get_cities(self,allCities):
        '''
        Create list of cities from string
        '''
        cities = allCities.split(',')
        cities = [x.strip() for x in cities]
        return cities
    
    
    
class ImageHandler (webapp2.RequestHandler):
    '''
    Gets image based on trip key send in url
    '''
    def get(self):
        trip_key=self.request.get('img_id')
        tripk = ndb.Key(urlsafe=trip_key)
        trip = tripk.get()
        if trip.trip_avatar:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(trip.trip_avatar)
        else:
            self.error(404)

class CityInfo(webapp2.RequestHandler):
    '''
    Shows city on google map using geonames.org to get coordinates
    '''
    def proces(self,json_string):
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
            return (lat,lon)
        except:
            return (0,0)

    def get(self):
        '''
        Calls Rest web servis from geonames.org to get coordinates for given city   
        '''
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        city = self.request.get('city').lower().replace(" ", "+")
        
        url = "http://api.geonames.org/searchJSON?formatted=true&name={0}&maxRows=1&lang=es&username=wsanjaw&style=short".format(city)
        result = urlfetch.fetch(url)
        data = self.proces(result.content)
       
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext, 'lat':data[0], 'lng':data[1]}
        template = JINJA_ENVIRONMENT.get_template('templates/cities.html')
        self.response.write(template.render(template_values))
    
class OneTrip(webapp2.RequestHandler):
    '''
    Shows one trip, with id sent in url, and tracks for that trip
    Shows form for uploading gpx files, and statistic for whole trip
    '''
    def get(self):
        
        upload_url = blobstore.create_upload_url('/upload')

        user = users.get_current_user()
        id ='0'
        #check if user is logged in and creates appropriate url
        if user:
            id = user.user_id()
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        #get specific trip     
        trip_key = self.request.get('trip_id')
        tripk = ndb.Key(urlsafe=trip_key)
        trip = tripk.get()
        
        #get id of user for given track
        trip_user = tripk.parent().id()
        
        #get tracks for trip
        track_query = Track.query(ancestor=tripk).order(-Track.creation_date)
        tracks = track_query.fetch(20)
        #get number of tracks
        num = len(tracks)
       
        
        #get global statistic for trip       
        stat_query = TrackStatistic.query(ancestor=trip.key).fetch(1)
        
        
        #get blobInfo objects from blob_key
        bli = []
        for track in tracks:
            bli.append(BlobInfo(track.blob_key))
                  
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'trip':trip,'upload':upload_url,
                           'tracks':tracks,'blobs':bli,'num':num,'trip_user':trip_user,'stats':stat_query}
        template = JINJA_ENVIRONMENT.get_template('templates/onetrip.html')
        
        #set cookie value to this page url
        self.response.set_cookie('redirect_url', self.request.url)

        self.response.write(template.render(template_values))
    
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    '''
    Handler for uploading gpx file to blobstore
    '''
    def post(self):
        
        upload_files = self.get_uploads('file') 
        blob_info = upload_files[0]
        #get trip_id from hidden filed in form
        trip_key = self.request.get('trip_id')
        tripk = ndb.Key(urlsafe=trip_key)
        
        #updetr trip status
        trip = tripk.get()
        trip.put()
        
        #create new track which parent is current track 
        track = Track(parent=tripk,track_name=self.request.get('trip_name'),blob_key=blob_info.key()) 
        track.status = "Processing track, try again later"  
        track.put()
        
        track_key = track.key
        #Add the task to the default queue.
        taskqueue.add(url='/worker', params={'key': track_key.urlsafe()},target="mybackend")
       

        self.redirect(self.request.referer)


class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    '''
    Handles file download
    '''
    def get(self, resource):
        
       
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        save_as_name =  blob_info.filename
        mime_type='text/xml'
        self.send_blob(blob_info,content_type=mime_type,save_as=save_as_name)

class UpdateTripHandler(webapp2.RequestHandler):
    '''
    Handler for updating trip name and cities
    TODO add other updates
    '''
    def post(self):
        
        if self.request.get('form_id') == 'nuf':
            
            new_name = self.request.get('txtValue')
            if new_name:
                
                #get specific trip     
                trip_key = self.request.get('trip_id')
                tripk = ndb.Key(urlsafe=trip_key)
                trip = tripk.get()
          
                trip.trip_name = new_name
                trip.put()
        
       
                # Create an array
                array = {'text': new_name}
       
                # Output the JSON
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(json.dumps(array))
        
        if self.request.get('form_id') == 'cuf':
            
            new_cities = self.request.get('txtValue')
            
            #get specific trip     
            trip_key = self.request.get('trip_id')
            tripk = ndb.Key(urlsafe=trip_key)
            trip = tripk.get()
            trip.cities = self.get_cities(new_cities)
           
            trip.put()
        
       
            # Create an array
            array = {'text': new_cities}
       
            # Output the JSON
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps(array))
    
    def get_cities(self,allCities):
        '''
        Create list of cities from string
        '''
        cities = allCities.split(',')
        cities = [x.strip() for x in cities]
        return cities

class DeleteTripHandler(webapp2.RequestHandler):
    '''
    Delete trip and all of his tracks and statistics
    '''
    def get(self):
        
        #get specific trip     
        trip_key = self.request.get('trip_id')
        tripk = ndb.Key(urlsafe=trip_key)
        trip = tripk.get()
                
        #get tracks for trip
        track_query = Track.query(ancestor=tripk)
        tracks = track_query.fetch()
        for track in tracks:
            #delete .gpx files from blobstore
            bolob = track.blob_key
            blobstore.delete(bolob)
            #delete statistic
            for item in TrackStatistic.query(TrackStatistic.track == track.key):
                item.key.delete()
            
            #delete track
            track.key.delete()
        
        stat_query = TrackStatistic.query(ancestor=trip.key).fetch(1)
        stat_query[0].key.delete()
        
        #redirect to mytrips because showing all tips will only be consistent in scope of user
        # and only eventually consistent for whole datastore  
        trip.key.delete()
        
        self.redirect('/alltrips?mytrips=True')



            
class TrackParserHandler(webapp2.RequestHandler):
    '''
    Calculates statistic for uploaded .gpx file
    Called from push queue
    TODO transaction when writing in db
    '''
               
    def post(self):
        
        #time.sleep(30)
        
        #get track
        key = self.request.get('key')
        track_key = ndb.Key(urlsafe=key)
        track = track_key.get()
        
        track_stat_query= TrackStatistic.query(TrackStatistic.track == track_key)
        stat = track_stat_query.fetch(1)
        if stat == []:
            
            #get global statistic
            stat_query = TrackStatistic.query(ancestor=track.key.parent()).fetch(1)
           
            
            
            #read data from uploaded file
            blob_reader = blobstore.BlobReader(track.blob_key)
            data = blob_reader.read()
            try:
                g = GPXReader()
                a = g.parse_gpx(data)
        
                for item in a:
            
                    gc = GPXCalculation(item)
                    ts = TrackStatistic(track=track.key,name=item.name)
                    total_distance = gc.calculate_distance()
                    ts.total_distance = total_distance
                    stat_query[0].total_distance += total_distance
                    
                    #get track time
                    total_time = gc.total_time().total_seconds()
                    #convert time from seconds to string to match db format 
                    str_time = helper.sec_to_time(total_time)   
                    ts.total_time = str_time
                    #get current trip time           
                    global_time = helper.time_to_sec(stat_query[0].total_time)
                    #add time and return it to string
                    stat_query[0].total_time = helper.sec_to_time(global_time+total_time)
                    avr_speed = gc.avr_speed()
                    ts.avr_speed = avr_speed
                    
                    #set trip average if time was not zero
                    if(helper.time_to_sec(stat_query[0].total_time) != 0):
                        stat_query[0].avr_speed = stat_query[0].total_distance/(helper.time_to_sec(stat_query[0].total_time) * 0.000277778)
                    else:
                        stat_query[0].avr_speed = 0
                        
                    total_climb = gc.total_climb()
                    ts.total_climb = total_climb
                    
                    stat_query[0].total_climb += total_climb
                    #TODO something with max elevation 
                    max_elev = gc.max_elev()
                    ts.max_elev = max_elev
                    if max_elev > stat_query[0].max_elev:
                        stat_query[0].max_elev = max_elev
                   
                    stat_query[0].put()
                    ts.put()
            
                #change status to indicate that calculation is done
                track.status = ""
                track.put()
                
            
            except GpxDateFormatException:
                #if error occurs set status so appropriate message is shown 
                track.status = "Date in wrong format"
                track.put()

            except GpxFormatException:
                #if error occurs set status so appropriate message is shown 
                track.status = "Unable to parse gpx"
                track.put()
       
        

class StatHandler(webapp2.RequestHandler):
    '''
    Show statistics for one track
    '''
    def get(self):
        
        user = users.get_current_user()
        #check if user is logged in and creates appropriate url
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        #get specific track   
        track_key = self.request.get('track_id')
        trackk = ndb.Key(urlsafe=track_key)
        track = trackk.get()
        
        #get statistic
        track_stat_query= TrackStatistic.query(TrackStatistic.track == trackk)
        stat = track_stat_query.fetch()
       
        #set cookie value to this page url
        self.response.set_cookie('redirect_url', self.request.url)
               
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'stat': stat,'status':track.status,'back':self.request.referer}
        template = JINJA_ENVIRONMENT.get_template('templates/stat.html')
     
        self.response.write(template.render(template_values))

class DeleteTrackHandler(webapp2.RequestHandler):
    '''
    Delete track and all of his statistics
    '''
    def get(self):
        
        #get specific track    
        track_key = self.request.get('track_id')
        trakk = ndb.Key(urlsafe=track_key)
        track = trakk.get()
       

        #delete .gpx files from blobstore
        bolob = track.blob_key
        blobstore.delete(bolob)
        #subtract from global statistic
        stat_query = TrackStatistic.query(ancestor=track.key.parent()).fetch(1)
        
        
        #delete statistic
        for item in TrackStatistic.query(TrackStatistic.track == track.key):
            stat_query[0].total_distance -= item.total_distance
            
            global_time = helper.time_to_sec(stat_query[0].total_time)
            stat_query[0].total_time = helper.sec_to_time(global_time-helper.time_to_sec(item.total_time))
         
            if helper.time_to_sec(stat_query[0].total_time) != 0:
                stat_query[0].avr_speed = stat_query[0].total_distance/(helper.time_to_sec(stat_query[0].total_time) * 0.000277778)
            else:
                stat_query[0].avr_speed = 0
            stat_query[0].total_climb -= item.total_climb
            stat_query[0].put()
            item.key.delete()
            
        #delete track
        track.key.delete()
        

        self.redirect(self.request.referer)

class LoadTripHandler(webapp2.RequestHandler):
    '''
    Load trips. Used with ajax call
    '''
    def post(self):
        
        trips_query = Trip.query(Trip.visibility==True).order(-Trip.creation_date)
               
        #get cursor to fetch only new trips
        curs = Cursor(urlsafe=self.request.get('cursor'))
        trips, next_curs, more = trips_query.fetch_page(5, start_cursor=curs)
        tripsstats = {}
        #get all statistics
        for trip in trips:
            stat_query = TrackStatistic.query(ancestor=trip.key).fetch(1)
            tripsstats[trip.key]=stat_query
        data = self.create_trip_html(trips,tripsstats)
        # Create an array
        array = {'trips': data,'next_curs':next_curs.urlsafe(),'more':more}
       
        # Output the JSON
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(array))
          
    def create_trip_html(self,trips,stats):
        '''
        Creates html for new trips
        '''
        data=""
        for trip in trips:
            data +='<div class="p_box">'
            data +='<h2>' + trip.trip_name +'</h2>'
            data += '<p><b>From:</b> <i>'+str(trip.from_date)+'</i> <b>To:</b> <i>' +str(trip.to_date) +'</i></p>'
            if trip.trip_avatar:
                data +='<div class="image_frame"><img src="/img?img_id='+trip.key.urlsafe()+'" alt="image 3" /></div>'
            else:
                data +='<div class="image_frame"></div>'
              
            data += trip.description+'<a href="/trip?trip_id='+trip.key.urlsafe()+'" class="read_more"></a>'
            data += '<ol style="font-size:20px;">'
            data += '<li>Distance: <b>' + "{0:0.2f}".format(stats[trip.key][0].total_distance) + 'km</b></li>'
            if stats[trip.key][0].total_time:
                data += '<li>Total time: <b>' + stats[trip.key][0].total_time + '</b></li>'
            else:
                data += '<li>Total time: <b>/</b></li>'
            data += '<li>Avr speed: <b>' + "{0:0.2f}".format(stats[trip.key][0].avr_speed) + 'km/h</b></li>'
            data += '<li>Total climb: <b>' + "{0:0.0f}".format(stats[trip.key][0].total_climb) + 'm</b></li>'
#             if stats[trip.key][0].max_elev == -100:
#                 data += '<li>Max elevation: <b>/</b></li>'
#             else:
#                 data += '<li>Max elevation: <b>' + "{0:0.0f}".format(stats[trip.key][0].max_elev) + ' m</b></li>'
            
            data +='</ol>'
            data +='<div class="cleaner">Cities:'
            for city in trip.cities:
                data +='<a href="/cityinfo?city='+city+'" >'+city+',</a>' 
#             
            data +="</div></div>"
        return data
