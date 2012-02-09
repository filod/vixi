# -*- coding: utf-8 -*-
import models
from validictory import validate
from base import BaseHandler
from tornado_utils.routes import route
from sqlalchemy import or_
import util 


@route(r'/admin/(user|user/list)',name='userlist')
@route(r'/admin/user/(add)',name='useradd')
class UserAdminHandler(BaseHandler):
    def enable(self,uid):
        u=self.session.query(models.User).get(uid)        
        u.stat = 'active' 
        self.session.commit() 
    def disable(self,uid):
        u=self.session.query(models.User).get(uid)
        u.stat = 'inactive' 
        self.session.commit() 
    def powerdown(self,uid):
        u=self.session.query(models.User).get(uid)
        if(u.mtype == 'superadmin'):
            self.alert('不能修改superadmin！')
            return
        u.mtype = 'user' 
        self.session.commit()
    def powerup(self,uid):
        u=self.session.query(models.User).get(uid)
        u.mtype = 'admin'
        self.session.commit()
    
    def user_list(self):
        op = self.get_argument('op', default='None', strip=True)
        pn = int(self.get_argument('pn', default=1, strip=True))
        s = self.get_argument('s', default=None)
        uid = self.get_argument('uid',default=None)
        if hasattr(self, op) and uid:
            getattr(self, op)(uid)
        if s : 
            q = self.session.query(models.User).filter(or_(models.User.email.like('%'+s+'%'),
                                                           models.User.displayname.like('%'+s+'%'),
                                                           models.User.uniquename.like('%'+s+'%')))[(pn-1)*25:pn*25]
        else :
            q = self.session.query(models.User)[(pn-1)*25:pn*25]
        arg = {
               'data' : q,
               'title' : "用户管理",
               'search-placeholder' :'email | displayname | uniquename'
        }
        self.render('admin/user-list.html',arg=arg)

    def add_user(self):
        email = self.get_argument('email') 
        if self.session.query(models.User).filter_by(email=email).count() > 0 :
            self.json_write('5')
            return
        user = models.User()
        user.email = email
        user.pwd = util.makepwd(self.get_argument('password'))
        user.displayname = self.get_argument('displayname')
        user.uniquename = self.get_argument('uniquename')
        user.mtype = self.get_argument('mtype')
        user.ctime = util.now()
        self.session.add(user)
        self.session.commit()
        self.json_write('7')
    
    @util.admin_authenticated
    def get(self, *pattern, **kw):
        if pattern and pattern[0]=='add' :
            arg = { 
                   'title' : "用户管理-添加用户"
            }
            self.render('admin/user-add.html',arg=arg)
        else :
            self.user_list()
    
    @util.admin_authenticated
    def post(self, *pattern, **kw):
        self.add_user()
        

@route(r'(/admin/wish/?)|(/admin/wish/list)')
class WishAdminHandler(BaseHandler):
    def delete(self,wid):
        w=self.session.query(models.Wish).get(wid)
        if w:
            self.session.delete(w)
            self.session.commit()
        return
    @util.admin_authenticated
    def get(self, *pattern, **kw):
        op = self.get_argument('op', default='None', strip=True)
        pn = int(self.get_argument('pn', default=1, strip=True))
        s = self.get_argument('s', default=None)
        wid = self.get_argument('wid',default=None)
        if hasattr(self, op) and wid:
            getattr(self, op)(wid)
        if s : 
            q = self.session.query(models.Wish).filter(models.Wish.uid==s)[(pn-1)*25:pn*25]
        else :
            q = self.session.query(models.Wish)[(pn-1)*25:pn*25]
        arg = {
               'data' : q,
               'title' : "愿望管理",
               'search-placeholder' :'uid '
        }
        self.render('admin/wish-list.html',arg=arg)
@route(r'/admin/note')
class NoteAdminHandler(BaseHandler):    
    @util.admin_authenticated
    def get(self, *pattern, **kw):
        op = self.get_argument('op', default='None', strip=True)
        pn = int(self.get_argument('pn', default=1, strip=True))
        s = self.get_argument('s', default=None)
        wid = self.get_argument('wid',default=None)
        if hasattr(self, op) and wid:
            getattr(self, op)(wid)
        if s : 
            q = self.session.query(models.Wish).filter(models.Wish.uid==s)[(pn-1)*25:pn*25]
        else :
            q = self.session.query(models.Wish)[(pn-1)*25:pn*25]
        arg = {
               'title' : "通知管理"
        }
        self.render('admin/note.html',arg=arg)
        
@route(r'(/admin/comment/?)|(/admin/comment/list)')
class CommentAdminHandler(BaseHandler):
    pass
@route(r'/admin/sys')
class SysAdminHandler(BaseHandler):
    
    pass
@route(r'/admin/?')
class AdminHandler(BaseHandler):
    @util.admin_authenticated
    def get(self, *pattern, **kw):
        arg = {
               'title':'欢迎！'
            }
        self.render('admin/welcome.html',arg=arg)
        return

