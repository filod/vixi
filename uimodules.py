# -*- coding: utf-8 -*-
import models
import tornado.web
#some UI Modules

class EntryModule(tornado.web.UIModule):
    def render(self,wish,poster=True,minimize=False):
        setattr(wish,'tags',list(self.handler.tg.get_tags(wish.wid)))
        setattr(wish,'editable',self.handler.is_owner(wish.uid))
        user = self.handler.session.query(models.User).get(wish.uid)
        setattr(wish,'username',user.displayname or user.uniquename)
        setattr(wish,'bless_count',self.handler.wg.get_bless_count(wish.wid))
        setattr(wish,'curse_count',self.handler.wg.get_curse_count(wish.wid))
        setattr(wish,'hasbless',self.handler.wg.is_bless(self.handler.current_user.uid, wish.wid))
        setattr(wish,'hascurse',self.handler.wg.is_curse(self.handler.current_user.uid, wish.wid))
        return self.render_string('modules/entry.html',wish=wish,poster=poster,minimize=minimize)

class FeedModule(tornado.web.UIModule):
    def render(self,feed): 
        return self.render_string('modules/feed-entry.html',feed=feed)

class CommentModule(tornado.web.UIModule):
    def render(self):
        return self.render_string('modules/')
class AsideModule(tornado.web.UIModule):
    def render(self,page='',wish=None,user=None):
        notetpl =u'''
                <div class="note note-rel">
                    <div class="note-wrap alert alert-block">
                        <a class="close">×</a>
                        <h4 class="alert-heading">相关须知</h4>
                        <p class="note-content">
                            %s
                        </p>
                    </div>
                </div>
                '''
        btnbartpl = u'''
                    <div class="op  op-rel  btn-toolbar"> 
                            %s
                            <div class="btn-group">
                                  <a class="btn btn-large dropdown-toggle" data-toggle="dropdown" href="#">
                                  <i class="icon-cog"></i> 选项 <span class="caret"></span></a>
                                  <ul class="dropdown-menu">
                                      %s
                                  </ul>
                            </div>
                    </div>
                 '''
        btntpl = u'''
                <div class="btn-group"><a class="btn btn-large %s " id="do-follow" data-target="%s" data-op="%s" data-toid="%s" href="javascript:;">
                <i class="%s"></i>%s</a></div>'''
        def wish_page():
            if(wish.uid==self.handler.current_user.uid):
                return ['', '']
            notes = notetpl % u'您可以点击下方的按钮对本愿望进行关注，关注后，本愿望的动态将会在你的主页中显示。'
            tuplestat = ('btn-success','wish','follow',wish.wid,'icon-heart icon-white',' 关注  ') if(not self.handler.wg.is_follow(self.handler.current_user.uid, wish.wid)) else ('','wish','unfollow',wish.wid,'','取消关注')
            btns = btntpl%tuplestat
            options = '<li><a class="send-message" href="javascript:;"><i class="icon-envelope"></i> test</a></li>'
            return [notes,btnbartpl %  (btns,options)]
        def people_page():
            if(user.uid==self.handler.current_user.uid):
                return ['', '']
            notes = notetpl % u'您可以点击下方的按钮对 Ta 进行关注，关注后，Ta的动态将会在你的主页中显示。'
            tuplestat = ('btn-success','people','follow',user.uid,'icon-heart icon-white',' 关注  ') if(not self.handler.ug.is_follow(self.handler.current_user.uid, user.uid)) else ('','people','unfollow',user.uid,'','取消关注')
            btns = btntpl%tuplestat
            options = '<li><a class="send-message" href="javascript:;"><i class="icon-envelope"></i> 给他发送私信</a></li>'
            return [notes , btnbartpl % (btns,options)]
            
        [notes,buttons] = {
            'wish' :  wish_page,
            'people' : people_page
        }[page]()
        return self.render_string('modules/aside.html',notes=notes,buttons=buttons)