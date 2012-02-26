# -*- coding: utf-8 -*-
import models
import util
import tornado
from tornado.web import HTTPError 
from base import BaseHandler
from tornado_utils.routes import route
from validictory import validate
from tornado.escape import *
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from sqlalchemy import func
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
                    'op' : self.get_argument('op'),
                    }
            wish = self.session.query(models.Wish).get(data['toid'])
            if not wish :
                raise ValueError()
            validate(data,self.schema)       
            getattr({'wish' : self.wg,'people':self.ug}[data['target']],data['op'])(data['fuid'],data['toid'])
            
            #关注时，对被关注人发送一条notice
            if(self.current_user.uid != data['toid'] and data['op'] =='follow'):
                self.noti.add_notice(wish.uid,{
                                                            'type' : data['target']+'_follow',
                                                            'fuid' : self.current_user.uid,
                                                            'toid' : wish.wid
                                                   })
            self.json_write(code='002')
        except ValueError,e:
            self.json_write(code='000')        
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
            self.update_friends(wish)
            return wish
        
        except ValueError,e:
            self.write(e.message)#TODO for debug
            self.json_write(code='000')
    def update_friends(self,wish):
        ''' '''
        if wish :
            friends = self.ug.get_friends(self.current_user.uid)
            users = json_decode(self.get_argument('friends',default='[]'))
            uids = []
            for user in users :
                if(str(user[0]) in friends) :
                    uids.append(user[0])
                    #对提到的人都发送一条通知
                    self.noti.add_notice(user[0],{
                                                                'type' : 'atme',
                                                                'fuid':self.current_user.uid,
                                                                'fid' : wish.wid
                                                       })
            self.wag.update_ones(wish.wid, set(uids))
            
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
                self.make_wish(wish)
                self.json_write(code='100')
        else: 
            self.json_write(code='100')
    @authenticated
    def get(self, *match, **kw):
        if match and match[0]:#编辑愿望
            wish = self.session.query(models.Wish).get(int(match[0]))
            if not wish : raise HTTPError(404)
        else:#新建愿望
            wish = models.Wish()
        if(wish.uid and not self.is_owner(wish.uid)):
            self.redirect('/')
            return 
        uids = self.ug.get_friends(self.current_user.uid)
        users = [self.session.query(models.User.uid, models.User.displayname, models.User.avatar ).filter_by(uid=uid).first() for uid in uids]
        atuids = self.wag.get_ones(wish.wid) 
        atusers =  [self.session.query(models.User.uid, models.User.displayname, models.User.avatar ).filter_by(uid=atuid).first() for atuid in atuids]
        self.arg.update({
            'tags' : str(list(self.tg.get_tags(wish.wid))),
            'atfriends' : json_encode(atusers),
            'wish' : wish,
            'title' : '许愿',
            'friends' : json_encode(users)
              })
        self.render('wish-make.html',arg=self.arg)

@route(r'/wish/(\d+)')
class WishDetailHandler(BaseHandler):
    @authenticated
    def get(self,*match,**kw):
        self.noti.mark(self.current_user.uid,self.get_argument('noti_uuid',default='0')) 
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
@route(r'/vote')
class WishVoteHandler(FollowHandler):        
    @authenticated
    def post(self,*m,**kw):
        try:
            data = {
                    'target' : 'wish', #默认为wish
                    'toid' : int(self.get_argument('toid')),
                    'fuid' : self.current_user.uid,
                    'op' : self.get_argument('op')
                    }
            wish = self.session.query(models.Wish).get(data['toid'])
            validate(data,self.schema)
            getattr(self.wg, data['op'])(data['fuid'],data['toid'])
            #仅在祝福时发送一条notice
            if(self.current_user.uid != data['toid'] and data['op'] =='bless'):
                self.noti.add_notice(wish.uid,{
                                                'type' : data['op'],
                                                'fuid':self.current_user.uid,
                                                'toid':wish.wid
                                               })
            self.json_write(code='002',data=getattr(self.wg,'get_'+data['op'].replace('un','')+'_count')(wish.wid))
        except ValueError,e:
            self.json_write(code='000')
@route(r'/wish/list')
class WishListHandler(BaseHandler):
    @authenticated
    def get(self,*m,**kw):
        atme_ids = self.wag.get_wishes(self.current_user.uid)
        atme = [ self.session.query(models.Wish).get(wid) for wid in atme_ids]
        iwish = self.session.query(models.Wish).filter_by(uid=self.current_user.uid).order_by(models.Wish.ctime.desc())[:19]
        ifollow_ids = tuple( int(i) for i in self.wg.get_follows(self.current_user.uid)) 
        ifollow = [ self.session.query(models.Wish).get(fid) for fid in ifollow_ids ] 
        self.arg.update({
                         'atme':atme,
                         'iwish' : iwish,
                         'ifollow':ifollow
                         })
        self.render('wish-list.html',arg=self.arg)
@route(r'/wishpool/')
class WishPoolHandler(BaseHandler):
    @authenticated
    def get(self):
        self.render('wish-pool.html',arg=self.arg)

@route(r'/friends')
class FriendsHandler(BaseHandler): 
    @authenticated
    def get(self):
        uids = self.ug.get_friends(self.current_user.uid)
        users = [[uid,self.session.query(models.User.displayname).filter_by(uid=uid).first()] for uid in uids]
        self.json_write('005',data=users)
        
@route(r'/people/(\d+)')
class PeopleHandler(BaseHandler):
    @authenticated
    def get(self,*match,**kw):
        user = self.session.query(models.User).get(int(match[0]))
        wishes = self.session.query(models.Wish).filter_by(uid=user.uid,is_public=1)
        self.arg.update({
                         'user' : user,
                         'public' : wishes,
                        'title' : '%s - 个人主页'%(user.displayname or user.email)
                         })
        self.render('people.html',arg=self.arg)

@route(r'/notice',name='notice-page')
@route(r'/notice/clear',name='clear-notice')
@route(r'/notice/mark',name='mark-notice')
class NoticeHandler(BaseHandler):
    def parse_notis(self,notis):
        notilist = []
        if not notis : 
            return notilist
        def noti_comment(item,noti):
            wish = self.session.query(models.Wish).get(int(item['toid']))
            noti['op'] = '评论了你的愿望'
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s">%s</a>'%(wish.wid,item['uuid'],wish.title)
            return noti
        def noti_reply(item,noti):
            comment = self.session.query(models.Comment).get(int(item['toid']))
            noti['op'] = '回复了你的评论'
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s#cid=%s">%s</a>'%(comment.wid,item['uuid'],comment.cid,comment.content)
            return noti
        def noti_people_follow(item,noti):
            noti['op'] = '关注了你'
            noti['target'] = ''
            return noti
        def noti_wish_follow(item,noti):
            wish = self.session.query(models.Wish).get(int(item['toid']))
            noti['op'] = '关注了你的愿望'
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s">%s</a>'%(wish.wid,item['uuid'],wish.title)
            return noti
        def noti_bless(item,noti):
            wish = self.session.query(models.Wish).get(int(item['toid']))
            noti['op'] = '在愿望'
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s">%s</a> 中祝福了你！'%(wish.wid,item['uuid'],wish.title)
            return noti
        def noti_curse(item,noti):
            #TODO： no notice
            return noti
        def noti_atme(item,noti):
            wish = self.session.query(models.Wish).get(int(item['fid']))
            noti['op'] = '在愿望 '
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s">%s</a> 中提到了你'%(wish.wid,item['uuid'],wish.title)
            return noti 
        def noti_msg(item,noti):
            noti['op'] = '给你发送了私信 '
            noti['target'] = '<a href="/inbox"> 点击查看 </a> '
            return noti
        def noti_sys(item,noti):
            noti['op'] = ''
            noti['target'] = ''
            return noti
        for item in notis:
            item = json_decode(item)
            noti = {}
            if int(item['fuid']) != 0 :
                user = self.session.query(models.User).get(int(item['fuid']))
                noti['who'] = '<a href="/people/%s">%s</a>'%(item['fuid'],user.displayname or user.uniquename)
            else:
                noti['who'] = '<span class="sys-noti">系统消息：<span>%s'%item['content']
                
            noti['ctime'] = item['addtime']
            noti['uuid'] = item['uuid']
            {
             'comment' : noti_comment,
             'reply' : noti_reply,
             'people_follow' : noti_people_follow,
             'wish_follow' : noti_wish_follow,
             'bless' : noti_bless,
             'curse' : noti_curse,
             'atme' : noti_atme,
             'msg' : noti_msg,
             'sys' : noti_sys
            }[item['type']](item,noti)
            notilist.append(noti)
        return notilist
    @authenticated
    def post(self,*m, **kw):
        try:
            if self.request.path == '/notice/clear' :
                self.noti.mark_all(self.current_user.uid)
                self.json_write('202')
            elif self.request.path == '/notice/mark': 
                uuid = self.get_argument('noti_uuid')
                self.noti.mark(self.current_user.uid, uuid)
                self.json_write('203',data=[uuid])
        except ValueError:
            self.json_write('000')
    @authenticated
    def get(self,*m, **kw):
        allnoti = self.parse_notis(self.noti.get_all(self.current_user.uid))
        [unread_data,count] = self.noti.get_unread(self.current_user.uid)
        unread = self.parse_notis(unread_data)
        self.arg.update({
                         'count' :count,
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
                        'wid' : {'type':'integer'},
                        'reply_uid' : {'type':[{'type':'integer'},{'type':'null'}]},
                        'reply_cid' : {'type':[{'type':'integer'},{'type':'null'}]}
                        }
              }
    @authenticated
    def post(self,*match,**kw):
        
        if(self.request.path == '/comment/add'):
            try:
                reply_uid = int(self.get_argument('reply_uid',default=0))
                reply_cid = int(self.get_argument('reply_cid',default=0))
                if(reply_uid == 0 or reply_cid ==0) :
                    reply_uid = None
                    reply_cid = None
                data = {
                        'wid' : int(self.get_argument('wid',default='')),
                        'reply_uid' : reply_uid,
                        'reply_cid' : reply_cid,
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
                #如果有reply_uid,且reply_uid不等于wish.uid,发送一条notice
                if(reply_uid != 0  and reply_uid != wish.uid) :
                    self.noti.add_notice(reply_uid,  {
                                                'type' : 'reply',
                                                'fuid' : self.current_user.uid,
                                                'fid' : comment.cid,
                                                'toid' : reply_cid
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

@route(r'/inbox',name='inbox-index')
@route(r'/inbox/(\d+)',name='conversation')
class MessageHandler(BaseHandler):
    schema = {
            'type' : 'object',
            'properties':{
                        'content' : {'type':'string','blank':True },
                        'from_uid' : {'type':'integer','required':False },
                        'to_uid' : {'type':'integer','required':False },
                        'ctime' :{'type':'integer','required':False },
                        }
              }
    def get_conversation_id(self,l):
        import sys
        if(sys.maxint == 2**31-1): LEFTBITS = 32
        elif(sys.maxint == 2**63-1) : LEFTBITS = 64
        l.sort()
        c = (long(l[0]) << LEFTBITS) + l[1]
        return c
    @authenticated
    def post(self,*m,**kw):
        try:
            #发送私信
            data = {
                        'content' : xhtml_escape(self.get_argument('content')),
                        'from_uid' : self.current_user.uid,
                        'to_uid' : int(self.get_argument('to_uid')),
                        'ctime' : util.now(),
                        'conversation' : self.get_conversation_id([self.current_user.uid,int(self.get_argument('to_uid'))])
                    }
            validate(data,self.schema)
            msg = models.Message()
            for item in data : 
                setattr(msg,item,data[item])
            self.session.add(msg)
            self.session.commit()
            #向收信人发送一条notice
            self.noti.add_notice(data['to_uid'],{
                                                 'type' : 'msg',
                                                 'fuid' : self.current_user.uid,
                                                 'fid' : msg.id
                                                 })
            self.json_write(code='300')
        except ValueError:
            self.json_write(code='000')
                
    @authenticated
    def get(self,*m,**kw):
        if m and m[0] :#进入与某人的会话
            conversation =self.session.query(models.Message).filter_by(conversation=long(m[0])).order_by(models.Message.ctime.desc())[0:19]#TODO
            self.arg.update({
                             'conversation' : conversation
                             })
            self.render('conversation.html',arg=self.arg)
            return
        else: #全部会话
            stmt = self.session.query(models.Message)\
            .filter( or_(models.Message.to_uid==self.current_user.uid, models.Message.from_uid==self.current_user.uid))\
            .order_by(models.Message.ctime.desc()).subquery()
            alias=aliased(models.Message,stmt)
            conversation_list = self.session.query(alias,func.count(alias)).group_by(alias.conversation).all()
            self.arg.update({
                             'conversation-list' : conversation_list
                             })
            self.render('conversation-list.html',arg=self.arg)

@route(r'/settings')
class SettingsHandler(BaseHandler):
    @authenticated
    def get(self):
        self.arg.update({
                         })
        self.render('settings.html',arg=self.arg)
#just lab!
@route(r'/lab')
class LabHandler(BaseHandler):
    def get(self):
        most_bless_ids = self.wg.get_most_bless()
        most_curse_ids = self.wg.get_most_curse()
        most_bless = [self.session.query(models.Wish).get(bwid) for bwid in most_bless_ids]
        most_curse = [self.session.query(models.Wish).get(bwid) for bwid in most_curse_ids]
        self.arg.update({
                         'most-bless' : most_bless,
                         'most-curse' : most_curse,
                         })
        self.render('lab-rank.html',arg=self.arg)
@route(r'/test')
class TestHandler(BaseHandler):
    @asynchronous
    def get(self):
        self.write('do over!')
        
        
