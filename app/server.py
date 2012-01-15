import os
import sys

import tornado.web as t
import tornado.ioloop
import tornado.httpserver

class empty (tornado.web.RequestHandler):
    def get(self):
        self.write('hi,tornado user !')
        return


class authEmpty (tornado.web.RequestHandler):
    @t.authenticated
    def get(self):
        self.write('sorry , U need to be authorized');
        return
    
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', empty), 
            (r'/home', authEmpty),
            (r'/signin', empty),
            (r'/signout', empty),
            (r'/wish', empty),
            (r'/', empty),
            (r'/signout', empty),
            
        ]
        settings = {
            'login_url' : '/signin', 
            'template_path' : os.path.join(os.path.dirname(__file__), 'tpl'), 
            'static_path' : os.path.join(os.path.dirname(__file__), "static"),
            'xsrf_cookies' : True, 
            'cookie_secret' : '3295bfab668c4ad48dad43f890402905',
            'debug' : True
        }
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(80)
    tornado.ioloop.IOLoop.instance().start()