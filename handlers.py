# -*- coding: utf-8 -*-
import models
import util
import tornado
from tornado.web import HTTPError 
from base import BaseHandler
from tornado_utils.routes import route
from validictory import validate
from tornado.escape import *
#decorators
from tornado.web import authenticated
from tornado.web import asynchronous
from tornado_utils.decorators import authenticated_plus
@route(r'/')
class StartHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect('/home')
        else :
            self.render('start.html')
 
@route(r'/home')
class HomeHandler(BaseHandler):
    def initialize(self):
        super(HomeHandler,self).initialize()  
        return
    def timeline(self,json=False):
        #TODO
        wishes = self.session.query(models.Wish).order_by(models.Wish.ctime.desc())[:19] 
        if json : 
            return self.json_write(code='001', data=wishes)
        return wishes
    @authenticated
    def get(self):
        self.arg.update({
               'data' : self.timeline(),
               'title' : "愿望动态"
        })
        self.render('home.html',arg=self.arg)
@route(r'/wish/make/?',name='new_wish')
@route(r'/wish/make/(\d+)',name='edit_wish')
class WishMakeHandler(BaseHandler):
    schema = {
            'type' : 'object',
            'properties':{
                        'title' :  {'type':'string','blank':False },
                        'content' : {'type':'string','blank':True },
                        'is_public' : {'type':'integer','required':False },
                        'is_anonymous' : {'type':'integer','required':False },
                        'is_share' : {'type':'integer','required':False },
                        'poster' : {'type':[{'type':'string','patten':util.REGEX.url},{'type':'null'}],'required':False },
                        'ctime' :{'type':'integer','required':False },
                        'stat' : {'type':[{'type':'string'},{'type':'null'}], 'maxLength':20},
                        'uid' : {'type':'integer'}
                        }
              }
    def remove_wish(self,wish):
        self.session.delete(wish)
    def make_wish(self,wish=None):
        try:
            data = {
                    'title' : xhtml_escape(self.get_argument('title',default='')),
                    'content' : xhtml_escape(self.get_argument('content',default='')),
                    'is_public' : 1 if self.get_argument('is_public',default=None)== 'on' else 0,
                    'is_anonymous' :1 if self.get_argument('is_anonymous',default=None)=='on' else 0,
                    'is_share' : 1 if self.get_argument('is_share',default=None)=='on' else 0,
                    'poster' : self.get_argument('poster',default=None),
                    'ctime' : util.now(),
                    'stat' : self.get_argument('stat',default='active'),
                    'uid' : self.current_user.uid
                    }
            validate(data,self.schema);
            if not wish : wish = models.Wish()
            for item in data : 
                setattr(wish,item,data[item])
            self.session.add(wish)
            
            self.session.commit()
            self.update_tag(wish)
            return wish
        
        except ValueError,e:
            self.write(e.message)#TODO for debug
            self.json_write(code='000')
            
    def update_tag(self,wish):
        '''
                        用redis做tag存储
                        结构|set:
            tag:[tagname] 'wid'
            wish:[wid] 'tagname'
        '''
        if wish:
            tags = json_decode(self.get_argument('tags',default='[]'))
            self.tg.update_tag(wish.wid, set(tags))
    
    @authenticated
    def post(self, *match, **kw):    
        #保存(草稿|添加)
        if match and match[0] :
            wid = int(match[0])
        else:
            wid = int(self.get_argument('wid')) if self.get_argument('wid').isdigit() else None
        if wid :
            wish = self.session.query(models.Wish).get(wid)
            if not wish : 
                self.json_write('101')
                return
            else:
                self.json_write(code='100',data=self.make_wish(wish))
        else: 
            self.json_write(code='100',data=self.make_wish())
    @authenticated
    def get(self, *match, **kw):
        if match and match[0]:#编辑愿望
            wish = self.session.query(models.Wish).get(int(match[0]))
            if not wish : raise HTTPError(404)
        else:#新建愿望
            wish = models.Wish()
        if(not self.is_owner(wish.uid)):
            self.redirect('/')
            return
        self.arg.update({
            'tags' : str(list(self.tg.get_tags(wish.wid))),
            'wish' : wish,
            'title' : '许愿'
              })
        self.render('wish-make.html',arg=self.arg)
        
@route(r'/wish/(\d+)')
class WishDetailHandler(BaseHandler):
    @authenticated
    def get(self,*match,**kw):
        wish = self.session.query(models.Wish).get(int(match[0]))
        if not wish: raise HTTPError(404) 
        user = self.session.query(models.User).get(wish.uid)
        setattr(wish,'username',user.displayname or user.uniquename)
        setattr(wish,'avatar',user.avatar)
        self.arg.update({
                'title' : '%s - 愿望详情'%wish.title,
                'wish':wish 
        })
        self.render('wish-detail.html',arg=self.arg)
       
@route(r'/follow')
class FollowHandler(BaseHandler):
    schema = {
              'type' :  'object',
              'properties' : {
                              'target' : {'type':'string','blank':False },
                              'toid' :{'type':'integer','required':True },
                              'fuid' : {'type':'integer','required':True },
                              'op' : {'type':'string','blank':False},
                              }
              }
    @authenticated
    def post(self,*match,**kw):
        try:
            data = {
                    'target' : self.get_argument('target'),
                    'toid' : int(self.get_argument('toid')),
                    'fuid' : self.current_user.uid,
                    'op' : self.get_argument('op')
                    }
            validate(data,self.schema)       
            getattr({'wish' : self.wg,'people':self.ug}[data['target']],data['op'])(data['fuid'],data['toid'])
            #关注时，对被关注人发送一条notice
            if(self.current_user.uid != data['toid']):
                self.noti.add_notice(data['toid'],{
                                                            'type' : 'user_follow',
                                                            'fuid':self.current_user.uid
                                                   })
            self.json_write(code='002')
        except ValueError,e:
            self.json_write(code='000')
            
@route(r'/people/(\d+)')
class PeopleHandler(BaseHandler):
    @authenticated
    def get(self,*match,**kw):
        user = self.session.query(models.User).get(int(match[0]))
        wishes = self.session.query(models.Wish).filter_by(uid=user.uid)
        self.arg.update({
                         'user' : user,
                         'data' : wishes,
                        'title' : '%s - 个人主页'%(user.displayname or user.email)
                         })
        self.render('people.html',arg=self.arg)

@route(r'/notice')
class NoticeHandler(BaseHandler):
    def parse_notis(self,notis):
        notilist = []
        def noti_comment(item,noti):
            wish = self.session.query(models.Wish).get(int(item['toid']))
            noti['op'] = '评论了你的愿望'
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s">%s</a>'%(wish.wid,item['uuid'],wish.title)
            return noti
        def noti_reply(item,noti):
            return noti
        def noti_user_follow(item):
            noti['op'] = '关注了你'
            return item
        def noti_wish_follow(item):
            return item
        def noti_bless(item):
            return item
        def noti_curse(item):
            return item
        def noti_atme(item):
            return item
        def noti_sys(item):
            return item
        for item in notis:
            item = json_decode(item) 
            noti = {}
            if int(item['fuid']) != 0 :
                user = self.session.query(models.User).get(int(item['fuid']))
                noti['who'] = '<a href="/people/%s">%s</a>'%(item['fuid'],user.displayname or user.uniquename)
            else:
                noti['who'] = '<span class="sys-noti">系统消息：<span>'
            {
             'comment' : noti_comment,
             'user_follow' : noti_user_follow
            }[item['type']](item,noti)
            notilist.append(noti)
        return notilist
    @authenticated
    def post(self):
        self.json_write()
    @authenticated
    def get(self):
        allnoti = self.parse_notis(self.noti.get_all(self.current_user.uid))
        unread = self.parse_notis(self.noti.get_unread(self.current_user.uid))
        self.arg.update({
                         'unread':unread,
                         'allnoti':allnoti
                         })
        self.render('notice.html',arg=self.arg)

@route(r'/comment/box',name='comment-box')
@route(r'/comment/add',name='add_comment')
@route(r'/comment/list',name='comment-list')
class CommentHandler(BaseHandler):
    schema = {
            'type' : 'object',
            'properties':{
                        'content' : {'type':'string','blank':False },
                        'ctime' :{'type':'integer','required':False },
                        'stat' : {'type':[{'type':'string'},{'type':'null'}], 'maxLength':20},
                        'uid' : {'type':'integer'},
                        'wid' : {'type':'integer'}
                        }
              }
    @authenticated
    def post(self,*match,**kw):
        
        if(self.request.path == '/comment/add'):
#            import time
#            time.sleep(1)
            try:
                data = {
                        'wid' : int(self.get_argument('wid',default='')),
                        'content' : xhtml_escape(self.get_argument('content',default='')),
                        'ctime' : util.now(),
                        'stat' : self.get_argument('stat',default='active'),
                        'uid' : self.current_user.uid
                        }
                validate(data,self.schema)
                wish = self.session.query(models.Wish).get(data['wid'])
                if not wish:
                    self.json_write(code='000')
                    return
                comment = models.Comment()
                for item in data : 
                    setattr(comment,item,data[item])
                self.session.add(comment)
                self.session.commit()
                #添加评论时，对wish主人发送一条notice
                if(wish.uid != self.current_user.uid) : 
                    self.noti.add_notice(wish.uid, {
                                                    'type':'comment',
                                                    'fuid':self.current_user.uid,
                                                    'fid':comment.cid,
                                                    'toid':wish.wid
                                                    })
                self.json_write(code='103')
            except ValueError,e:
                self.json_write(code='000')
        else:
            self.json_write('004')
    @authenticated
    def get(self,*match,**kw):
        if(self.request.path == '/comment/list'):
            wid = self.get_argument('wid')
            comments = self.session.query(models.Comment).filter_by(wid=wid)
            if not comments.count():
                self.write('还没有评论哦！')
                return;
            self.arg.update({
                             'comments' : comments
                             })
            self.render('modules/comment-list.html',arg=self.arg)
        elif(self.request.path == '/comment/box'):
            self.render('modules/comment-box.html')
            
            
            
            
            
            
@route(r'/test')
class TestHandler(BaseHandler):
    @asynchronous
    def get(self):
        self.write('do over!')
        
        
