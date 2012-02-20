# -*- coding: utf-8 -*-

#import json
from tornado.escape import json_encode
from tornado.web import RequestHandler
from tornado.web import HTTPError
from config import ret_code_map
from models import User
import models
import util
from tornado_utils.routes import route

class BaseHandler(RequestHandler):
    def initialize(self): 
        self.arg = {
                    'current_user' : self.current_user
                    }
        self.tg = models.TagGraph(self.r)
        self.ug = models.UserGraph(self.r)
        self.wg = models.WishGraph(self.r)
        self.noti = models.Notice(self.r)
    @property
    def r(self): #redis db obj
        return self.application.r
    @property
    def session(self):
        return self.application.session
        
    def get_current_user(self):
        auth = self.get_secure_cookie("auth")
        if not auth:
            return None
        query = self.session.query(User).filter_by(email = auth)
        if query.count() == 0:
            return None
        return query.one()
    def is_owner(self,uid):
        return  self.current_user.uid == uid or self.is_admin()
    def is_admin(self):
        cur = self.get_current_user()
        if(cur) :
            return cur.mtype == 'admin' or cur.mtype=='superadmin'
        return False
    def json_write(self,code='0000',data=None,plain=False,jsonp=False):
        '''在采用ajax输出时调用此方法 可以加入logging装饰器TODO 以记录日志 '''
        #some logging        
        if not data:
            ret_code_map[code]['data'] = data
        if plain : 
            self.set_header("Content-Type", "text/plain;charset=UTF-8")
        else:
            self.set_header("Content-Type", "application/json;charset=UTF-8")
        if jsonp : 
            callback = self.get_argument('callback') or 'callback'
            self.write(callback+json_encode(ret_code_map[code]))
        else:
            self.write(json_encode(ret_code_map[code]))
        
    def alert(self,msg):
        self.write('<script>alert("'+str(msg)+'")</script>')
        

    def write_error(self, status_code, **kwargs):
        if status_code >= 500 and not self.application.settings['debug']:
            if self.application.settings['admin_emails']:
                try:
                    self._email_exception(status_code, *kwargs['exc_info'])
                except:
                    pass
            else:
                pass
        if self.application.settings['debug']:
            super(BaseHandler, self).write_error(status_code, **kwargs)
        else:
            options = dict(
              status_code=status_code,
              err_type=kwargs['exc_info'][0],
              err_value=kwargs['exc_info'][1],
              err_traceback=kwargs['exc_info'][2],
            )
            self.render("error.html", **options)

class PageNotFoundHandler(RequestHandler):
    def get(self):
        path = self.request.path
        if not path.endswith('/'):
            new_url = '%s/' % path
            if self.request.query:
                new_url += '?%s' % self.request.query
            self.redirect(new_url)
            return
        raise HTTPError(404, path)
    
 
#整个登录&注册采用 ajax 方式
@route(r'/register')
class RegisterHandler(BaseHandler):
    def add_user(self):
        email = self.get_argument('email')
        pwd = self.get_argument('password')
        
        q = self.session.query(User).filter_by(email=email)
        if q.count() > 0 :
            self.json_write('5')
            return        
        user = User()
        user.email = email
        user.pwd = util.makepwd(pwd)
        user.mtype = 'user'
        user.ctime = util.now()
        self.session.add(user)
        self.session.commit()
        self.set_secure_cookie('auth',email)
        self.json_write('6')
    def post(self):
        self.add_user()
        return

@route(r'/signin')
class SigninHandler(BaseHandler):
    @util.not_authenticated
    def get(self):
        self.render('start.html')
    
    @util.not_authenticated
    def post(self):        
        i_email = self.get_argument("email")
        i_pwd = self.get_argument("password")
        if not i_email or not i_pwd:
            self.json_write('3')
            return
        query = self.session.query(User).filter_by(email = i_email)
        if query.count() == 0:
            self.json_write('2')
            return
        elif query.count() >= 0 :
            if(util.validpwd(i_pwd, query.one().pwd)):
                self.set_secure_cookie('auth',i_email)
                self.json_write('1')
                self.redirect('/home')
                return
            else:
                self.json_write('0')
                return
        else:
            self.json_write('000')
            return

@route(r'/signout')
class SignoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('auth')
        self.redirect('/')