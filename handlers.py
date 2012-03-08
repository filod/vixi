# -*- coding: utf-8 -*-
import models
import util
import tornado
from tornado.web import HTTPError , RequestHandler
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
class FeedHandler(BaseHandler):
    def parse_feeds(self,feeds): 
        feeds_list = []
        if not feeds : 
            return feeds_list
        def feed_new_w(item,feed): 
            feed['action'] = feed['actor']+'<span class="label">添加</span>了该愿望'
            feed['content'] = feed['wish'].content
            return
        def feed_follow_w(item,feed):
            feed['action'] = feed['actor']+'<span class="label label-info">关注</span>了该愿望'
            feed['content'] = feed['wish'].content
            return
        def feed_bless_w(item,feed):
            feed['action'] = feed['actor']+'<span class="label label-success">祝福</span>了该愿望'
            feed['content'] = feed['wish'].content
            return
        def feed_update_w(item,feed):
            feed['action'] = feed['actor']+'<span class="label label-info">更新</span>了该愿望'
            feed['content'] = feed['wish'].content
            return
        def feed_comment_w(item,feed):
            feed['action'] = feed['actor']+'<span class="label label-info">评论</span>了该愿望'
            comment = self.session.query(models.Comment).get(int(item['actionid']))
            feed['content'] = comment.content
            return 
        for item in feeds:
            feed = {}
            feed['ctime'] = str(long(item[1]))
            item = json_decode(item[0])
            feed['wish'] = self.session.query(models.Wish).get(int(item['targetid']))
            user = self.session.query(models.User).get(int(item['actorid']))
            feed['actor'] = '<a href="/people/%s">%s</a>'%(item['actorid'],user.displayname or user.uniquename)
            {'new_w':feed_new_w,
             'follow_w' : feed_follow_w,
             'bless_w' : feed_bless_w,
             'update_w' :feed_update_w,
             'comment_w' : feed_comment_w
             }[item['type']](item,feed)
            feeds_list.append(feed)
        return feeds_list
    
@route(r'/home')
class HomeHandler(FeedHandler):
    def timeline(self,json=False):
        #TODO:
        feeds_data= self.parse_feeds(self.feed.get_feeds(self.current_user.uid))
        return feeds_data
    @authenticated
    def post(self):
        before = self.get_argument('before',default=util.now())
        feeds= self.parse_feeds(self.feed.get_feeds(self.current_user.uid, before=long(before)))
        self.json_write('001', data={'html' : self.render_string('modules/more-feeds.html',feeds=feeds),'count' : len(feeds)})
    @authenticated
    def get(self):
        self.arg.update({
               'feeds' : self.timeline(),
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
            validate(data,self.schema)
            wish = None
            if data['target'] == 'wish':
                wish = self.session.query(models.Wish).get(data['toid'])
                if not wish and wish.is_anonymous:
                    raise ValueError()
            getattr({'wish' : self.wg,'people':self.ug}[data['target']],data['op'])(data['fuid'],data['toid'])
            
            #关注时，对被关注人发送一条notice
            if(self.current_user.uid != data['toid'] and data['op'] =='follow'):
                to = wish.uid if wish else data['toid']
                self.noti.add_notice(to,{
                                                            'type' : data['target']+'_follow',
                                                            'fuid' : self.current_user.uid,
                                                            'toid' : wish.wid if wish else None
                                                   })
            #仅当followe某愿望时更新feed evt
            if data['target'] == 'wish' :
                self.feed.add_to_feed_evt(uid=self.current_user.uid, content={
                                                                              'type' : 'follow_w',
                                                                              'actorid' : self.current_user.uid,
                                                                              'targetid' : wish.wid
                                                                              })
            #同时重建自己的feed列表
            self.feed.build_feed(self.current_user.uid)
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
                        'has_cometrue' : {'type':'integer','required':False },
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
                    'has_cometrue' :0,
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
            is_active = data['stat'] == 'active'
            self.update_tag(wish,is_active)
            self.update_friends(wish,is_active)
            return wish
        
        except ValueError,e:
            self.write(e.message)#TODO for debug
            self.json_write(code='000')
    def update_friends(self,wish,is_active):
        ''' '''
        if wish :
            friends = self.ug.get_friends(self.current_user.uid)
            users = json_decode(self.get_argument('friends',default='[]'))
            uids = []
            for user in users :
                if(str(user[0]) in friends) :
                    uids.append(user[0]) 
                    if(is_active): #仅当愿望正式提交时，才通知friends
                    #TODO:更新愿望后，同一批人又将会得到通知！！
                        self.noti.add_notice(user[0],{
                                                                    'type' : 'atme',
                                                                    'fuid':self.current_user.uid,
                                                                    'fid' : wish.wid
                                                       })
            self.wag.update_ones(wish.wid, set(uids))
            
    def update_tag(self,wish,is_active):
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
            wish = self.session.query(models.Wish).get(wid) #
            if not wish : 
                self.json_write('101')
                return
            else:
                wish = self.make_wish(wish)
                #修改愿望时，更新愿望的feed evt
                if wish.stat =='active' and wish.is_public and not wish.is_anonymous : 
                    self.feed.add_to_feed_evt(wid=wish.wid,is_wish_evt=True, content={
                                                                                      'type' : 'update_w',
                                                                                      'actorid' : wish.uid,
                                                                                      'targetid' : wish.wid
                                                                                    })
                self.json_write(code='100')
            
        else: #添加愿望并更新该用户feed
            wish = self.make_wish()
            if wish.stat == 'active' and wish.is_public  and not wish.is_anonymous:
                self.feed.add_to_feed_evt(uid=self.current_user.uid,content={
                                                                         'type':'new_w',
                                                                         'actorid' : self.current_user.uid,
                                                                         'targetid' : wish.wid
                                                                     })
            self.json_write(code='100')
    @authenticated
    def get(self, *match, **kw):
        if match and match[0]:#编辑愿望
            wish = self.session.query(models.Wish).get(int(match[0]))
            if not wish : raise HTTPError(404)
            if(wish.uid and not self.is_owner(wish.uid)):
                self.redirect('/')
                return 
            atuids = self.wag.get_ones(wish.wid) 
            atusers =  [self.session.query(models.User.uid, models.User.displayname, models.User.avatar ).filter_by(uid=atuid).first() for atuid in atuids]
            self.arg.update({
                'tags' : str(list(self.tg.get_tags(wish.wid))),
                'atfriends' : json_encode(atusers),
            })
        else:#新建愿望
            wish = models.Wish()
            wish.is_anonymous = 0
            wish.is_public =1
            self.arg.update({
                'tags' : json_encode([]),
                'atfriends' : json_encode([]),
            })
            
        #无论是新建还是编辑都需要加载的信息：↓
        uids = self.ug.get_friends(self.current_user.uid)
        users = [self.session.query(models.User.uid, models.User.displayname, models.User.avatar ).filter_by(uid=uid).first() for uid in uids]
        self.arg.update({
            'wish' : wish,
            'title' : '许愿',
            'friends' : json_encode(users)
              })
        self.render('wish-make.html',arg=self.arg)

@route(r'/wish/(\d+)' , name='wish-detail')
@route(r'/wish/(\d+)/realize',name='wish-realize')
class WishDetailHandler(BaseHandler):
    @authenticated
    def post(self,*m,**kw):
        if self.request.path.endswith('realize') :
            wish = self.session.query(models.Wish).get(int(m[0]))
            if  self.is_owner(wish.uid):
                wish.has_cometrue = 1
                wish.mdata = self.get_argument('mdata',default='')
                self.session.add(wish)
                self.session.commit()
                self.json_write('002')
            else:
                self.json_write('003')
        
    @authenticated
    def get(self,*match,**kw):
        self.noti.mark(self.current_user.uid,self.get_argument('noti_uuid',default='0')) 
        wish = self.session.query(models.Wish).get(int(match[0]))
        if not wish: raise HTTPError(404) 
        user = self.session.query(models.User).get(wish.uid)
        if not wish.is_public:
            if not self.is_owner(wish.uid) or not self.wag.is_at(wish.wid,self.current_user.uid):
                self.redirect('/')
                return
        setattr(wish,'username',user.displayname or user.uniquename)
        setattr(wish,'avatar',user.avatar)
        self.arg.update({
                'title' : '%s - 愿望详情'%wish.title,
                'wish':wish ,
                'user': wish.user
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
            #仅在祝福时发送一条notice 并更新feed evt
            if(data['op'] =='bless' and self.current_user.uid != wish.uid ):
                self.noti.add_notice(wish.uid,{
                                                'type' : data['op'],
                                                'fuid':self.current_user.uid,
                                                'toid':wish.wid
                                               })
                self.feed.add_to_feed_evt(uid=self.current_user.uid, content={
                                                                               'type' : 'bless_w',
                                                                               'actorid' : self.current_user.uid,
                                                                               'targetid' : wish.wid
                                                                               })
            self.json_write(code='002',data=getattr(self.wg,'get_'+data['op'].replace('un','')+'_count')(wish.wid))
        except ValueError,e:
            self.json_write(code='000')
@route(r'/wish/list',name='wish-list')
@route(r'/wish/list/more/atme',name='more-atme')
@route(r'/wish/list/more/ifollow',name='more-ifollow')
@route(r'/wish/list/more/iwish',name='more-iwish')
class WishListHandler(BaseHandler):
    def get_atme(self,page=1):
        atme_ids = self.wag.get_wishes(self.current_user.uid,page=page)
        atme = [ self.session.query(models.Wish).get(wid) for wid in atme_ids]
        return atme
    def get_ifollow(self,page=1):
        ifollow_ids = tuple( int(i) for i in self.wg.get_follows(self.current_user.uid,page=page)) 
        ifollow = [ self.session.query(models.Wish).get(fid) for fid in ifollow_ids ] 
        return ifollow
    def get_iwish(self,page=1):
        iwish = self.session.query(models.Wish).filter_by(uid=self.current_user.uid).order_by(models.Wish.ctime.desc())[(page-1)*20:page*20]
        return iwish
    @authenticated
    def post(self,*m,**kw):
        page = int(self.get_argument('nextpage', default=1))
        wishes = []
        if self.request.path =='/wish/list/more/atme':
            wishes = self.get_atme(page)
        elif self.request.path =='/wish/list/more/iwish':
            wishes = self.get_iwish(page)
        elif self.request.path =='/wish/list/more/ifollow':
            wishes = self.get_ifollow(page)
        self.json_write('007', data={'html':self.render_string('modules/more-wish.html',wishes=wishes),'count':len(wishes),'nextpage':page+1})
    @authenticated
    def get(self,*m,**kw):
        self.arg.update({
                         'atme':self.get_atme(),
                         'iwish' : self.get_iwish(),
                         'ifollow':self.get_ifollow()
                         })
        self.render('wish-list.html',arg=self.arg)
@route(r'/wishpool/')
class WishPoolHandler(BaseHandler):
    @authenticated
    def get(self):
        #TODO: 
        wishes = self.session.query(models.Wish).filter_by(is_public=1).order_by(func.rand())[0:19]
        self.arg.update({
                         'wishes' : wishes
                         })
        self.render('wish-pool.html',arg=self.arg)

@route(r'/friends')
class FriendsHandler(BaseHandler): 
    @authenticated
    def get(self):
        uids = self.ug.get_friends(self.current_user.uid)
        users = [[uid,self.session.query(models.User.displayname).filter_by(uid=uid).first()] for uid in uids]
        self.json_write('005',data=users)
        
@route(r'/people/anonymous',name='people-redirect')
@route(r'/people/(\d+)',name='people-index')
@route(r'/people/(\d+)/more/feed',name='more-feed')
@route(r'/people/(\d+)/more/public',name='more-public')
@route(r'/people/(\d+)/follow',name='people-follow')
@route(r'/people/(\d+)/follower',name='people-follower')
class PeopleHandler(FeedHandler):
    @authenticated
    def post(self,*m,**kw):
        if m and m[0]:
            if self.request.path.endswith('/more/feed'):
                before = self.get_argument('before',default=None)
                feeds= self.parse_feeds(self.feed.get_feeds_evt(int(m[0]), before=long(before)))
                self.json_write('001', data={'html':self.render_string('modules/more-feeds.html',feeds=feeds),'count':len(feeds)})
            elif self.request.path.endswith('/more/public'):
                page = int(self.get_argument('nextpage', default=1))
                wishes = self.session.query(models.Wish).filter_by(uid=int(m[0]),is_public=1)[(page-1)*20:page*20]
                self.json_write('007',data={'html':self.render_string('modules/more-wish.html',wishes=wishes),'count':len(wishes)})
        
    @authenticated
    def get(self,*m,**kw):
        if self.request.path.endswith('anonymous'):
            self.redirect('/')
            return
        user = self.session.query(models.User).get(int(m[0]))
        self.arg.update({
                             'follows' : self.ug.get_follows_count(user.uid),
                             'followers' : self.ug.get_followers_count(user.uid)
                             })
        if self.request.path.endswith('follow') or self.request.path.endswith('follower'):
            page = int(self.get_argument('nextpage', default=1))
            if self.request.path.endswith('follow'):
                people_ids = self.ug.get_follows(int(m[0]), page)
            else : 
                people_ids = self.ug.get_followers(int(m[0]), page)
            people = [self.session.query(models.User).get(uid) for uid in people_ids]
            self.arg.update({'user':user,'people':people})
            self.render('relation-list.html',arg=self.arg)
        else:
            wishes = self.session.query(models.Wish).filter_by(uid=user.uid,is_public=1)
            self.arg.update({
                             'feeds' : self.parse_feeds(self.feed.get_feeds_evt(user.uid)),
                             'user' : user,
                             'public' : wishes,
                             'title' : '%s - 个人主页'%(user.displayname or user.email)
                             })
            self.render('people.html',arg=self.arg)
        

@route(r'/notice',name='notice-page')
@route(r'/notice/clear',name='clear-notice')
@route(r'/notice/mark',name='mark-notice')
@route(r'/notice/more/unread',name='more-unread')
@route(r'/notice/more/all',name='more-all')
class NoticeHandler(BaseHandler):
    def parse_notis(self,notis):
        notilist = []
        if not notis : 
            return notilist
        def noti_comment(item,noti):
            wish = self.session.query(models.Wish).get(int(item['toid']))
            noti['op'] = '<span class="label label-info">评论</span>了你的愿望'
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s">%s</a>'%(wish.wid,item['uuid'],wish.title)
            return noti
        def noti_reply(item,noti):
            comment = self.session.query(models.Comment).get(int(item['toid']))
            noti['op'] = '<span class="label label-info">回复</span>了你的评论'
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s#cid=%s">%s</a>'%(comment.wid,item['uuid'],comment.cid,comment.content)
            return noti
        def noti_people_follow(item,noti):
            noti['op'] = '关注了你'
            noti['target'] = ''
            return noti
        def noti_wish_follow(item,noti):
            wish = self.session.query(models.Wish).get(int(item['toid']))
            noti['op'] = '<span class="label label-info">关注</span>了你的愿望'
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
            noti['target'] = '<a href="/wish/%s?noti_uuid=%s">%s</a> 中<span class="label label-info">提及</span>了你'%(wish.wid,item['uuid'],wish.title)
            return noti 
        def noti_msg(item,noti):
            noti['op'] = '给你发送了<span class="label  label-warning">私信</span> '
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
                noti['who'] = '<span class="label">系统消息：<span>%s'%item['content']
                
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
            elif self.request.path == '/notice/more/unread':
                page = int(self.get_argument('nextpage', default=1))
                [unread_data ,count]= self.noti.get_unread(self.current_user.uid, page)
                self.arg.update({
                                 'notice' : self.parse_notis(unread_data),
                                 'is_unread' : True
                                 })
                unread = self.render_string('modules/more-notice.html',arg = self.arg)
                self.json_write('006', data={'notice' : unread, 'count' : len(unread_data),'nextpage':page+1})
            elif self.request.path == '/notice/more/all':
                page = int(self.get_argument('nextpage', default=1))
                allnoti_data = self.noti.get_all(self.current_user.uid, page)
                self.arg.update({
                                 'notice' : self.parse_notis(allnoti_data),
                                 'is_unread' : False
                                 })
                notice = self.render_string('modules/more-notice.html',arg = self.arg)
                self.json_write('006', data={'notice' : notice,'count' : len(allnoti_data),'nextpage':page+1})
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
                #添加评论时，对wish主人发送一条notice 并对wish 添加一条feed evt
                if(wish.uid != self.current_user.uid) : 
                    self.noti.add_notice(wish.uid, {
                                                    'type':'comment',
                                                    'fuid':self.current_user.uid,
                                                    'fid':comment.cid,
                                                    'toid':wish.wid
                                                    })
                    self.feed.add_to_feed_evt(wid=wish.wid,is_wish_evt=True, content={
                                                                                      'type' : 'comment_w',
                                                                                      'actorid' : wish.uid,
                                                                                      'actionid' : comment.cid,
                                                                                      'targetid' : wish.wid
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
                self.write('<div class="alert alert-info">还没有评论哦！说点什么？</div>')
                return;
            self.arg.update({
                             'comments' : comments
                             })
            self.render('modules/comment-list.html',arg=self.arg)
        elif(self.request.path == '/comment/box'):
            self.render('modules/comment-box.html')

@route(r'/inbox',name='inbox-index')
@route(r'/inbox/send',name='send-msg')
@route(r'/inbox/(\d+)',name='conversation')
#@route(r'/inbox/(\d+)/more/message',name='more-message')
@route(r'/inbox/more/conversation',name='more-conversation')
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
    import sys
    if(sys.maxint == 2**31-1): MOVEBITS = 32
    elif(sys.maxint == 2**63-1) : MOVEBITS = 64
    def get_conversation_id(self,l):
        l.sort()
        c = (long(l[0]) << self.MOVEBITS) + l[1]
        return c
    def is_conversation_ownby(self,uid,conv_id):
        import sys
        return uid in self.get_conversation_owner(conv_id)
    def get_conversation_owner(self,conv_id):
        conv_id = long(conv_id)
        return [conv_id >> self.MOVEBITS,conv_id & sys.maxint]
    def get_conversation_touser(self,conv_id):
        owner = self.get_conversation_owner(conv_id);
        if owner[0]==self.current_user.uid:
            uid = owner[1]
        else:
            uid = owner[0]
        return self.session.query(models.User).get(uid)
    def get_conversation(self,conv_id,page=1,page_size=20):
        if not self.is_conversation_ownby(self.current_user.uid, long(conv_id)):
            return []
        conversation =self.session.query(models.Message).filter_by(conversation=long(conv_id)).order_by(models.Message.ctime.desc())[(page-1)*20:page*20]
        return conversation
    @authenticated
    def post(self,*m,**kw):
        try:
            #发送私信
            if self.request.path == '/inbox/send' :
                data = {
                            'content' : xhtml_escape(self.get_argument('content')),
                            'from_uid' : self.current_user.uid,
                            'to_uid' : int(self.get_argument('to_uid')),
                            'ctime' : util.now(),
                            'conversation' : self.get_conversation_id([self.current_user.uid,int(self.get_argument('to_uid'))])
                        }
                validate(data,self.schema)
                if self.um.get_meta(data['to_uid'], 'message-accept')=='ifollow' and not self.ug.is_follow(data['to_uid'], data['from_uid']):
                    self.json_write('301')
                    return
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
            elif m and m[0]: # 加载更多绘画该会话的更多信息
                page = int(self.get_argument('nextpage', default=1))
                msgs = self.get_conversation(m[0], page)
                self.arg.update({
                                 'conversation' : msgs
                                 })
                self.json_write('008', data={'html':self.render_string('modules/more-msg.html',arg=self.arg),'count':len(msgs),'nextpage':page+1})
            elif self.request.path.endswith('/more/conversation'): #TODO 精简代码
                page = int(self.get_argument('nextpage', default=1))
                stmt = self.session.query(models.Message)\
                .filter( or_(models.Message.to_uid==self.current_user.uid, models.Message.from_uid==self.current_user.uid))\
                .order_by(models.Message.ctime.desc()).subquery()
                alias=aliased(models.Message,stmt)
                conversation_list = self.session.query(alias,func.count(alias)).group_by(alias.conversation)[(page-1)*20:page*20]
                self.arg.update({
                                 'conversation-list' : conversation_list
                                 })
                self.json_write('008', data={'html':self.render_string('modules/more-conversation.html',arg=self.arg),'count':len(conversation_list),'nextpage':page+1})
        except ValueError:
            self.json_write(code='000')
                
    @authenticated
    def get(self,*m,**kw):
        if m and m[0] :#进入与某人的会话
            self.arg.update({
                             'touser' : self.get_conversation_touser(m[0]),
                             'conversation' : self.get_conversation(m[0])
                             })
            self.render('conversation.html',arg=self.arg)
            return
        else: #全部会话
            stmt = self.session.query(models.Message)\
            .filter( or_(models.Message.to_uid==self.current_user.uid, models.Message.from_uid==self.current_user.uid))\
            .order_by(models.Message.ctime.desc()).subquery()
            alias=aliased(models.Message,stmt)
            conversation_list = self.session.query(alias,func.count(alias)).group_by(alias.conversation)[0:20]
            self.arg.update({
                             'conversation-list' : conversation_list
                             })
            self.render('conversation-list.html',arg=self.arg)

@route(r'/settings',name='settings-index')
@route(r'/settings/profile',name='settings-profile')
@route(r'/settings/message',name='settings-message')
@route(r'/settings/account',name='settings-account')
@route(r'/settings/email',name='settings-email')
class SettingsHandler(BaseHandler):
    profile_schema = {
            'type' : 'object',
            'properties':{
                        'displayname' : {'type':'string','blank':True },
                        'avatar' :{'type':'string','blank':True }
                        }
              }
    @authenticated
    def post(self,*m,**kw):
        try:
            if self.request.path=='/settings/profile':
                data = {
                        'displayname' : self.get_argument('displayname', default=''),
                        'avatar' : self.get_argument('avatar', default='')
                        }
                validate(data,self.profile_schema)
                self.current_user.displayname = data['displayname']
                self.current_user.avatar = data['avatar']
                self.session.add(self.current_user)
                self.session.commit()
                self.json_write('402')
                return
            elif self.request.path=='/settings/account':
                if not util.validpwd(self.get_argument('curpwd',default=''),self.current_user.pwd):
                    self.json_write('401')
                    return
                data = {
                        'pwd' : util.makepwd(self.get_argument('newpwd'))
                       }
                self.current_user.pwd = data['pwd']
                self.session.add(self.current_user)
                self.session.commit()
                self.json_write('400')
                return
            elif self.request.path=='/settings/message':
                self.um.set_meta(self.current_user.uid, 'message-accept', self.get_argument('msg', default='all'))
                self.json_write('404')
                return
            elif self.request.path=='/settings/email':
                return
        except ValueError:
            self.json_write('000')
    @authenticated
    def get(self,*m,**kw):
        
        self.arg.update({
                         'settings' : json_encode({
                                                      'msg' : self.um.get_meta(self.current_user.uid,'message-accept')
                                                 })
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
        
@route(r'/upload')
class UploadHandler(BaseHandler):    
    @authenticated    
    def post(self): 
        import os.path,random,string
        from tornado_utils.thumbnailer import get_thumbnail
        if self.request.files:
            file1 = self.request.files['avatar-file'][0]
            original_fname = file1['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            final_filename= fname+extension #TODO: 需要一个唯一的文件名
            save_path= self.application.settings.get('static_path')+'/uploads/' + final_filename
            access_url = self.static_url('uploads/'+final_filename)
            get_thumbnail(save_path, file1['body'], (100, 100), quality=100)
            callbackname = self.get_argument('callback')
            chunk = '<script>parent.%s(%s)</script>';
            self.finish(chunk%(callbackname,json_encode({'ret':'success','url':access_url})))
    #        else:
    #            self.finish(chunk%(callbackname,json_encode({'ret':'fail','url':self.static_url('img/no-avatar.jpg')})))
@route(r'/test')
class TestHandler(RequestHandler):
    def get(self):
        self.write('hello world')
        
        
