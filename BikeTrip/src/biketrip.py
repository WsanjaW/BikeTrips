import webapp2

from handlers import ShowTrips,AddTrip,ImageHandler,CityInfo,OneTrip,UploadHandler,DownloadHandler,UpdateTripHandler,DeleteTripHandler,StatHandler


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

], debug=True)