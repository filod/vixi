# -*- coding: utf-8 -*-
# script for testing some thoughts

#from validictory import validate
#a= '2012-1-a1'
#try:
#    schema = {
#            'type' : 'object',
#            'properties':{
#                        'title' :  {'type':'string'},
#                        'content' : {'type':'string','required':False },
#                        'is_public' : {'type':'integer','required':False },
#                        'is_anonymous' : {'type':'integer','required':False },
#                        'is_share' : {'type':'integer','required':False },
#                        'poster' : {'type':[{'type':'string','patten':util.REGEX.url},{'type':'null'}],'required':False },
#                        'ctime' :{'type':'integer','required':False },
#                        'stat' : {'type':[{'type':'string'},{'type':'null'}], 'maxLength':20},
#                        'uid' : {'type':'integer'}
#                        }
#              }
#    validate(a,schema)
#    b = a
#    print 'b:'+str(b)
#except ValueError, errormsg:
#    print errormsg.message
#import models
#
#
#user = models.User()
#user.ctime = 123
#print user.ctime
#setattr(user,'ctime',321)
#print user.ctime                                                             
#a = int('' or 0)
#if not a : print 'ahah'
#print a

#a=long('1231512315123151231414L')
#print a
#if True:
#    wid = 1
#else:
#    wid =2
#print wid
#from tornado.escape import *
#a= xhtml_escape(None)
#print a
#import sys
#if sys.version_info[0] == 3:
#    _str_type = str
#else:
#    _str_type = basestring
#print _str_type
#
#print isinstance(u'',basestring)
#a = ''
#if a:
#    print 't'
#else:
#    print 'f'
#
#from celery.task import task
#@task
#def add (a,b):
#    return a+b
#result = add.delay(4,4)
#print add(3,3)
#print result.wait()
#print add(6,3)
#import db
#from tornado.escape import json_decode
#r = db.ConnectRDB()
#tagSet = r.smembers('wish:%s'%61)
#l = list()
#j = 
#print type(j)
#tags_orig = {"tag1","tag2","tag3",'tag4','tag5','tag6'}
#print tags_orig
#tags_orig = set(tags_orig)
#print tags_orig
#taglist = {'tag2','tag3','tag4'}
#tags_to_add = taglist.difference(tags_orig)
#tags_to_del = tags_orig.difference(taglist)
#print tags_to_del 
#print tags_to_add 
#for tag1 in tags_to_del:
#    self.remove_tag(wid, tag1)
#for tag2 in tags_to_add:
#    self.add_tag(wid, tag2)
#a = '''sadfasdf%sasdfweqweq%swe'''%('filod','wsm')
#print a
#a= int('a')

#a = string.join(['a','b'],'')
#print a
#import db
#r = db.ConnectRDB()
#a = r.get('sadfas')
#print int(a)
#print a
#import re
#a = '{uid}aaaa'
#def rep(*l,**kw):
#    print l
#    return 'asdf'
##import string
##string.replace(a, rep , 'aha')
#r = re.compile('{.+}')
#print r.sub(rep,a)
#a = ['1','2']
#b= [int(i) for i in a]
#print b

#import sys
#print "%d"%(4294967312 & sys.maxint)
#def get_conversation_id(l):
#    MOVEBITS = 32
#    l.sort()
#    c = (long(l[0]) << MOVEBITS) + l[1]
#    return c
#def is_conversation_ownby(uid,conv_id):
#    return uid in [conv_id >> 32,conv_id & sys.maxint]
#print "%d"%get_conversation_id([1L,16])
#print "%x"%get_conversation_id([2,1]) 
#print "%x"%get_conversation_id([2,4]) 
#print "%x"%get_conversation_id([4,2])
#print 7415424000 >> 32 

