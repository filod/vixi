# -*- coding: utf-8 -*-
# 读写key性能测试：
import db
import util
r = db.ConnectRDB() 
print 'python 空操作测试'
for j in range(0,3) :#三次空操作：
    i = 10000 # 1w次 
    start = util.now()
    while(i):
        i-=1
    end = util.now()
    print '第'+str(j+1)+'次:'+str(end-start) +'ms'
    
print 'redis 读写测试'
for j in range(0,3) :#三次测试
    i = 10000 # 1w次读写 
    start = util.now()
    while(i):
        r.set(i,i)
        r.get(i)
        i-=1
    end = util.now()
    print '第'+str(j+1)+'次:'+str(end-start) +'ms'