import webapp2

from handlers import ShowTrips,AddTrip,ImageHandler
from handlers import OneTrip,UploadHandler,DownloadHandler
from handlers import UpdateTripHandler,DeleteTripHandler,StatHandler
from handlers import DeleteTrackHandler,LoadTripHandler,ChartsHandler
from handlers import MyTripManagerHandler,OneTripManagerHandler
from handlers import OneTrackManagerHandler,FilterHandler,SearchHandler
from webapp2_extras import sessions

#This is needed to configure the session secret key
#Runs first in the whole application
myconfig_dict = {}
myconfig_dict['webapp2_extras.sessions'] = {
    'secret_key': 'fdgb46bjutjikiukbyujyb8bjyhgh7',
}


application = webapp2.WSGIApplication([
    ('/', ShowTrips),
    ('/tripmanager/addtrip',AddTrip),
    ('/alltrips',ShowTrips),
    ('/img',ImageHandler),
    ('/trip',OneTrip),
    ('/tripmanager/upload', UploadHandler),
    ('/serve/([^/]+)?', DownloadHandler),
    ('/tripmanager/updatetrip', UpdateTripHandler),
    ('/tripmanager/deleteTrip', DeleteTripHandler),
    ('/stat', StatHandler),
    ('/tripmanager/deleteTrack',DeleteTrackHandler),
    ('/loadtrips',LoadTripHandler),
    ('/charts',ChartsHandler),
    ('/tripmanager/onetrip',OneTripManagerHandler),
    ('/tripmanager',MyTripManagerHandler),
    ('/tripmanager/onetrack',OneTrackManagerHandler),
    ('/tripmanager/filter',FilterHandler),
    ('/search',SearchHandler),
     
],config=myconfig_dict, debug=True)