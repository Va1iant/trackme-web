# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from mapi import Session, Point, session_key
from webapp2_extras import json
from datetime import datetime, timedelta

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_USERID = 'Va1iant'


def td_format(td_object):
    
    seconds = int(td_object.total_seconds())
    periods = [
                ('y', 60 * 60 * 24 * 365),
                ('m', 60 * 60 * 24 * 30),
                ('d', 60 * 60 * 24),
                ('h', 60 * 60),
                ('m', 60),
                ('s', 1)
                ]
    
    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value , seconds = divmod(seconds, period_seconds)
            if period_value == 1:
                    strings.append("%s %s" % (period_value, period_name))
            else:
                    strings.append("%s %s" % (period_value, period_name))
    
    return ", ".join(strings)

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        info = ''
        info += '<html>'
        info += 'See history:<br />'
        info += '/history/user/(user_id) <br />'
        info += 'See live session:<br />'
        info += '/live/user/(user_id) <br />'
        info += '</html>'    
        self.response.write(info)
# [END main_page]


class History(webapp2.RequestHandler):
    
    def get(self, userId):
        
        userid_lower = userId.lower()
        
        sessions_query = Session.query(Session.live == False, ancestor=session_key(userid_lower)).order(-Session.tstartstamp)
        sessions = sessions_query.fetch()
        
        session_lst = []
        
        for session in sessions:
            
            points_query = Point.query(ancestor=session.key).order(Point.tstamp)
            points = points_query.fetch()
            
            points_arr = [dict(lat=point.lat, lng=point.lng, tdist=point.tdist, tstamp=str(point.tstamp)) for point in points]
            
            obj = {
                'tdist': session.tdist,
                'tstartstamp': session.tstartstamp.strftime('%Y/%m/%d %H:%M:%S'),
                'duration': td_format(session.tendstamp - session.tstartstamp),
                'points': points_arr
            } 

            session_lst.append(obj)
            
        
        template_values = {
            'sessions': session_lst,
            'userId': userId.title()
        }
        
        template = JINJA_ENVIRONMENT.get_template('history.html')
        self.response.write(template.render(template_values))

        # self.response.write('History')
    
class LiveSession(webapp2.RequestHandler):
    
    def get(self, userId):
        
        template_values = {
            'userId': userId.title()
        }
        
        template = JINJA_ENVIRONMENT.get_template('live.html')
        self.response.write(template.render(template_values))
        
        
        
class SessionData(webapp2.RequestHandler):
    
    def get(self, userId):
        
        userid_lower = userId.lower()
        
        sessions_query = Session.query(Session.live == False, ancestor=session_key(userid_lower)).order(-Session.tstartstamp)
        sessions = sessions_query.fetch()
        
        lst = []
        
        for session in sessions:
            
            points_query = Point.query(ancestor=session.key).order(Point.tstamp)
            points = points_query.fetch()
            
            points_str = [dict(lat=point.lat, lng=point.lng, tdist=point.tdist, tstamp=str(point.tstamp)) for point in points]
            
            obj = {
                'tdist': session.tdist,
                'tstamp': str(session.tstamp),
                'points': points_str
            } 
            
            lst.append(obj)

        self.response.content_type = 'application/json'
        self.response.write(json.encode(lst))
        
def toEpoch(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return (delta.seconds + delta.days * 24 * 3600)

def toDatetime(epoch):
    delta = timedelta(seconds=int(epoch))
    return datetime.utcfromtimestamp(0) + delta
    

class LiveInit(webapp2.RequestHandler):
    
    def get(self, userId):
        
        userid_lower = userId.lower()
        
        latest_session = Session.query(ancestor=session_key(userid_lower)).order(-Session.tstartstamp).get()
        if latest_session:
            if not latest_session.live:
                self.abort(410, body_template='')
        else:
            self.abort(410, body_template='')

            
        # session is active!
        points_query = Point.query(ancestor=latest_session.key).order(Point.tstamp)
        points = points_query.fetch()
        
        points_str = [dict(lat=point.lat, lng=point.lng, tdist=point.tdist, tstamp=point.tstamp.strftime('%Y/%m/%d %H:%M:%S')) 
                      for point in points]
        
        self.response.content_type = 'application/json'
        self.response.write(json.encode(points_str)) 
        
        
class LiveUpdate(webapp2.RequestHandler):
    
    def get(self, userId):
        
        userid_lower = userId.lower()
        
        latest_session = Session.query(ancestor=session_key(userid_lower)).order(-Session.tstartstamp).get()
        if latest_session:
            if not latest_session.live:
                self.abort(410, body_template='')
        else:
            self.abort(410, body_template='')

        # session is active!
        points_query = Point.query(ancestor=latest_session.key).order(-Point.tstamp)
        points = points_query.fetch(1)
        if points:
            points_str = [dict(lat=point.lat, lng=point.lng, tdist=point.tdist, tstamp=point.tstamp.strftime('%Y/%m/%d %H:%M:%S')) 
                     for point in points]
        
            self.response.content_type = 'application/json'
            self.response.write(json.encode(points_str)) 
         
        # return nothing if no point    
        self.response.content_type = 'application/json'
              

application = webapp2.WSGIApplication([  
    ('/bapi/live/user/(.*)/lastpoint', LiveUpdate),
    ('/bapi/live/user/(.*)', LiveInit),
    ('/live/user/(.*)', LiveSession),
    ('/history/user/(.*)', History),
    ('/sessions/user/(.*)', SessionData),
    ('/', MainPage),
], debug=True)
