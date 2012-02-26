#!/usr/bin/env python
import time
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado_utils.routes import route
from tornado.web import authenticated
from handlers import NoticeHandler
from tornado.escape import json_decode,json_encode
from tornado.httpclient import HTTPError

@route(r'/update')
class MainHandler(NoticeHandler):
    def get_data(self,callback):        
        [unread_data ,count] = self.noti.get_unread(self.current_user.uid,page_size=10);
        unread = self.parse_notis(unread_data)
        callback([unread,count])
    @tornado.web.asynchronous 
    @authenticated
    def post(self,*m,**kw):
        #TODO: timeout 30
        atonce = bool( self.get_argument('atonce',default=False))
        if atonce :
            tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 1, lambda: self.get_data(callback=self.wait))
        else : 
            tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 50, lambda: self.get_data(callback=self.wait))
    def get(self,*m,**kw):
        raise HTTPError(405)
    
    def wait(self, result):
        self.json_write(code='201',data=result)
        self.finish()