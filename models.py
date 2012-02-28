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
#     use redis to deal this
#    bless_count = Column(Integer)   
#    follow_count = Column(Integer)


    
class Comment(Base):
    __tablename__ = 'comment'
    cid = Column(Integer, primary_key = True)
    wid = Column(Integer)
    content = Column(String)
    ctime = Column(Integer) 
    reply_uid = Column(Integer) 
    reply_cid = Column(Integer) 
    stat = Column(String)
    uid = Column(Integer,ForeignKey('user.uid'))  
    user = relationship("User", backref=backref('comment'))
    

class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key = True)
    content = Column(String)
    ctime = Column(Integer)
    conversation = Column(Integer)
    from_uid = Column(Integer,ForeignKey('user.uid'))
    from_user = relationship("User",primaryjoin="Message.from_uid==User.uid",backref=backref('message'))
    to_uid = Column(Integer,ForeignKey('user.uid'))
    
    
class Conversation(object):
    def get_count(self):
        return 2
    def get_last(self):
        return
    def __init__(self):
        self.count = self.get_count()
        self.last = self.get_last()
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
        
    def get_friends(self,user):
        '''获取某人好友（互现关注的）'''
        return self.r.sinter('%s:%s' % (self.FOLLOWERS_KEY, user),'%s:%s' % (self.FOLLOWS_KEY, user))
    def is_follow(self,user,uid):
        return bool(self.r.sismember('%s:%s' % (self.FOLLOWS_KEY,user),uid))
    def is_followed(self,uid,user):
        return bool(self.r.sismember('%s%s'%(self.FOLLOWERS_KEY,uid),user))
    
    def get_blocks(self, user):
        return list(self.r.smembers('%s:%s' % (self.BLOCKS_KEY, user)))
    
    def get_blocked(self, user):
        return list(self.r.smembers('%s:%s' % (self.BLOCKED_KEY, user)))

class WishGraph(object):
    '''与wish相关的各种关系操作'''
    def __init__(self, r):
        self.r = r
        
        # These keys are intentionally short, so as to save on memory in redis
        self.FOLLOWS_KEY = 'W'  #某人关注了哪些愿望  ###W:[uid] uid
        self.FOLLOWERS_KEY = 'w'#愿望被哪些人关注 ### w:[wid] uid
        
        self.BLESS_KEY = 'u.bless'#某人祝福了哪些愿望 u.bless:[uid] wid 
        self.BLESSED_KEY = 'w.blessed' #某愿望被哪些人祝福了 w.bless:[wid] uid 
        self.CURSE_KEY = 'u.curse' #某人诅咒了哪些愿望
        self.CURSED_KEY = 'w.curseed' #愿望被哪些人诅咒了
        self.BLESS_COUNT_KEY = 'w.bless.count:%s' #某愿望的被祝福数 w.bless.count:[wid] int
        self.CURSE_COUNT_KEY = 'w.curse.count:%s' #某愿望的被诅咒数 w.bless.count:[wid] int
        
        self.MOST_BLESS_WISH = 'most.bless' #被最多祝福的愿望，仅保留 Top 1000
        self.MOST_CURSE_WISH = 'most.curse' #被最多诅咒的愿望，同上
    
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
    
    def is_follow(self,user,wid):
        return bool(self.r.sismember('%s:%s' % (self.FOLLOWS_KEY,user),wid))
    def is_followed(self,wid,user):
        return bool(self.r.sismember('%s%s'%(self.FOLLOWERS_KEY,wid),user))
    
    def get_follows(self, user,page=1,page_size=25):
        follows = self.r.smembers('%s:%s' % (self.FOLLOWS_KEY, user)) 
        return list(follows)
   
    def get_followers(self, wid):
        followers = self.r.smembers('%s:%s' % (self.FOLLOWERS_KEY, wid))
        return list(followers)
    
    def bless(self, from_user, toid):
        forward_key = '%s:%s' % (self.BLESS_KEY, from_user)
        forward = self.r.sadd(forward_key, toid)
        reverse_key = '%s:%s' % (self.BLESSED_KEY, toid)
        reverse = self.r.sadd(reverse_key, from_user)
        self.r.zadd(self.MOST_BLESS_WISH,toid,self.r.incr(self.BLESS_COUNT_KEY%toid))#belss计数加1，并更新排行
        self.r.zremrangebyrank(self.MOST_BLESS_WISH,0,1000)
        return forward and reverse
    def unbless(self, from_user, toid):
        forward_key = '%s:%s' % (self.BLESS_KEY, from_user)
        forward = self.r.srem(forward_key, toid)
        reverse_key = '%s:%s' % (self.BLESSED_KEY, toid)
        reverse = self.r.srem(reverse_key, from_user)
        self.r.zadd(self.MOST_BLESS_WISH,toid,self.r.decr(self.BLESS_COUNT_KEY%toid))#belss计数减1，并更新排行
        self.r.zremrangebyrank(self.MOST_BLESS_WISH,0,1000)
        return forward and reverse
        
    def curse(self, from_user, toid):
        forward_key = '%s:%s' % (self.CURSE_KEY, from_user)
        forward = self.r.sadd(forward_key, toid)
        reverse_key = '%s:%s' % (self.CURSED_KEY, toid)
        reverse = self.r.sadd(reverse_key, from_user)
        self.r.zadd(self.MOST_CURSE_WISH,toid,self.r.incr(self.CURSE_COUNT_KEY%toid)) 
        return forward and reverse 
    def uncurse(self, from_user, toid):
        forward_key = '%s:%s' % (self.CURSE_KEY, from_user)
        forward = self.r.srem(forward_key, toid)
        reverse_key = '%s:%s' % (self.CURSED_KEY, toid)
        reverse = self.r.srem(reverse_key, from_user)
        self.r.zadd(self.MOST_CURSE_WISH,toid,self.r.decr(self.CURSE_COUNT_KEY%toid)) 
        return forward and reverse
    def is_bless(self,user,wid):
        return bool(self.r.sismember('%s:%s' % (self.BLESS_KEY,user),wid))
    def is_curse(self,user,wid):
        return bool(self.r.sismember('%s:%s' % (self.CURSE_KEY,user),wid))
    def get_blessed(self,wid):
        '''获取某愿望被哪些人祝福了 '''
        return list(self.r.smembers('%s:%s' % (self.BLESSED_KEY, wid)))
    def get_bless_count(self,wid):
        return int(self.r.get(self.BLESS_COUNT_KEY%wid) or 0)
    def get_curse_count(self,wid):
        return int(self.r.get(self.CURSE_COUNT_KEY%wid) or 0)
    def get_most_bless(self,page=1,page_size=100):
        return self.r.zrevrange(self.MOST_BLESS_WISH,(page-1)*page_size,page*page_size)
    def get_most_curse(self,page=1,page_size=100):
        return self.r.zrevrange(self.MOST_CURSE_WISH,(page-1)*page_size,page*page_size)
    
class WishAtGraph(object):
    ''' 某愿望 提及 某些人
    redis结构：
    set：    #某愿望 提及了 哪些人  
    zset : #某人被哪些愿望提及  
     '''
    def __init__(self,r):
        self.r = r
        self.FOLLOWS_KEY = 'wish.at' ### wish.at:[wid] uid
        self.FOLLOWERS_KEY = 'at.user' ### at.user:[uid] wid
        
    def at_someone(self,wid,uid):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, wid)
        forward = self.r.sadd(forward_key, uid) 
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, uid) 
        reverse = self.r.zadd(reverse_key,   wid , util.now())  #TODO: 新版本api 参数可能会变化！！
        return forward and reverse
    def remove_someone(self, wid, uid):  
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, wid)
        forward = self.r.srem(forward_key, uid)
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, uid)
        reverse = self.r.zrem(reverse_key, wid)
        return forward and reverse

    def update_ones(self, wid, uidset={}):
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, wid)
        uids_orig = self.r.smembers(forward_key)
        uids_to_add = uidset.difference(uids_orig)   
        uids_to_del = uids_orig.difference(uidset)  
        for uid1 in uids_to_del:
            self.remove_someone(wid, uid1)
        for uid2 in uids_to_add:
            self.at_someone(wid, uid2)
        return 
    def get_ones(self, wid,page=1,page_size=25):
        '''获取某愿望提及到的人'''        
        forward_key = '%s:%s' % (self.FOLLOWS_KEY, wid) 
        uids = self.r.smembers(forward_key)
        return list(uids)
    def get_wishes(self,uid,page=1,page_size=25):
        '''获取某人被提及的愿望'''
        reverse_key = '%s:%s' % (self.FOLLOWERS_KEY, uid) 
        wids = self.r.zrevrange(reverse_key,(page-1)*page_size,page*page_size)
        return list(wids)
    

class Notice(object): 
    ''' notice 系统 
    通知 redis 数据结构： 
    list ： 存未读通知的id    unread.notice.id:[uid] uuid，标记为已读后直接lrem 并删除hash中对于uuid的条目
    hash ： 存未读通知内容        unread.notice:[uid] uuid content  
    list ：   存全部通知, 5K+条消息后trim  all.notice:[uid] content  
    content为json，结构：
     {
         'type':'xxx'  //notify-type 包含下面的类型
         // comment(愿望有新评论时) | reply (有人回复评论时) | people_follow(有人关注自己时) | wish_follow | bless | curse | atme (有愿望提及自己时) | msg (新私信）| sys (系统消息)
         'fuid': 123  //消息发起用户 （谁..）
         // uid | uid | uid | uid | uid | uid | uid | 0
         'fid' : 123  //消息来源（如果消息是发起用户的行为，则为None） （..的什么..）
         // cid | cid | None | None  | None | None  | wid | None  | 0
         'toid' : 321 //消息目的地            (..对你的什么做了type类型的事)
         // wid | cid | None | wid | wid | wid | None | None  | 0
         'content' : xxx        仅在系统消息时适用
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
        pipe.lpush('%s:%s'%(self.UNREAD_LIST_KEY,touid),uuid)
        pipe.hset('%s:%s'%(self.UNREAD_HASH_KEY,touid),uuid,content)
        pipe.lpush('%s:%s'%(self.ALL_KEY,touid),content)
        pipe.ltrim('%s:%s'%(self.ALL_KEY,touid),0,5000) #只为用户保留5K条信息 
        return pipe.execute()
    def get_all(self,uid,page=1,page_size=25):
        '''
                获取某人的通知消息    
            @param uid: 该用户的uid
            @param page: 分页，默认第一页
            @param page_size: 每页的大小  
        '''
        
        return self.r.lrange('%s:%s'%(self.ALL_KEY,uid),(page-1)*page_size,page*page_size)
    def get_unread(self,uid,page=1,page_size=99):
        '''
                获取某人的全部未读消息    
            @param uid: 该用户的uid
            @param page: 分页，默认第一页
            @param page_size: 每页的大小  
        '''
        count = self.r.llen('%s:%s'%(self.UNREAD_LIST_KEY,uid))
        uuids = self.r.lrange('%s:%s'%(self.UNREAD_LIST_KEY,uid),(page-1)*page_size,page*page_size)
        if not uuids:
            return [None,0 ]
        return [self.r.hmget('%s:%s'%(self.UNREAD_HASH_KEY,uid), uuids), count] 
    def get_unread_count(self,uid):
        return self.r.llen('%s:%s'%(self.UNREAD_KEY,uid))
    def mark(self,uid,uuid):
        '''
                将某未读消息标记为已读（实质是从未读list里删除它）
        '''
        #pipe = .pipeline(transaction=True)
        self.r.lrem('%s:%s'% (self.UNREAD_LIST_KEY,uid),uuid,0) #TODO: 更新redis-py后此api参数顺序可能有变！！！！！
        self.r.hdel('%s:%s'% (self.UNREAD_HASH_KEY,uid),uuid)
        return 
    def mark_all(self,uid):
        '''
                将全部未读消息标记为已读 
        '''
        self.r.delete('%s:%s'%(self.UNREAD_LIST_KEY,uid))
        self.r.delete('%s:%s'%(self.UNREAD_HASH_KEY,uid))
        return
        
        
class Feed(object):
    ''' 
    timeline 内容：
    1，关注的人 发表了愿望  or 关注了别人的愿望  or  祝福某愿望 
    2，关注的愿望 有修改  or 新的评论 
    3，关注的tag 有新愿望产生 （第二版 TODO）
    
    redis结构：
    zset ：  存某人的全部feed,5K+条消息后trim  feed:[uid] content  
    content {
        'type' : 'xxx'          // new_w | follow_w | bless_w ||||  update_w | comment_w 
        'actorid' : 123         // 事件发起者id， uid |||| wid
        'actionid' : 123        // 事件动作id，cid（仅在comment_w存在)
        'targetid' : 123        // 事件目标id，wid
        
    }
    zset2 : 存某人的可能造成feed的事件 ，5K+后trim feed.evt:[uid] content
    zset3 : 存某愿望可能造成feed的时间, 1K+后trim feed.evt.wish:[wid] content
     '''
    def __init__(self,r):
        self.r = r
        self.wg = WishGraph(self.r)
        self.ug = UserGraph(self.r)
        self.FEED_KEY= 'feed:%s' 
        self.FEED_EVT_KEY = 'feed.evt:%s'
        self.FEED_EVT_WISH_KEY = 'feed.evt.wish%s'
        
    def get_feeds(self, uid, until=None , page=1,page_size=50):
        '''获取某人的feeds，当指定了until的时候仅获取until之后发生的feeds '''
        if(not until):
            return self.r.zrevrange(self.FEED_KEY%uid,(page-1)*page_size,page*page_size)
        else : 
            return self.r.zrevrangebyscore(self.FEED_KEY%uid,until+1,util.now())
    def get_feeds_evt(self,uid,page=1,page_size=50):
        '''获取某人的feeds 事件，目前没有愿望feeds事件获取。'''
        return self.r.zrevrange(self.FEED_EVT_KEY%uid,(page-1)*page_size,page*page_size)
    def __add_to_feed(self,uid,content,ctime):
        ''' 给某人的 feed 添加一条内容  '''
        self.r.zadd(self.FEED_KEY%uid,content,ctime)
        self.r.zremrangebyrank(self.FEED_KEY%uid,0,-5000)  #仅保留后5k条
        return
    def __push_to_user_followers(self,uid,content): 
        '''给某user的所有关注者push feed '''
        followers = self.ug.get_followers(uid)
        for uid in followers : 
            self.__add_to_feed(uid, content,util.now())
        
    def __push_to_wish_followers(self,wid,content):
        '''给某wish的所有关注者push feed '''
        followers = self.wg.get_followers(wid)
        for uid in followers : 
            self.__add_to_feed(uid, content,util.now())
            
    def add_to_feed_evt(self,uid=None,wid=None,is_wish_evt=False,content=None):
        ''' 给某人或某愿望的 feed事件 添加一条内容  TODO: 当粉丝规模过大时可能会出现性能问题！'''
#        isUserEvt =  {
#        'new_w' : True,
#        'follow_w' :True,
#        'bless_w' :True,
#        'update_w' :False,
#        'comment_w' :False,
#         }[content['type']]
        content_json = json_encode(content)
        #添加feed事件后同时push给所有的followers。 TODO: 后序可能有重复事件(某wish和某人发出的事件相同)？
        if is_wish_evt and wid :
            self.r.zadd(self.FEED_EVT_WISH_KEY%wid,content_json,util.now())
            self.r.zremrangebyrank(self.FEED_EVT_WISH_KEY%uid,0,-1000)
            self.__push_to_wish_followers(wid, content_json)
        else:
            self.r.zadd(self.FEED_EVT_KEY%uid,content_json,util.now())
            self.r.zremrangebyrank(self.FEED_EVT_KEY%uid,0,-5000)
            self.__push_to_user_followers(uid, content_json)
        
    
    def build_feed(self,uid):
        ''' 重建feed 列表：关注/取消关注时  !!!可能耗时比较长？？？'''
        wish_follows = self.wg.get_follows(uid)
        user_follows = self.ug.get_follows(uid)
        #用所有关注的 人&愿望 的feed_evt 动态  union 之后添加到 uid的feed列表里面
        #TODO: 如果一个人的feed evt 5K条， 关注操作后的  关注为100人  那么union将会产生 50W条消息，可能导致cpu响应过长？
        keys = []
        for u in user_follows:
            keys.append(self.FEED_EVT_KEY%u)
        for w in wish_follows:
            keys.append(self.FEED_EVT_KEY%w)
        self.r.zunionstore(self.FEED_KEY%uid,keys,'max')
        self.r.zremrangebyrank(self.FEED_KEY%uid,0,-5000)
