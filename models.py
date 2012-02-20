# -*- coding: utf-8 -*-
from tornado.escape import json_decode
from tornado.escape import json_encode
from sqlalchemy import Column,Integer,String,ForeignKey
from sqlalchemy.orm import relation,relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import util

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    uid = Column(Integer, primary_key = True)
    pwd = Column(String)    
    email = Column(String)
    mdata = Column(String)
    mtype = Column(String)
    ctime = Column(Integer)
    uniquename = Column(String)
    stat = Column(String)
    displayname = Column(String)
    sex = Column(Integer)
    avatar = Column(String)
    
class Wish(Base):
    __tablename__ = 'wish'
    wid = Column(Integer, primary_key = True)
    title = Column(String)    
    content = Column(String)    
    poster = Column(String)    
    ctime = Column(Integer)    
    stat = Column(String)   
    is_public = Column(Integer)    
    is_anonymous = Column(Integer)     
    uid = Column(Integer,ForeignKey('user.uid'))   
    user = relationship("User", backref=backref('wish'))
    bless_count = Column(Integer)   
    follow_count = Column(Integer)


    
class Comment(Base):
    __tablename__ = 'comment'
    cid = Column(Integer, primary_key = True)
    wid = Column(Integer)
    content = Column(String)
    ctime = Column(Integer) 
    stat = Column(String)
    uid = Column(Integer,ForeignKey('user.uid'))  
    user = relationship("User", backref=backref('comment'))



'''
--------redis 相关数据结构-------
--------------------------------
--------------------------------

--------------------------------
--------------------------------
--------------------------------
--------------------------------
--------------------------------
--------------------------------    
'''
    
class TagGraph(object):
    def __init__(self, r):
        self.r = r
        self.FOLLOWS_KEY = 'w.t' #wish上有哪些tag ###w.t:[wid] 'tagname'
        self.FOLLOWERS_KEY = 't.w' #tag上有哪些wish ###t.w:[tagname] 'wid' 
    
    def add_tag(self, wid, tagname):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, wid)   
        forward = self.r.sadd(forward_key,tagname) 
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, tagname) 
        reverse = self.r.sadd(reverse_key, wid) 
        return forward and reverse
    
    def remove_tag(self, wid, tagname):  
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, wid)
        forward = self.r.srem(forward_key, tagname)
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, tagname)
        reverse = self.r.srem(reverse_key, wid)
        return forward and reverse

    def update_tag(self, wid, tagset={}):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, wid) 
        tags_orig = self.r.smembers(forward_key)
        tags_to_add = tagset.difference(tags_orig)  #属于taglist 且不属于 tags_orig 的tag是要用来添加的tag
        tags_to_del = tags_orig.difference(tagset)  #属于tags_orig 且不属于 taglist   的tag是要用来删除的tag
        for tag1 in tags_to_del:
            self.remove_tag(wid, tag1)
        for tag2 in tags_to_add:
            self.add_tag(wid, tag2)
        return 
    def get_tags(self, wid):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, wid) 
        tags = self.r.smembers(forward_key)
        return list(tags)
    
    
    
#enlightened by gist: https://gist.github.com/564313 tks a lot!~
class UserGraph(object):
    
    def __init__(self, r):
        self.r = r
        
        # These keys are intentionally short, so as to save on memory in redis
        self.FOLLOWS_KEY = 'F' #某人关注了哪些人  ###F:[uid] uid
        self.FOLLOWERS_KEY = 'f'#某人被哪些人关注 ### f:[uid] uid
        self.BLOCKS_KEY = 'BF' #黑名单
        self.BLOCKED_KEY = 'bf'
    
    def follow(self, from_user, toid):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, from_user)
        forward = self.r.sadd(forward_key, toid)
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, toid)
        reverse = self.r.sadd(reverse_key, from_user)
        return forward and reverse
    
    def unfollow(self, from_user, toid):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, from_user)
        forward = self.r.srem(forward_key, toid)
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, toid)
        reverse = self.r.srem(reverse_key, from_user)
        return forward and reverse
    
    def block(self, from_user, toid):
        forward_key = '%s:%s' % (self.BLOCKS_KEY, from_user)
        forward = self.r.sadd(forward_key, toid)
        reverse_key = '%s:%s' % (self.BLOCKED_KEY, toid)
        reverse = self.r.sadd(reverse_key, from_user)
        return forward and reverse
    
    def unblock(self, from_user, toid):
        forward_key = '%s:%s' % (self.BLOCKS_KEY, from_user)
        forward = self.r.srem(forward_key, toid)
        reverse_key = '%s:%s' % (self.BLOCKED_KEY, toid)
        reverse = self.r.srem(reverse_key, from_user)
        return forward and reverse
    
    def get_follows(self, user):
        follows = self.r.smembers('%s:%s' % (self.FOLLOWS_KEY, user))
        blocked = self.r.smembers('%s:%s' % (self.BLOCKED_KEY, user))
        return list(follows.difference(blocked))
    
    def get_followers(self, user):
        followers = self.r.smembers('%s:%s' % (self.FOLLOWERS_KEY, user))
        blocks = self.r.smembers('%s:%s' % (self.BLOCKS_KEY, user))
        return list(followers.difference(blocks))
        
    def is_follow(self,user,uid):
        return bool(self.r.sismember('%s:%s' % (self.FOLLOWS_KEY,user),uid))
    def is_followed(self,uid,user):
        return bool(self.r.sismember('%s%s'%(self.FOLLOWERS_KEY,uid),user))
    
    def get_blocks(self, user):
        return list(self.r.smembers('%s:%s' % (self.BLOCKS_KEY, user)))
    
    def get_blocked(self, user):
        return list(self.r.smembers('%s:%s' % (self.BLOCKED_KEY, user)))

class WishGraph(object):
    def __init__(self, r):
        self.r = r
        
        # These keys are intentionally short, so as to save on memory in redis
        self.FOLLOWS_KEY = 'W'  #某人关注了哪些愿望  ###W:[uid] uid
        self.FOLLOWERS_KEY = 'w'#愿望被哪些人关注 ### w:[wid] uid
        self.BLOCKS_KEY = 'BW' #wish 黑名单
        self.BLOCKED_KEY = 'bw'
    
    def follow(self, from_user, toid):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, from_user)
        forward = self.r.sadd(forward_key, toid)
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, toid)
        reverse = self.r.sadd(reverse_key, from_user)
        return forward and reverse
    
    def unfollow(self, from_user, toid):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, from_user)
        forward = self.r.srem(forward_key, toid)
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, toid)
        reverse = self.r.srem(reverse_key, from_user)
        return forward and reverse
    
    def block(self, from_user, toid):
        forward_key = '%s:%s' % (self.BLOCKS_KEY, from_user)
        forward = self.r.sadd(forward_key, toid)
        reverse_key = '%s:%s' % (self.BLOCKED_KEY, toid)
        reverse = self.r.sadd(reverse_key, from_user)
        return forward and reverse
    
    def unblock(self, from_user, toid):
        forward_key = '%s:%s' % (self.BLOCKS_KEY, from_user)
        forward = self.r.srem(forward_key, toid)
        reverse_key = '%s:%s' % (self.BLOCKED_KEY, toid)
        reverse = self.r.srem(reverse_key, from_user)
        return forward and reverse
    
    def is_follow(self,user,wid):
        return bool(self.r.sismember('%s:%s' % (self.FOLLOWS_KEY,user),wid))
    def is_followed(self,wid,user):
        return bool(self.r.sismember('%s%s'%(self.FOLLOWERS_KEY,wid),user))
    
    def get_follows(self, user):
        follows = self.r.smembers('%s:%s' % (self.FOLLOWS_KEY, user))
        blocked = self.r.smembers('%s:%s' % (self.BLOCKED_KEY, user))
        return list(follows.difference(blocked))

    
    def get_followers(self, user):
        followers = self.r.smembers('%s:%s' % (self.FOLLOWERS_KEY, user))
        blocks = self.r.smembers('%s:%s' % (self.BLOCKS_KEY, user))
        return list(followers.difference(blocks))
    
    def get_blocks(self, user):
        return list(self.r.smembers('%s:%s' % (self.BLOCKS_KEY, user)))
    
    def get_blocked(self, user):
        return list(self.r.smembers('%s:%s' % (self.BLOCKED_KEY, user)))
    

class Notice(object):
    ''' notice 系统 
    通知 redis 数据结构： 
    list ： 存未读通知的id    unread.notice.id:[uid] uuid，标记为已读后直接lrem 并删除hash中对于uuid的条目
    hash ： 存未读通知内容        unread.notice:[uid] uuid content  
    list ：   存全部通知, 5K+条消息后trim  all.notice:[uid] content  
    content为json，结构：
     {
         'type':'xxx'  //notify-type 包含下面的类型
         // comment(愿望有新评论时) | reply (有人回复评论时) | user_follow(有人关注自己时) | wish_follow | bless | curse | atme (有愿望提及自己时) | sys (系统消息)
         'fuid': 123  //消息发起用户 （谁..）
         // uid | uid | uid | uid | uid | uid | 0
         'fid' : 123  //消息来源（如果消息是发起用户的行为，则为None） （..的什么..）
         // cid | cid | None | None  | None | None  | wid | 0
         'toid' : 321 //消息目的地            (..对你的什么做了type类型的事)
         // wid | cid | None | wid | wid | wid | None | 0
         'uuid' : xxx,               auto generate
         'addtime' : xxx,            auto generate
     }'''
    def __init__(self,r):
        self.r = r  
        self.NOTI_UUID = 'noti.uuid'  
        self.UNREAD_LIST_KEY = 'unread.notice.id'   #未读通知
        self.UNREAD_HASH_KEY = 'unread.notice'
        self.ALL_KEY = 'all.notice'         #全部通知
    def get_uuid(self):    
        return self.r.incr(self.NOTI_UUID)
    def add_notices(self,content,*touids):
        ''' 为一批人添加一条通知 '''
        for touid in touids : 
            self.add_notice(touid, content)
    def add_notice(self,touid,content):
        '''
                      为某人添加一条通知:
            @param uid: 接受通知的人
        '''
        
        uuid = self.get_uuid()
        content['uuid'] = uuid
        content['addtime'] = util.now()
        content = json_encode(content)
        pipe = self.r.pipeline(transaction=True)
        pipe.rpush('%s:%s'%(self.UNREAD_LIST_KEY,touid),uuid)
        pipe.hset('%s:%s'%(self.UNREAD_HASH_KEY,touid),uuid,content)
        pipe.rpush('%s:%s'%(self.ALL_KEY,touid),content)
        pipe.ltrim('%s:%s'%(self.ALL_KEY,touid),0,5000) #只为用户保留5K条信息 
        return pipe.execute()
    def get_all(self,uid,page=1,page_size=25):
        '''
                获取某人的通知消息    
            @param uid: 该用户的uid
            @param page: 分页，默认第一页
            @param page_size: 每页的大小  
        '''
        return self.r.lrange('%s:%s'%(self.ALL_KEY,uid),0,-1)
    def get_unread(self,uid,page=1,page_size=25):
        '''
                获取某人的未读消息    
            @param uid: 该用户的uid
            @param page: 分页，默认第一页
            @param page_size: 每页的大小  
        '''
#        uuids = self.r.lrange('%s:%s'%(self.UNREAD_LIST_KEY,uid),0,-1)
#        return self.r.hmget('%s:%s'%(self.UNREAD_HASH_KEY,uid), uuids)
        return self.r.hvals('%s:%s'%(self.UNREAD_HASH_KEY,uid))
    def get_unread_count(self,uid):
        return self.r.llen('%s:%s'%(self.UNREAD_KEY,uid))
    def mark(self,uid,uuid):
        '''
                将某未读消息标记为已读（实质是从未读list里删除它）
        '''
        pipe = self.r.pipeline(transaction=True)
        pipe.lrem('%s:%s'% (self.UNREAD_LIST_KEY,uid) ,0,uuid)
        pipe.hdel('%s:%s'% (self.UNREAD_HASH_KEY,uid) ,uuid)
        return pipe.execute()
    def mark_all(self,uid):
        '''
                将全部未读消息标记为已读 
        '''
        return self.r.delete('%s:%s'%(self.UNREAD_LIST_KEY,uid)) and self.r.delete('%s:%s'%(self.UNREAD_HASH_KEY,uid))
        
    
    