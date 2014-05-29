'''
Created on May 27, 2014

@author: Va1iant
'''

# [START imports]
import os
import urllib

from google.appengine.ext import ndb
from webapp2_extras import json
from datetime import datetime, timedelta

import webapp2
import logging


# [END imports]

# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def session_key(userId):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('User', userId)

class Session(ndb.Model):
    live = ndb.BooleanProperty()
    tdist = ndb.FloatProperty()
    tstartstamp = ndb.DateTimeProperty(auto_now_add=True)
    tendstamp = ndb.DateTimeProperty(auto_now_add=True)
    
class Point(ndb.Model):
    lat = ndb.FloatProperty()
    lng = ndb.FloatProperty()
    tdist = ndb.FloatProperty()
    tstamp = ndb.DateTimeProperty(auto_now_add=True)
    
class StartSession(webapp2.RequestHandler):
    
    def get(self, userId):
        
        userid_lower = userId.lower()
    
        newSession = Session(parent=session_key(userid_lower))
        
        'first time create always have this as true until user end it'
        newSession.live = True
        newSession.tdist = 0

        newSession.put()
        
        self.response.content_type = 'application/json'
        obj = {
            'session_id': str(newSession.key.id()),
          } 
        self.response.write(json.encode(obj))
    
    post = get
        

class PutSession(webapp2.RequestHandler):
    
    def get(self, userId, sessionId, lat, lng, tdist):
        
        userid_lower = userId.lower()
        
        targetSession = Session.get_by_id(int(sessionId), parent=session_key(userid_lower))
        
        'check if this a live session'
        'if not return 410 Gone'
        if not targetSession.live:
            self.abort(410)
            
        newPoint = Point(parent=targetSession.key,
                         lat=float(lat),
                         lng=float(lng),
                         tdist=float(tdist))
        
        newPoint.put()
        
    post = get    
        
        
class EndSession(webapp2.RequestHandler):
    
    def get(self, userId, sessionId):
        
        userid_lower = userId.lower()
        
        targetSession = Session.get_by_id(int(sessionId), parent=session_key(userid_lower))
        
        'check if this a live session'
        'if not return 410 Gone'
        if not targetSession.live:
            self.abort(410)
            
        targetSession.live = False
        
        latest = Point.query(ancestor=targetSession.key).order(-Point.tstamp).get()
        if latest:
            targetSession.tdist = latest.tdist
            
        targetSession.tendstamp = datetime.now();

        targetSession.put()

    post = get


application = webapp2.WSGIApplication([
    ('/mapi/start/user/(.*)', StartSession),
    ('/mapi/put/user/(.*)/session/(.*)/lat/(.*)/lng/(.*)/tdist/(.*)', PutSession),
    ('/mapi/end/user/(.*)/session/(.*)', EndSession),
], debug=True)
