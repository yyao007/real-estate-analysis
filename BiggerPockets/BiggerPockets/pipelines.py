# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, DateTime, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from BiggerPockets.items import postItem, userItem
from sqlalchemy.exc import InvalidRequestError
from datetime import datetime


connStr = 'mysql+mysqldb://yuan:931005@127.0.0.1/homeDB'
Base = declarative_base()
class Posts(Base):
    __tablename__ = 'forumposts'
    URL = Column(String(500), primary_key=True)
    replyid = Column(Integer, primary_key=True)
    pid = Column(Integer) # post id
    title = Column(String(500))
    category = Column(String(500)) # discussion category
    categoryURL = Column(String(500))
    uid = Column(String(50), ForeignKey('forumusers.uid', onupdate="CASCADE", ondelete='CASCADE')) # user id
    replyTo = Column(Integer) # This is the first post id of the discussion
    postTime = Column(DateTime(timezone=True)) # precise to hour eg. 2017-02-11 19:00:00
    body = Column(Text)
    likes = Column(Integer)
    tags = Column(String(500))

class Users(Base):
    __tablename__ = 'forumusers'

    uid = Column(String(50), primary_key=True) # user id
    firstName = Column(String(200))
    lastName = Column(String(100))
    source = Column(String(100)) # URL of the user profile
    colleagues = Column(Integer)
    followers = Column(Integer)
    following = Column(Integer)
    numPosts = Column(Integer)
    numVotes = Column(Integer)
    numAwards = Column(Integer)
    points = Column(Integer)
    account = Column(String(50)) # account type: base, plus, pro
    city = Column(String(100))
    state = Column(String(50))
    dateJoined = Column(DateTime) # creation date of the user account
    seeking = Column(Text) # currently seeking
    experience = Column(Text) # real estate experience
    occupation = Column(String(767))
    goals = Column(Text) # real estate goals
    crawl_time = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class BiggerpocketsPipeline(object):
    def open_spider(self, spider):
        self.engine = create_engine(connStr, convert_unicode=True, echo=False)
        self.DB_session = sessionmaker(bind=self.engine)
        self.session = self.DB_session()
        Base.metadata.create_all(self.engine)
        spider.homeDB = self

    def close_spider(self, spider):
        self.session.commit()
        self.session.close()
        self.engine.dispose()

    def get_last_crawl_time(self):
        t = self.session.execute("SELECT postTime FROM forumposts WHERE URL LIKE '%biggerpockets%' ORDER BY postTime DESC LIMIT 1")
        t = t.first()[0]
        return datetime(t.year, t.month, t.day)

    def process_item(self, item, spider):
        if isinstance(item, postItem):
            return self.handlePost(item, spider)
        if isinstance(item, userItem):
            return self.handleUser(item, spider)

    def handlePost(self, item, spider):
        post = Posts(URL=item.get('URL'),
                     replyid=item.get('replyid'),
                     pid=item.get('pid'),
                     title=item.get('title'),
                     category=item.get('category'),
                     categoryURL=item.get('categoryURL'),
                     uid=item.get('uid'),
                     replyTo=item.get('replyTo'),
                     postTime=item.get('postTime'),
                     body=item.get('body'),
        )
        # Avoid a post was deleted in the future
        while True:
            try:
                self.session.add(post)
                self.session.commit()
                break
            except InvalidRequestError:
                self.session.rollback()
                post.replyid += 1
            else:
                raise DropItem('Invalid item found...')
                break
	    return item

    def handleUser(self, item, spider):
        user =Users(uid=item.get('uid'),
                    firstName=item.get('firstName'),
                    lastName=item.get('lastName'),
                    source=item.get('source'),
                    colleagues=item.get('colleagues'),
                    followers=item.get('followers'),
                    following=item.get('following'),
                    numPosts=item.get('numPosts'),
                    numVotes=item.get('numVotes'),
                    numAwards=item.get('numAwards'),
                    account=item.get('account'),
                    city=item.get('city'),
                    state=item.get('state'),
                    dateJoined=item.get('dateJoined'),
                    seeking=item.get('seeking'),
                    occupation=item.get('occupation'),
                    experience=item.get('experience'),
                    goals=item.get('goals'),
        )
        self.session.add(user)
        self.session.flush()
        self.session.commit()
        return item

class DuplicatesPipeline(object):
    def __init__(self):
        self.engine = create_engine(connStr, convert_unicode=True, echo=False)
        self.DB_session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.session = self.DB_session()
        self.users_seen = set()
        self.posts = set()

    def process_item(self, item, spider):
        if isinstance(item, postItem):
            URL = item.get('URL')
            replyid = item.get('replyid')
            if (URL, replyid) in self.posts:
                raise DropItem("Duplicate post found: ")
            else:
                p = self.session.query(Posts).filter(Posts.URL == URL, Posts.replyid == replyid).first()
                if p:
                    self.posts.add((URL, replyid))
                    raise DropItem("Duplicate post found: ")
                else:
                    self.posts.add((URL, replyid))
                    return item

        if isinstance(item, userItem):
            uid = item.get('uid')
            if uid in self.users_seen:
                raise DropItem("Duplicate user found: ")
            else:
                u = self.session.query(Users).filter(Users.uid == uid)
                if u.first():
                    d = {'colleagues': item.get('colleagues'),
                         'followers': item.get('followers'),
                        'following': item.get('following'),
                        'numPosts': item.get('numPosts'),
                        'numVotes': item.get('numVotes'),
                        'numAwards': item.get('numAwards'),
                        'account': item.get('account'),
                        #'city': item.get('city'),
                        #'state': item.get('state'),
                    }
                    u.update(d)
                    self.session.commit()
                    self.users_seen.add(uid)
                    raise DropItem("Updating user: {0}".format(uid))
                else:
                    self.users_seen.add(uid)
                    return item



