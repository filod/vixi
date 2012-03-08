# -*- coding: utf-8 -*-
import models
import tornado.web
#some UI Modules

class EntryModule(tornado.web.UIModule):
    def render(self,wish,poster=True,minimize=False,vote=False,detail=False):
        setattr(wish,'tags',list(self.handler.tg.get_tags(wish.wid)))
        setattr(wish,'editable',self.handler.is_owner(wish.uid) and not wish.has_cometrue)
        user = self.handler.session.query(models.User).get(wish.uid)
        if not wish.is_anonymous :
            setattr(wish,'username',user.displayname or user.uniquename)
        else : setattr(wish,'username','<span>匿名用户</span>')
        setattr(wish,'bless_count',self.handler.wg.get_bless_count(wish.wid))
        setattr(wish,'curse_count',self.handler.wg.get_curse_count(wish.wid))
        setattr(wish,'hasbless',self.handler.wg.is_bless(self.handler.current_user.uid, wish.wid))
        setattr(wish,'hascurse',self.handler.wg.is_curse(self.handler.current_user.uid, wish.wid))
        if detail :
            return self.render_string('modules/entry-detail.html',wish=wish,poster=poster,minimize=minimize,vote=vote)
        else:
            return self.render_string('modules/entry.html',wish=wish,poster=poster,minimize=minimize,vote=vote)

class FeedModule(tornado.web.UIModule):
    def render(self,feed): 
        return self.render_string('modules/feed-entry.html',feed=feed)

class PeopleModule(tornado.web.UIModule):
    def render(self,user): 
        return self.render_string('modules/people-entry.html',user=user)

class CommentModule(tornado.web.UIModule):
    def render(self):
        return self.render_string('modules/')
class AsideModule(tornado.web.UIModule):
    def render(self,page='',wish=None,user=None):
        notetpl =u'''
                <div class="note note-rel">
                    <div class="note-wrap alert %s alert-block">
                        <a class="close">×</a>
                        <h4 class="alert-heading"></h4>
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
                <div class="btn-group">
                    <a class="btn btn-large %s " id="do-follow" data-target="%s" data-op="%s" data-toid="%s" href="javascript:;">
                    <i class="%s"></i>%s</a>
                </div>'''
        ibtntpl =u'''
            <div class="btn-group">
                <button class="btn btn-large realize %s " rel="tooltip" title="把愿望标记为「已实现」" %s  data-op="%s" data-toid="%s" href="javascript:;"> <i class="%s"></i>%s</button>
            </div>
        '''
        def wish_page():
            options = '<li><a class="send-message" href="javascript:;"><i class="icon-envelope"></i> test</a></li>'
            if(wish.uid==self.handler.current_user.uid):
                notes = notetpl %('alert-info', u'这是您自己许的愿，您可以对愿望进行编辑、标记等操作')
                tuplestat = ('btn-warning','','realize',wish.wid,'icon-check icon-white',' 实现  ') \
                    if(not self.handler.session.query(models.Wish).get(wish.wid).has_cometrue) \
                    else ('','disabled','',wish.wid,'','已实现')
                btns = ibtntpl%tuplestat
                options = '<li><a class="" href="/wish/make/%s"><i class="icon-pencil"></i> 编辑该愿望</a></li>'%wish.wid \
                        if(not self.handler.session.query(models.Wish).get(wish.wid).has_cometrue) \
                        else '<li>无操作</li>'
                return [notes, btnbartpl % (btns,options)]
            else:
                notes = notetpl %('alert-info', u'您可以点击下方的按钮对本愿望进行关注，关注后，本愿望的动态将会在你的主页中显示。')
                tuplestat = ('btn-success','wish','follow',wish.wid,'icon-heart icon-white',' 关注  ') if(not self.handler.wg.is_follow(self.handler.current_user.uid, wish.wid)) else ('','wish','unfollow',wish.wid,'','取消关注')
                btns = btntpl%tuplestat
                options = '<li><a class="send-message" href="javascript:;"><i class="icon-envelope"></i> 给许愿人发送私信</a></li>'
                return [notes,btnbartpl %  (btns,options)]
        def people_page():
            if(user.uid==self.handler.current_user.uid):
                notes = notetpl %('alert', u'这是您自己的个人主页，其他人将可以在你的页面查看你的动态和公开的愿望。')
                return [notes, '']
            else:
                notes = notetpl % ('alert-info',u'您可以点击下方的按钮对 Ta 进行关注，关注后，Ta的动态将会在你的主页中显示。')
                tuplestat = ('btn-success','people','follow',user.uid,'icon-heart icon-white',' 关注  ') if(not self.handler.ug.is_follow(self.handler.current_user.uid, user.uid)) else ('','people','unfollow',user.uid,'','取消关注')
                btns = btntpl%tuplestat
                options = '<li><a class="send-message" href="javascript:;"><i class="icon-envelope"></i> 给他发送私信</a></li>'
                if self.handler.um.get_meta(user.uid, 'message-accept')=='ifollow' and not self.handler.ug.is_follow(user.uid, self.handler.current_user.uid):
                    options = ''
                options += '<li><a class="" id="report" href="javascript:;"><i class="icon-exclamation-sign"></i> 举报</a></li>'
                return [notes , btnbartpl % (btns,options)]
        def wish_make_page():
            notes = notetpl %('alert-info', u'在许愿页面你可以畅所欲言，点击“补充”按钮可以完善你的愿望。')
            return [notes,'']
        def home_page():
            notes = notetpl %('alert-info', u'首页将显示你关注的愿望、人的所有动态')
            return [notes,'']
        def msg_page():
            notes = notetpl %('', u'担心骚扰可以点击 <a href="/settings#tab_3"><strong>这里</strong></a> 设置为只接收「我关注的人」给我发私信。')
            return [notes,'']
        [notes,buttons] = {
            'wish' :  wish_page,
            'people' : people_page,
            'wish-make': wish_make_page,
            'home' : home_page,
            'inbox' : msg_page
            
        }[page]()
        return self.render_string('modules/aside.html',notes=notes,buttons=buttons)