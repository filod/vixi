# -*- coding: utf-8 -*-
from sqlalchemy import Column,Integer,String
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base

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
    uid = Column(Integer)   
    bless_count = Column(Integer)   
    follow_count = Column(Integer)