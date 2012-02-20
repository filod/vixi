# -*- coding: utf-8 -*-
import tornado.web as t
import tornado.ioloop
import tornado.httpserver

from db import ConnectDB
from db import ConnectRDB
from config import app_config
from tornado_utils.routes import route
#handler module
import base
import handlers
import admin
    
class Application(tornado.web.Application):
    def __init__(self):
#        handlers = [
#            ################用户页面#############
#            (r'/people/([^/]+)', empty), 
#            ################愿望相关##############
#            (r'/wish/pool', empty),
#            (r'/wish/([^/]+)', empty),
#            (r'/wish/([^/]+)/add', empty),
#            (r'/wish/([^/]+)/edit', empty),
#            (r'/wish/([^/]+)/delete', empty),
#            (r'/wish/([^/]+)/reply', empty), 
#            ###############设置系统###############
#            (r'/settings/profile',empty),
#            (r'/settings/email',empty),
#            (r'/settings/profile',empty),
#            (r'/settings/acount',empty), 
#            ################通知系统##############
#            (r'/notifications',empty),
#            (r'/notifications/all',empty)
#        ]
        routed_handlers = route.get_routes()
        routed_handlers.append(                               
              tornado.web.url(r"/static/(.*)", t.StaticFileHandler,
                            app_config['static_path'])
        )
        routed_handlers.append(
              tornado.web.url('/.*?', base.PageNotFoundHandler,
                            name='page_not_found')
        )
        settings = app_config
        tornado.web.Application.__init__(self, routed_handlers, **settings)
        self.session = ConnectDB()
        self.r = ConnectRDB()

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(80)
    tornado.ioloop.IOLoop.instance().start()