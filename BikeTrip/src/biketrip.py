import webapp2

from handlers import ShowTrips,AddTrip,ImageHandler,CityInfo


application = webapp2.WSGIApplication([
    ('/', ShowTrips),
    ('/addtrip',AddTrip),
     ('/alltrips',ShowTrips),
     ('/img',ImageHandler),
     ('/cityinfo',CityInfo),
], debug=True)