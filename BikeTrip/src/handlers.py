'''
Created on 28.01.2014.

@author: Sanja
'''
import os
import webapp2
import jinja2
import json
import urllib

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.blobstore import BlobInfo

from datetime import datetime
from models import Trip,Track


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
        
        #TODO something other then 10 
        trips = trips_query.fetch(10)

        #return index page
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'trips':trips}
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.write(template.render(template_values))
    
   
    
class AddTrip(webapp2.RequestHandler):
    '''
    Handles form for adding trip
    '''
    def get(self):

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
        
        self.redirect('/')
    
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
        return (data['geonames'][0]['lat'],data['geonames'][0]['lng'])

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
    Shows form for uploading gpx files
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
        track_query = Track.query(ancestor=tripk)
        tracks = track_query.fetch(10)
        #get number of tracks
        num = len(tracks)
        
        #get blobInfo objects from blob_key
        bli = []
        for track in tracks:
            bli.append(BlobInfo(track.blob_key))
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'trip':trip,'upload':upload_url,
                           'tracks':tracks,'blobs':bli,'num':num,'trip_user':trip_user}
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
        #create new track which parent is current track 
        track = Track(parent=tripk,track_name=self.request.get('trip_name'),blob_key=blob_info.key())   
        track.put()
        
        #get cookie with value of page from where upload is started
        cookie_value = self.request.cookies.get('redirect_url')
        self.redirect(str(cookie_value))


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

class UpdateTripHandler(blobstore_handlers.BlobstoreUploadHandler):
    '''
    Handler for uploading gpx file to blobstore
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
