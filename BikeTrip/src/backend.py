import webapp2

from handlers import TrackParserHandler


application = webapp2.WSGIApplication([
     ('/worker', TrackParserHandler),
    

], debug=True)