import webapp2

from handlers import ShowTrips,AddTrip,ImageHandler,CityInfo,OneTrip,UploadHandler,DownloadHandler,UpdateTripHandler,DeleteTripHandler,StatHandler,DeleteTrackHandler,LoadTripHandler,ChartsHandler


application = webapp2.WSGIApplication([
    ('/', ShowTrips),
    ('/addtrip',AddTrip),
     ('/alltrips',ShowTrips),
     ('/img',ImageHandler),
     ('/cityinfo',CityInfo),
     ('/trip',OneTrip),
     ('/upload', UploadHandler),
     ('/serve/([^/]+)?', DownloadHandler),
     ('/update', UpdateTripHandler),
     ('/deleteTrip', DeleteTripHandler),
     ('/stat', StatHandler),
     ('/deleteTrack',DeleteTrackHandler),
     ('/loadtrips',LoadTripHandler),
     ('/charts',ChartsHandler),
], debug=True)