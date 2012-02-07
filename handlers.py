# -*- coding: utf-8 -*-
import models
from tornado.web import HTTPError 
from base import BaseHandler
from tornado_utils.routes import route
from tornado.web import authenticated

class Wish():
    pass
    
@route(r'/')
class StartHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect('/home')
        else :
            self.render('start.html')
 
@route(r'/home')
class HomeHandler(BaseHandler):
    def timeline(self,json=False):
        #TODO
        q = self.session.query(models.Wish).order_by(models.Wish.ctime)[:19]
        if json : 
            return self.json_write(code='001', data=q)
        return q
    @authenticated
    def get(self):
        arg = {
               'data' : self.timeline(),
               'current_user' : self.current_user,
               'title' : "愿望管理"
        }
        self.render('home.html',arg=arg)
        return
