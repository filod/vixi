# -*- coding: utf-8 -*-
import os

app_config = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    'template_path' : os.path.join(os.path.dirname(__file__), 'tpl'), 
    "cookie_secret": 'ZjLpnC7ZRy+1mucQHlQZRsGxxBXkLku6lPNBcpl0FTI=',#base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
    "login_url": "/signin",
    "xsrf_cookies": False,
    'debug' : True,
    'autoescape' : None
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
                '000' : {'ret':'000','req_stat':'fail','res_stat':'success','msg':u'参数错误','data':None},
                '001' : {'ret':'001','req_stat':'done','res_stat':'success','msg':u'常规数据：timeline','data':None},
                
                #其他：
                '0000': {'ret':'000','req_stat':'done','res_stat':'success','msg':u'未知错误'}
                
                }

#需要记录日志的 code
log_code_map = []

