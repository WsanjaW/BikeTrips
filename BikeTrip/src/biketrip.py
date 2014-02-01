import webapp2

from handlers import ShowTrips,AddTrip,ImageHandler,CityInfo,OneTrip,UploadHandler,DownloadHandler,UpdateTripHandler


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

], debug=True)