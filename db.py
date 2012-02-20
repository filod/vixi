# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import mysql_config
import redis
def ConnectDB() :
    ConnectString = "mysql://%s:%s@%s/%s?charset=utf8" % (mysql_config['mysql_user'], 
                                                               mysql_config['mysql_password'], 
                                                              mysql_config['mysql_host'], 
                                                                 mysql_config['mysql_database'])
    engine = create_engine(ConnectString, encoding='utf8', convert_unicode=True)
    DBSession = sessionmaker(autoflush=True, expire_on_commit=False,bind=engine)
    session = DBSession()
    return session
pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
def ConnectRDB():
    r = redis.Redis(connection_pool=pool)
    return r