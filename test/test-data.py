# -*- coding: utf-8 -*-
# script for testing,
# just need run once
import db
import models
import util
import random

session = db.ConnectDB()

def adder(funcmap):
    for item in funcmap:
        i  = item[1]
        print 'add : '+ item[0].__name__ + '\n'
        while i !=0 :
            model = item[0](i)
            session.add(model)
            i-=1
        session.commit()
        print 'added suc!\n'
    print 'op complete\n'
    return 

#add some random users:
def user(i):
    u = models.User(email='filod'+str(i)+'@q.com',
                        pwd='833f10702b774c469bf1f1b219226979$a8a55cb1855d706b998fd3e8e022308bc3da3e79',
                        displayname='filod'+str(i),
                        uniquename='filod'+str(i),
                        sex=random.randint(0,1),
                        stat='active',
                        mtype='user',
                        ctime=util.now())
    return u
#add some random wishes:
def wish(i):
    w = models.Wish(
            uid = random.randint(12,21),
            title = '愿望,每一个人都有吧,但是每个人的愿望都不同',
            content = '而我的愿望是当一位出色的教师,这个愿望在我心中隐藏很久了,\
                        我想当老师是因为我喜欢老师这个职业.老师这个职业是非常伟大的,也是非常神圣的,\
                        老师是能够照亮别人的蜡烛.是让人们踩的地板,是辛勤的园丁,是学生们心中的好棒样,\
                        老师可以把自己知道的知识传给学生们,也可以把做人的道理教给学生们,教学生们如何做人,\
                        做人的基本道理是什么.所以,我想做一名教师,',
            #poster =  
            stat = 'active',
            is_public = random.randint(0,1),
            is_anonymous = random.randint(0,1),
            bless_count = random.randint(0,1000),
            follow_count =random.randint(0,1000), 
            ctime=util.now())
    return w


adder([
       #[user,10],
       [wish,10]
    ])

#u = session.query(models.User).all()
#print u
#    
