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
from webapp2_extras import sessions


from datetime import datetime,timedelta
from models import Trip,Track,TrackStatistic,Tags
from gpxManager import GPXReader,GPXCalculation
from errors import GpxFormatException,GpxDateFormatException


#set jinja templates environment
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
#set number of trips to show on page
PAGE_SIZE = 10



#Base Classes
class BaseHandler(webapp2.RequestHandler):
    '''
    Handles user
    '''
    def get_user(self):
        user = users.get_current_user()
        id ='0'
        #check if user is logged in and creates appropriate url
        if user:
            id = user.user_id()
            url = users.create_logout_url('/')
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        return user,id,url,url_linktext

class BaseSessionHandler(BaseHandler):
    '''
    Session Handling class, gets the store, dispatches the request
    '''
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

class TripManagerBaseHandler(BaseSessionHandler):
    '''
    Base handler for all handlers in trip manager section
    Contains methods used on every page
    
    '''
    
    def create_trip_tree(self,id):
        '''
        Returns tree structure of trips
        '''
        if self.session.get('locationfilter'):
            locationfilter = self.session.get('locationfilter')
            locationfilter = [str(x) for x in locationfilter]
        else:
            locationfilter = []
        if self.session.get('typefilter'):
            typefilter = self.session.get('typefilter')
            typefilter = [str(x) for x in typefilter]
        else:
            typefilter = []
        if self.session.get('seasonfilter'):
            seasonfilter = self.session.get('seasonfilter')
            seasonfilter = [str(x) for x in seasonfilter]
        else:
            seasonfilter = []
        #creates tree structure of trips
        tree = helper.make_track_tree(id,locationfilter,typefilter,seasonfilter)
        return tree
    
    
    def get_all_tags(self,id):
        '''
        Returns all tags for specified user
        '''
        #get users tags
        tags_query = Tags.query(ancestor=helper.trip_key(id))
        tags = tags_query.fetch(1)
        if tags:
            tags = tags[0]
            location = [str(x) for x in tags.location]
            type = [str(x) for x in tags.type]
            season = [str(x) for x in tags.season]
        else:
            location = []
            type = []
            season = []
        tags = []
        tags.append(location)
        tags.append(type)
        tags.append(season)
        return tags
    
    def get_location_filters(self):
        '''
        Returns location filters from session
        '''
        if self.session.get('locationfilter'):
                loc = [str(x) for x in self.session['locationfilter']]
                return loc
        else:
            return []
    def get_type_filters(self):
        '''
        Returns type filters from session
        '''
        if self.session.get('typefilter'):
                ty = [str(x) for x in self.session['typefilter']]
                return ty
        else:
            return []
    def get_season_filters(self):
        '''
        Returns season filters from session
        '''
        if self.session.get('seasonfilter'):
                se = [str(x) for x in self.session['seasonfilter']]
                return se
        else:
            return []

#Public part classes
class ShowTrips(BaseHandler):
    '''
    Shows either newest trips or trips for logged in user
    '''
    
    def get(self):
        
        user,id,url,url_linktext = self.get_user()
        
        #parameter mytrips = True if only users trips should be shown  
        mytrips = self.request.get('mytrips')
        
        if mytrips == 'True':
            trips_query = Trip.query(ancestor=helper.trip_key(id)).order(-Trip.creation_date)
        else:
            trips_query = Trip.query(Trip.visibility==True).order(-Trip.creation_date)
              
        trips, next_curs, more = trips_query.fetch_page(PAGE_SIZE)
        
        #return index page
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'trips':trips,'cursor':next_curs,
                           'more':more,'mytrips':mytrips}
        template = JINJA_ENVIRONMENT.get_template('templates/new/alltrips.html')
        self.response.write(template.render(template_values))
    
class OneTrip(BaseHandler):
    '''
    Shows one trip, with id sent in url, and tracks for that trip
    Shows form for uploading gpx files, statistic for whole trip, and map of cities
    '''
    def get(self):
        
        upload_url = blobstore.create_upload_url('/tripmanager/upload')

        user,_,url,url_linktext = self.get_user()
        
        #get specific trip     
        trip_key = self.request.get('trip_id')
        tripk = ndb.Key(urlsafe=trip_key)
        trip = tripk.get()
       
        #get id of user for given trip
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
                  
        #get trip cities
        cities = trip.cities
        
        #create list of lon,lat pares for every city
        cordinates = []
        for city in cities:
            try:
                city = city.lower().replace(" ", "+")
                api_url = "http://api.geonames.org/searchJSON?formatted=true&name={0}&maxRows=1&lang=es&username=wsanjaw&style=short".format(city)
                result = urlfetch.fetch(api_url)
                cordinates.append(helper.procesCity(result.content))
            except:
                cordinates.append([0,0])
        
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'trip':trip,'upload':upload_url,
                           'tracks':tracks,'blobs':bli,'num':num,'trip_user':trip_user,'stats':stat_query,'cordinates':cordinates}
        template = JINJA_ENVIRONMENT.get_template('templates/new/onetrip.html')
        
        #set cookie value to this page url
        self.response.set_cookie('redirect_url', self.request.url)

        self.response.write(template.render(template_values))

class StatHandler(BaseHandler):
    '''
    Show statistics for one track
    '''
    def get(self):
        
        user,_,url,url_linktext = self.get_user() 
        
        #get specific track   
        track_key = self.request.get('track_id')
        trackk = ndb.Key(urlsafe=track_key)
        track = trackk.get()
        
        #get statistic
        track_stat_query= TrackStatistic.query(ancestor=trackk)
        stat = track_stat_query.fetch()
                
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'stat': stat,'status':track.status,
                           'back':self.request.referer,'trip': trackk.parent().get(),"track":track,
                           "blob":BlobInfo(track.blob_key)}
        template = JINJA_ENVIRONMENT.get_template('templates/new/stat.html')
     
        self.response.write(template.render(template_values))
        
class ChartsHandler(BaseHandler):
    '''
    Get data for creating charts
    '''
    def get(self):
        
        user,_,url,url_linktext = self.get_user()
        
        #get specific trip     
        trip_key = self.request.get('trip_id')
        tripk = ndb.Key(urlsafe=trip_key)
        trip = tripk.get()
               
        #get statistic
        track_stat_query= TrackStatistic.query(ancestor=tripk)
        stats = track_stat_query.fetch()
        #create data for total climb chart and bubble chart
        climb_data = []
        bubble_data = []
        for s in stats:
            climb_data.append([s.name,s.total_climb])
            bubble_data.append([s.key.parent().id(),s.name[0:3].upper(),s.total_distance,s.total_climb,"tracks",helper.time_to_sec(s.total_time)])
        
       
        
        
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,
                           'climb_data':map(json.dumps, climb_data),'bubble_data':map(json.dumps, bubble_data)}
        template = JINJA_ENVIRONMENT.get_template('templates/charts.html')
     
        self.response.write(template.render(template_values))

class SearchHandler(BaseHandler):
    '''
    TODO implement
    '''
    def get(self):
        user,_,url,url_linktext = self.get_user()
        
        #get filters from url
        location = helper.creatList(self.request.get("locationfilter"))
        type = helper.creatList(self.request.get("typefilter"))
        season = helper.creatList(self.request.get("seasonfilter"))
        
        #get all trips
        trips_query = Trip.query(Trip.visibility==True)
        if location != ['']:
            trips_query = trips_query.filter(Trip.trip_tags.location.IN(location))
        if type != ['']:
            trips_query = trips_query.filter(Trip.trip_tags.type.IN(type))
        if season != ['']:
            trips_query = trips_query.filter(Trip.trip_tags.season.IN(season))
    
        trips = trips_query.fetch()
        
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,
                          'location':location,'type':type,'season':season,'trips':trips}
        template = JINJA_ENVIRONMENT.get_template('templates/new/search.html')
     
        self.response.write(template.render(template_values))
    

# Trip Manager classes(private part)
class AddTrip(TripManagerBaseHandler):
    '''
    Handles form for adding trip
    '''
    def get(self):
        '''
        Show form
        '''

        user,id,url,url_linktext = self.get_user()  
         
        tree = self.create_trip_tree(id)
        
        tags = self.get_all_tags(id)
        
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'tree':tree,
                           'location':self.get_location_filters(),'type':self.get_type_filters(),'season':self.get_season_filters(),
                           'sug_location':tags[0],'sug_type':tags[1],'sug_season':tags[2]}
        template = JINJA_ENVIRONMENT.get_template('templates/new/addtrip.html')
        self.response.write(template.render(template_values))
    
    def post(self):
        '''
        Adds trip to datastore
        '''
        
        _,id,_,_ = self.get_user()
        
        #TODO some checking      
        trip = Trip(parent=helper.trip_key(id))
        trip.trip_name = self.request.get('trip_name')
        
        trip.description = self.request.get('description')
        trip.cities =  self.get_cities(self.request.get('cities'))
        avatar = self.request.get('img')
        if  avatar:
            trip.trip_avatar = avatar
        
        
        try:
            trip.from_date = datetime.strptime( self.request.get('from_date'), '%d/%m/%Y')  
            trip.to_date = datetime.strptime(self.request.get('to_date'), '%d/%m/%Y')
        except:
            try:
                trip.from_date = datetime.strptime( self.request.get('from_date'), '%Y-%m-%d')  
                trip.to_date = datetime.strptime(self.request.get('to_date'), '%Y-%m-%d')
            except:
                trip.from_date = datetime.strptime( '2000-01-01', '%Y-%m-%d')  
                trip.to_date = datetime.strptime('2000-01-01', '%Y-%m-%d')
        
        if self.request.get('visibility') == 'True':
            trip.visibility = True
        else:
            trip.visibility = False
        
        #create statistic for trip 
        trip.trip_statistic = TrackStatistic(name="Trip Stat",total_distance=0,total_time="",
                                             avr_speed=0,total_climb=0,max_elev=-100)
        
        #crete tags for trip
        locationl = helper.creatList(self.request.get('location'))
        typel = helper.creatList(self.request.get('type'))
        seasonl = helper.creatList(self.request.get('season'))
        trip.trip_tags = Tags(location=locationl,type=typel,season=seasonl)
        
        trip.put()
               
        #put new tags in users tags
        tags_query = Tags.query(ancestor=helper.trip_key(id))
        tags = tags_query.fetch(1)
        if tags:
            tags = tags[0]
            tags.location = helper.union(tags.location,locationl)
            tags.type = helper.union(tags.type,typel)
            tags.season = helper.union(tags.season,seasonl)
                      
        else:
            new_loc_tags = locationl
            new_type_tags = typel
            new_seasion_tags = seasonl
            tags = Tags(parent=helper.trip_key(id),location=new_loc_tags,type=new_type_tags,season=new_seasion_tags)
        
        tags.put()
        
        #redirect to mytrips because showing all tips will only be consistent in scope of user
        # and only eventually consistent for whole datastore  
        self.redirect('/tripmanager')
    
    def get_cities(self,allCities):
        '''
        Create list of cities from string
        '''
        cities = allCities.split(',')
        cities = [x.strip() for x in cities]
        return cities

class UpdateTripHandler(TripManagerBaseHandler):
    '''
    Handler for updating trip name and cities
    '''
    def post(self):
        
        _,id,_,_ = self.get_user()
        
        #get specific trip     
        trip_key = self.request.get('trip_id')
        tripk = ndb.Key(urlsafe=trip_key)
        trip = tripk.get()    
        
        #get new values
        new_name = self.request.get('trip_name')
        if new_name:         
            trip.trip_name = new_name
        new_description = self.request.get('description')
        if new_description:
            trip.description = new_description
            
        new_cities =  self.get_cities(self.request.get('cities'))
        if new_cities:
            trip.cities = new_cities
            
        new_avatar = self.request.get('img')
        if  new_avatar:
            trip.trip_avatar = new_avatar
        
        new_from_date = self.request.get('from_date') 
        if new_from_date:
            try:
                new_from_date = datetime.strptime( new_from_date, '%d/%m/%Y')  
            except:
                try:
                    new_from_date = datetime.strptime( new_from_date, '%Y-%m-%d')  
                except:
                        new_from_date = datetime.strptime( '2000-01-01', '%Y-%m-%d')  
            trip.from_date = new_from_date
        
        new_to_date = self.request.get('to_date')
        if new_to_date:
            try:
                new_to_date = datetime.strptime( new_to_date, '%d/%m/%Y')  
            except:
                try:
                    new_to_date = datetime.strptime( new_to_date, '%Y-%m-%d')  
                except:
                    new_to_date = datetime.strptime( '2000-01-01', '%Y-%m-%d')  
            trip.to_date = new_to_date
        
        if self.request.get('visibility') == 'True':
            trip.visibility = True
        else:
            trip.visibility = False 
        
        #crete tags for trip
        locationl = helper.creatList(self.request.get('location'))
        typel = helper.creatList(self.request.get('type'))
        seasonl = helper.creatList(self.request.get('season'))
        trip.trip_tags = Tags(location=locationl,type=typel,season=seasonl)
        
        #put new tags in users tags
        tags_query = Tags.query(ancestor=helper.trip_key(id))
        tags = tags_query.fetch(1)
        if tags:
            tags = tags[0]
            tags.location = helper.union(tags.location,locationl)
            tags.type = helper.union(tags.type,typel)
            tags.season = helper.union(tags.season,seasonl)
                      
        else:
            new_loc_tags = locationl
            new_type_tags = typel
            new_seasion_tags = seasonl
            tags = Tags(parent=helper.trip_key(id),location=new_loc_tags,type=new_type_tags,season=new_seasion_tags)
        
        tags.put()
        
        trip.put()
        
       
        self.redirect('/tripmanager/onetrip?trip_id='+ tripk.urlsafe())
    
    def get_cities(self,allCities):
        '''
        Create list of cities from string
        '''
        cities = allCities.split(',')
        cities = [x.strip() for x in cities]
        return cities

class DeleteTripHandler(TripManagerBaseHandler):
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
            for item in TrackStatistic.query(ancestor=track.key):
                item.key.delete()
            
            #delete track
            track.key.delete()
        
        #redirect to mytrips because showing all tips will only be consistent in scope of user
        # and only eventually consistent for whole datastore  
        trip.key.delete()
        
        self.redirect('/tripmanager')

class DeleteTrackHandler(TripManagerBaseHandler):
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
        
        #delete statistic
        for item in TrackStatistic.query(ancestor=track.key):
            item.key.delete()
            
        #delete track
        track.key.delete()
        
        #calculate trip statistic
        helper.calculate_trip_stat(track.key.parent())

        self.redirect("/tripmanager/onetrip?trip_id="+track.key.parent().urlsafe())

class MyTripManagerHandler(TripManagerBaseHandler):
    '''
    Shows first page of trip manager
    '''
    def get(self):
        
        user,id,url,url_linktext = self.get_user()  
         
        tree = self.create_trip_tree(id)
        tags = self.get_all_tags(id)
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'tree':tree,
                           'location':self.get_location_filters(),'type':self.get_type_filters(),'season':self.get_season_filters(),
                           'sug_location':tags[0],'sug_type':tags[1],'sug_season':tags[2]}
        template = JINJA_ENVIRONMENT.get_template('templates/new/tripmanager.html')
     
        self.response.write(template.render(template_values))
        
class OneTripManagerHandler(TripManagerBaseHandler):
    '''
    Shows page with one trip 
    '''
    def get(self):
        
        upload_url = blobstore.create_upload_url('/tripmanager/upload')
        
        user,id,url,url_linktext = self.get_user()  
         
        tree = self.create_trip_tree(id)
        
        #get specific trip     
        trip_key = self.request.get('trip_id')
        tripk = ndb.Key(urlsafe=trip_key)
        trip = tripk.get()
        
        #get tracks for trip
        track_query = Track.query(ancestor=tripk).order(-Track.creation_date)
        tracks = track_query.fetch(20)
        #get number of tracks
        num = len(tracks)       
        
        #get blobInfo objects from blob_key
        bli = []
        for track in tracks:
            bli.append(BlobInfo(track.blob_key))
                  
        #get trip cities
        cities = trip.cities
        #create list of lon,lat pares for every city
        cordinates = []
        cities_string = ""
        for city in cities:
            if city == cities[-1]:
                cities_string += str(city)
            else:
                cities_string += str(city)+","
            city = city.lower().replace(" ", "+")
            try:
                api_url = "http://api.geonames.org/searchJSON?formatted=true&name={0}&maxRows=1&lang=es&username=wsanjaw&style=short".format(city)
                result = urlfetch.fetch(api_url)
                cordinates.append(helper.procesCity(result.content)) 
            except:
                cordinates.append([0,0])
        #get statistic
        track_stat_query= TrackStatistic.query(ancestor=tripk)
        stats = track_stat_query.fetch()
        
        #create data for total climb chart and bubble chart
        climb_data = []
        bubble_data = []
        for s in stats:
            climb_data.append([s.name,s.total_climb])
            bubble_data.append([s.key.parent().id(),s.name[0:3].upper(),s.total_distance,s.total_climb,"tracks",helper.time_to_sec(s.total_time)])
        
        tags = self.get_all_tags(id)
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'tree':tree,'trip':trip,
                           'climb_data':map(json.dumps, climb_data),'bubble_data':map(json.dumps, bubble_data),
                           'tracks':tracks,'blobs':bli,'num':num,'stats':track_stat_query,'cordinates':cordinates,
                           'upload':upload_url,'cities':cities_string,'sug_location':tags[0],'sug_type':tags[1],'sug_season':tags[2],
                           'location':self.get_location_filters(),'type':self.get_type_filters(),'season':self.get_season_filters(),
                           'trip_loc':[str(x) for x in trip.trip_tags.location],'trip_type':[str(x) for x in trip.trip_tags.type],
                           'trip_ses':[str(x) for x in trip.trip_tags.season]}
        template = JINJA_ENVIRONMENT.get_template('templates/new/onetriptrackmanager.html')
     
        self.response.write(template.render(template_values))
        
class OneTrackManagerHandler(TripManagerBaseHandler):
    '''
    Shows one track
    '''
    def get(self):
        
        user,id,url,url_linktext = self.get_user()  
         
        tree = self.create_trip_tree(id)

        #get specific track   
        track_key = self.request.get('track_id')
        trackk = ndb.Key(urlsafe=track_key)
        track = trackk.get()
        
        #get statistic
        track_stat_query= TrackStatistic.query(ancestor=trackk)
        stat = track_stat_query.fetch()
        
        tags = self.get_all_tags(id)
        
        #create template
        template_values = {'user': user, 'url': url, 'url_linktext': url_linktext,'tree':tree,'track':track,
                           'stat':stat,'trip': trackk.parent().get(),"blob":BlobInfo(track.blob_key),'status':track.status,
                           'location':self.get_location_filters(),'type':self.get_type_filters(),'season':self.get_season_filters(),
                           'sug_location':tags[0],'sug_type':tags[1],'sug_season':tags[2]}
        template = JINJA_ENVIRONMENT.get_template('templates/new/onetrack.html')
     
        self.response.write(template.render(template_values))


# Helper handlers
class FilterHandler(BaseSessionHandler):
    '''
    Gets filters and stores them in session
    '''
    def post(self):
        
        
        if self.request.get('locationfilter'):
            self.session['locationfilter'] = helper.creatList(self.request.get('locationfilter'))
        else:
            if self.session.get('locationfilter'):
                del self.session['locationfilter']
        if self.request.get('typefilter'):
            self.session['typefilter'] = helper.creatList(self.request.get('typefilter'))
        else:
            if self.session.get('typefilter'):
                del self.session['typefilter']
                
        if self.request.get('seasonfilter'):
            self.session['seasonfilter'] = helper.creatList(self.request.get('seasonfilter'))
        else:
            if self.session.get('seasonfilter'):
                del self.session['seasonfilter']
        
        self.redirect(self.request.referer)


class LoadTripHandler(webapp2.RequestHandler):
    '''
    Load trips. Used with ajax call
    '''
    def post(self):
        
        trips_query = Trip.query(Trip.visibility==True).order(-Trip.creation_date)
               
        #get cursor to fetch only new trips
        curs = Cursor(urlsafe=self.request.get('cursor'))
        trips, next_curs, more = trips_query.fetch_page(PAGE_SIZE, start_cursor=curs)
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
            data +='''<div class="panel panel-default">
                                            <div class="panel-body" style="{ word-wrap: break-word;}">
                                            
                                                <li>
                                                    <div class="row">
                                                        <div class="col-md-2">'''
            if trip.trip_avatar:
                data+='''                                  <a class="pull-left" href="#">
                                                                <img class="media-object" src="/img?img_id='''+trip.key.urlsafe()+'''" alt="...">
                                                            </a>'''
                
                                                            
            data+='''                                          </div>
                                                        <div class="col-md-8">
                                                            <a href="/trip?trip_id='''+ trip.key.urlsafe()+'''"><h4 class="media-heading">'''+trip.trip_name + '''</h4></a>
                                                            <div class="row">
                                                                <div class="col-md-4">
                                                                    <p><b>From:</b> <i>''' +str(trip.from_date) + '''</i> <b>To:</b> <i>'''+ str(trip.to_date) +'''
                                                                    </i></p>'''+ trip.description + '''
                                                                </div>
                                                                <div class="col-md-4">
                                                                    <b><i>Trip Statistic</i></b>
                                                                    <ol>
                                                                        <li>Distance: <b> ''' + "{0:0.2f}".format(trip.trip_statistic.total_distance)+'''
                                                                         km</b></li>'''
            if trip.trip_statistic.total_time:
                data += '''
                                                                        <li>Total time: <b>''' + trip.trip_statistic.total_time+ '''</b></li>'''
            else:
                data +='''                                                     <li>Total time: <b>/</b></li>'''
            data +='''
                                                                     
                                                                        <li>Avr speed: <b>''' + "{0:0.2f}".format(trip.trip_statistic.avr_speed)+''' km/h</b></li>
                                                                        <li>Total climb: <b>''' +"{0:0.0f}".format(trip.trip_statistic.total_climb) + '''
                                                                         m</b></li>'''
            if trip.trip_statistic.max_elev == -100:
                data +='''
                                                                         <li>Max elevation: <b>/</b></li> '''
            else:
                data+='''
                                                                      
                                                                        <li>Max elevation: <b>'''+"{0:0.0f}".format(trip.trip_statistic.max_elev)+''' m</b></li>'''
            data +='''                                                    
                                                                    </ol>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-8">
                                                            Cities:''' 
            for city in trip.cities:
                data +='''
                                                                     <a href="/cityinfo?city=''' +city + '''" >''' + city + ''',</a> '''
                                                             
            data +='''                                             </div>
                                                    </div>
                                                </li>
                                            
                                            </div>
                                            <div class="panel-footer">
                                                <a href="#">ffffffsd</a> <a href="#">ffffffsd</a>
                                            </div>'''
        return data

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
        track = Track(parent=tripk,track_name=self.request.get('track_name'),blob_key=blob_info.key()) 
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
        
        #to ensure immutability
        track_stat_query= TrackStatistic.query(ancestor=track_key)
        stat = track_stat_query.fetch(1)
        if stat == []:

            #read data from uploaded file
            blob_reader = blobstore.BlobReader(track.blob_key)
            data = blob_reader.read()
            try:
                g = GPXReader()
                a = g.parse_gpx(data)
        
                for item in a:
            
                    gc = GPXCalculation(item)
                    ts = TrackStatistic(parent=track.key,name=item.name)
                    total_distance = gc.calculate_distance()
                    ts.total_distance = total_distance
                    #get track time
                    total_time = gc.total_time().total_seconds()
                    #convert time from seconds to string to match db format 
                    str_time = helper.sec_to_time(total_time)   
                    ts.total_time = str_time
                    avr_speed = gc.avr_speed()
                    ts.avr_speed = avr_speed
                    total_climb = gc.total_climb()
                    ts.total_climb = total_climb
                    max_elev = gc.max_elev()
                    ts.max_elev = max_elev
                   
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
            
            #if track is added to db calculate statistic for whole trip
            helper.calculate_trip_stat(track.key.parent())