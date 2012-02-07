# -*- coding: utf-8 -*-
import time
import hashlib
import uuid
import functools
import urlparse
import urllib
from tornado.web import HTTPError 
def now():
    return long(time.time()*1000)

def timeformat(ctime,long=False):
    if long :
        return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(ctime/1000))
    return time.strftime('%Y-%m-%d',time.localtime(ctime/1000))

def makepwd(pwd):
    salt = str(uuid.uuid4()).replace('-','')
    return salt+'$'+ str(hashlib.sha1(pwd+salt).hexdigest())

def validpwd(ipwd,pwd):
    [salt,cryptograph] = pwd.split('$')
    return hashlib.sha1(ipwd+salt).hexdigest() == cryptograph

def admin_authenticated(method):
    """装饰必须要使用admin身份访问的方法 ."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user or (self.current_user.mtype != 'admin' and self.current_user.mtype != 'superadmin'):
            if self.request.method in ("GET", "HEAD"):
                url = self.get_login_url()
                if "?" not in url:
                    if urlparse.urlsplit(url).scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += "?" + urllib.urlencode(dict(next=next_url))
                self.redirect(url)
                return
            raise HTTPError(403)
        else :
            return method(self, *args, **kwargs) 
    return wrapper

def not_authenticated(method):
    """装饰必须要在未登录情况下访问的方法 ."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.current_user :
            self.json_write('4')
            self.redirect('/home')
            return
        else :
            return method(self, *args, **kwargs) 
    return wrapper
