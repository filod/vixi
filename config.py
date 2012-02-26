# -*- coding: utf-8 -*-
import os
import uimodules
app_config = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    'template_path' : os.path.join(os.path.dirname(__file__), 'tpl'), 
    "cookie_secret": 'ZjLpnC7ZRy+1mucQHlQZRsGxxBXkLku6lPNBcpl0FTI=',#base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
    "login_url": "/signin",
    "xsrf_cookies": False,
    'debug' : True,
    'autoescape' : None,
    'ui_modules': {"Entry": uimodules.EntryModule,
                   'Aside': uimodules.AsideModule
                   },
}
mysql_config = {
    'mysql_host' : 'localhost:3306', 
    'mysql_database' : 'wishing', 
    'mysql_user' : 'root', 
    'mysql_password' : '', 
}
#json ajax ret map
#req_stat  表示请求某件事儿是失败了还是完成了 fail & done
#res_stat  表示服务器端处理情况,是否是异常？是否是服务器错误（包括验证错误等）？ 
ret_code_map = {
                #登录相关
                '0': {'ret':'0','req_stat':'fail','res_stat':'success','msg':u'登录失败，密码错误','data':None},
                '1': {'ret':'1','req_stat':'done','res_stat':'success','msg':u'登录成功','data':None},
                '2': {'ret':'2','req_stat':'fail','res_stat':'success','msg':u'没有该账号','data':None},
                '3': {'ret':'3','req_stat':'fail','res_stat':'failure','msg':u'请输入账号和密码','data':None},
                '4': {'ret':'4','req_stat':'done','res_stat':'success','msg':u'已经登录','data':None},
                '5': {'ret':'5','req_stat':'fail','res_stat':'success','msg':u'该账号已经被注册','data':None},
                '6': {'ret':'6','req_stat':'done','res_stat':'success','msg':u'注册成功，已经自动登录','data':None},
                '7': {'ret':'7','req_stat':'done','res_stat':'success','msg':u'添加用户成功','data':None},
                #通用：
                '000' : {'ret':'000','req_stat':'fail','res_stat':'success','msg':u'提交参数错误','data':None},
                '001' : {'ret':'001','req_stat':'done','res_stat':'success','msg':u'常规数据返回：user timeline','data':None},
                '002' : {'ret':'002','req_stat':'done','res_stat':'success','msg':u'操作成功','data':None},
                '003' : {'ret':'003','req_stat':'done','res_stat':'failure','msg':u'操作失败','data':None},
                '004' : {'ret':'004','req_stat':'fail','res_stat':'failure','msg':u'请求错误','data':None},
                '005' : {'ret':'005','req_stat':'done','res_stat':'success','msg':u'请求成功：用户好友','data':None},
                #愿望相关：
                '100' : {'ret':'100','req_stat':'done','res_stat':'success','msg':u'保存愿望成功','data':None},
                '101' : {'ret':'101','req_stat':'done','res_stat':'failure','msg':u'保存愿望失败：未找到该愿望','data':None},
                '102' : {'ret':'102','req_stat':'done','res_stat':'failure','msg':u'保存愿望失败','data':None},
                '103' : {'ret':'103','req_stat':'done','res_stat':'success','msg':u'添加评论成功','data':None},
                #通知系统：
                '201' : {'ret':'201','req_stat':'done','res_stat':'success','msg':u'通知数据返回','data':None},
                '202' : {'ret':'202','req_stat':'done','res_stat':'success','msg':u'清除全部未读通知成功','data':None},
                '203' : {'ret':'203','req_stat':'done','res_stat':'success','msg':u'清除未读通知成功','data':None},
                '204' : {'ret':'204','req_stat':'fail','res_stat':'success','msg':u'清除未读通知失败','data':None},
                #私信：
                '300' : {'ret':'300','req_stat':'done','res_stat':'success','msg':u'发送私信成功','data':None},
                #关系：
                #其他：
                '0000': {'ret':'0000','req_stat':'fail','res_stat':'failure','msg':u'未知错误'}
                
                }

#需要记录日志的 code
log_code_map = []

