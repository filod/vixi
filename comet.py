#!/usr/bin/env python
import time
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado_utils import routes
from tornado.web import authenticated
@routes(r'/update')
class MainHandler(tornado.web.RequestHandler):
    def get_data(self,callback):
        data = {}
        #notie type : 
        callback(data)
    @tornado.web.asynchronous 
    @authenticated
    def get(self):
        self.get_data(callback=self.wait)
 
    def wait(self, result):
        if result:
            self.write(result)
            self.finish()
        else:#TODO: timeout 30
            tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 3, lambda: self.get_data(callback=self.wait))